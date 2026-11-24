import streamlit as st
from helpers import tutor_reply, transcribe_audio, text_to_speech

st.set_page_config(page_title="AI Tutor", page_icon="🤖", layout="wide")
st.title("🤖 AI Study Tutor")

st.session_state.setdefault("chat", [])

read_aloud = st.toggle("🔊 Read text replies aloud", value=False)
tab_text, tab_voice = st.tabs(["💬 Text → Text (+ optional speech)", "🎙️ Speech → Speech"])


def history_text():
    return "\n".join(f"{m['role']}: {m['content']}" for m in st.session_state.chat[-8:])


# ---------- Text to Text ----------
with tab_text:
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.write(m["content"])
            if m.get("audio"):
                st.audio(m["audio"], format="audio/mp3")

    question = st.chat_input("Ask anything about your subject...")
    if question:
        past = history_text()
        st.session_state.chat.append({"role": "user", "content": question})
        with st.spinner("Tutor is thinking..."):
            try:
                answer = tutor_reply(past, question)
            except Exception as e:
                answer = f"Sorry, I ran into an error: {e}"
        audio = text_to_speech(answer) if (read_aloud and not answer.startswith("Sorry")) else None
        st.session_state.chat.append({"role": "assistant", "content": answer, "audio": audio})
        st.rerun()

    if st.session_state.chat and st.button("🗑️ Clear chat"):
        st.session_state.chat = []
        st.rerun()

# ---------- Speech to Speech ----------
with tab_voice:
    st.write("Record your question. The tutor listens, answers, and speaks back.")
    audio_in = st.audio_input("🎙️ Record your question")

    if audio_in is not None and st.button("Ask the tutor", type="primary"):
        with st.spinner("Listening..."):
            try:
                question_text = transcribe_audio(audio_in.getvalue())
            except Exception as e:
                st.error(f"Could not understand the audio: {e}")
                st.stop()
        st.markdown(f"**You said:** {question_text}")

        with st.spinner("Thinking..."):
            answer = tutor_reply("", question_text)
        st.markdown(f"**Tutor:** {answer}")

        with st.spinner("Preparing voice reply..."):
            st.audio(text_to_speech(answer), format="audio/mp3", autoplay=True)