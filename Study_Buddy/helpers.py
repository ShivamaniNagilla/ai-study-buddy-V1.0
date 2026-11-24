import io
import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS
from pypdf import PdfReader

MODEL = "gemini-2.5-flash"  # Change this if Google releases a newer model
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "study_buddy.db"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ---------------- Gemini ----------------
def get_client():
    key = None
    try:
        key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        key = os.getenv("GEMINI_API_KEY")
    if not key:
        st.error("GEMINI_API_KEY is missing. Add it to .streamlit/secrets.toml")
        st.stop()
    return genai.Client(api_key=key)


def ask_gemini(prompt, json_mode=False):
    config = None
    if json_mode:
        config = types.GenerateContentConfig(response_mime_type="application/json")
    response = get_client().models.generate_content(
        model=MODEL, contents=prompt, config=config
    )
    return response.text or ""


PACK_PROMPT = """You are an exam revision assistant. Using ONLY the notes below, create a revision pack.
Return ONLY valid JSON in exactly this shape:
{
  "summary": ["short bullet point", "..."],
  "quiz": [
    {
      "question": "question text",
      "options": ["option A", "option B", "option C", "option D"],
      "answer_index": 0,
      "explanation": "one short sentence"
    }
  ],
  "key_terms": [
    {"term": "word", "meaning": "simple meaning in plain English"}
  ]
}
Rules: summary must have 5 or 6 bullets. quiz must have exactly 5 questions with 4 options each.
key_terms must have exactly 3 items. answer_index is 0, 1, 2 or 3 for the correct option.

NOTES:
"""


def generate_revision_pack(notes):
    raw = ask_gemini(PACK_PROMPT + notes[:150000], json_mode=True)
    return json.loads(raw)


def transcribe_audio(audio_bytes, mime_type="audio/wav"):
    response = get_client().models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            "Transcribe this audio exactly as spoken. Return only the transcript.",
        ],
    )
    return (response.text or "").strip()


TUTOR_PROMPT = """You are a friendly, patient study tutor for students.
Explain clearly in simple words, with a short example when helpful.
Keep answers under 200 words unless the student asks for more.

"""


def tutor_reply(history, question):
    prompt = f"{TUTOR_PROMPT}Conversation so far:\n{history}\n\nStudent: {question}\nTutor:"
    return ask_gemini(prompt)


# ---------------- Text to speech / PDF ----------------
def text_to_speech(text):
    buffer = io.BytesIO()
    gTTS(text=text[:3000], lang="en").write_to_fp(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def extract_pdf_text(file_bytes):
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


# ---------------- Database (upload history) ----------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            file_path TEXT,
            extracted_text TEXT,
            uploaded_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_upload(filename, data, text):
    path = UPLOAD_DIR / f"{uuid.uuid4().hex}_{Path(filename).name}"
    path.write_bytes(data)
    conn = get_conn()
    conn.execute(
        "INSERT INTO uploads (filename, file_path, extracted_text, uploaded_at) VALUES (?, ?, ?, ?)",
        (filename, str(path), text, datetime.now().strftime("%d %b %Y, %I:%M %p")),
    )
    conn.commit()
    conn.close()


def list_uploads():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM uploads ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def delete_upload(upload_id, file_path):
    Path(file_path).unlink(missing_ok=True)
    conn = get_conn()
    conn.execute("DELETE FROM uploads WHERE id = ?", (upload_id,))
    conn.commit()
    conn.close()


# ---------------- Shared UI ----------------
def render_pack(pack, key_prefix="pack"):
    st.subheader("📝 Summary")
    for bullet in pack["summary"]:
        st.markdown(f"- {bullet}")

    st.subheader("❓ Quiz")
    with st.form(f"{key_prefix}_quiz_form"):
        answers = []
        for i, q in enumerate(pack["quiz"], 1):
            answers.append(
                st.radio(
                    f"{i}. {q['question']}",
                    q["options"],
                    index=None,
                    key=f"{key_prefix}_q{i}",
                )
            )
        submitted = st.form_submit_button("Check answers")

    if submitted:
        score = 0
        for i, (q, answer) in enumerate(zip(pack["quiz"], answers), 1):
            correct = q["options"][q["answer_index"]]
            if answer is None:
                st.warning(f"Q{i}: not answered")
            elif answer == correct:
                score += 1
                st.success(f"Q{i}: Correct ✅")
            else:
                st.error(f"Q{i}: Wrong ❌. Correct answer: **{correct}**. {q.get('explanation', '')}")
        st.metric("Score", f"{score} / {len(pack['quiz'])}")

    st.subheader("🔑 Key Terms")
    for item in pack["key_terms"]:
        st.markdown(f"**{item['term']}**: {item['meaning']}")