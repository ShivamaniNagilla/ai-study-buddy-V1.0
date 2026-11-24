from pathlib import Path
import streamlit as st
from helpers import init_db, list_uploads, delete_upload, generate_revision_pack, render_pack

st.set_page_config(page_title="My Uploads", page_icon="🗂️", layout="wide")
st.title("🗂️ My Uploaded PDFs")
init_db()

search = st.text_input("🔎 Search by file name")
rows = [r for r in list_uploads() if search.lower() in r["filename"].lower()]

if not rows:
    st.info("No uploads yet. Upload a PDF on the Notes → Quiz page.")

for r in rows:
    uid = r["id"]
    with st.expander(f"📄 {r['filename']}   •   Uploaded: {r['uploaded_at']}"):
        c1, c2, c3 = st.columns(3)
        path = Path(r["file_path"])

        if path.exists():
            c1.download_button("⬇️ Download PDF", path.read_bytes(),
                               file_name=r["filename"], key=f"dl{uid}")
        else:
            c1.warning("File missing (cloud storage was reset)")

        if c2.button("🧠 Make revision pack", key=f"gen{uid}"):
            with st.spinner("Creating revision pack..."):
                try:
                    st.session_state[f"pack{uid}"] = generate_revision_pack(r["extracted_text"])
                except Exception as e:
                    st.error(f"Error: {e}")

        if c3.button("🗑️ Delete", key=f"del{uid}"):
            delete_upload(uid, r["file_path"])
            st.rerun()

        with st.expander("Show extracted text"):
            st.text(r["extracted_text"][:3000] + ("..." if len(r["extracted_text"]) > 3000 else ""))

        if f"pack{uid}" in st.session_state:
            render_pack(st.session_state[f"pack{uid}"], key_prefix=f"up{uid}")