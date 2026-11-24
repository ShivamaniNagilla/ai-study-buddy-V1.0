import streamlit as st
from helpers import init_db

st.set_page_config(page_title="AI Study Buddy", page_icon="🎓", layout="wide")
init_db()

st.title("🎓 AI Study Buddy")
st.write("Turn long notes into quick revision packs, stay focused, find free books, and learn with an AI tutor.")

st.markdown("""
### What you can do
- 📚 **Notes → Revision Pack**: summary, 5 MCQs, and key terms
- ⏱️ **Focus Timer**: Pomodoro sessions to study with focus
- 📖 **Free Books**: search free books on any topic and download them
- 🤖 **AI Tutor**: chat by text or talk by voice, with spoken replies
- 🗂️ **My Uploads**: all your PDFs with upload dates

👈 Pick a page from the sidebar to begin.
""")