import streamlit as st
from helpers import init_db, save_upload, extract_pdf_text, generate_revision_pack, render_pack

st.set_page_config(page_title="Notes to Quiz", page_icon="📚", layout="wide")
st.title("📚 Notes → Revision Pack")
init_db()

source = st.radio("Input source", ["Paste notes", "Upload PDF"], horizontal=True)
text = ""

if source == "Paste notes":
    text = st.text_area("Paste your notes or chapter here", height=280)
else:
    pdf = st.file_uploader("Upload a PDF", type="pdf")
    if pdf:
        data = pdf.getvalue()
        text = extract_pdf_text(data)
        saved_key = f"saved-{pdf.name}-{pdf.size}"
        if saved_key not in st.session_state:
            save_upload(pdf.name, data, text)
            st.session_state[saved_key] = True
            st.success("PDF saved to 'My Uploads' with today's date.")
        st.caption(f"Extracted {len(text):,} characters from the PDF")

if st.button("✨ Generate revision pack", type="primary"):
    if len(text.strip()) < 100:
        st.warning("Please provide more text (at least a paragraph). Scanned PDFs without text won't work.")
    else:
        with st.spinner("Gemini is building your revision pack..."):
            try:
                st.session_state["pack"] = generate_revision_pack(text)
                st.session_state["pack_id"] = st.session_state.get("pack_id", 0) + 1
            except Exception as e:
                st.error(f"Something went wrong: {e}")

if "pack" in st.session_state:
    render_pack(st.session_state["pack"], key_prefix=f"quiz{st.session_state['pack_id']}")