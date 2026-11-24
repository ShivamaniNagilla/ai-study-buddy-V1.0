import requests
import streamlit as st

st.set_page_config(page_title="Free Books", page_icon="📖", layout="wide")
st.title("📖 Free Books for Any Topic")
st.caption("Public-domain books from Project Gutenberg, plus free scans from Open Library / Internet Archive.")

topic = st.text_input("Search a topic, subject or author", placeholder="e.g. physics, Shakespeare, economics")


@st.cache_data(ttl=3600, show_spinner=False)
def search_gutenberg(query):
    r = requests.get("https://gutendex.com/books/", params={"search": query}, timeout=15)
    r.raise_for_status()
    return r.json().get("results", [])[:10]


@st.cache_data(ttl=3600, show_spinner=False)
def search_openlibrary(query):
    r = requests.get(
        "https://openlibrary.org/search.json",
        params={"q": query, "has_fulltext": "true", "limit": 10,
                "fields": "title,author_name,first_publish_year,ia"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("docs", [])


def format_label(mime):
    if "epub" in mime:
        return "📘 EPUB"
    if "pdf" in mime:
        return "📄 PDF"
    if mime.startswith("text/plain"):
        return "📝 TXT"
    if mime.startswith("text/html"):
        return "🌐 Read online"
    return None


if topic:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Project Gutenberg (free classics & textbooks)")
        try:
            books = search_gutenberg(topic)
            if not books:
                st.info("No books found. Try another keyword.")
            for book in books:
                with st.container(border=True):
                    authors = ", ".join(a["name"] for a in book.get("authors", [])) or "Unknown author"
                    st.markdown(f"**{book['title']}**")
                    st.caption(authors)
                    buttons = []
                    for mime, url in book.get("formats", {}).items():
                        label = format_label(mime)
                        if label:
                            buttons.append((label, url))
                    if buttons:
                        cols = st.columns(len(buttons))
                        for c, (label, url) in zip(cols, buttons):
                            c.link_button(label, url)
        except Exception as e:
            st.error(f"Could not reach Gutendex: {e}")

    with col2:
        st.subheader("Open Library / Internet Archive")
        try:
            docs = search_openlibrary(topic)
            if not docs:
                st.info("No readable scans found. Try another keyword.")
            for doc in docs:
                with st.container(border=True):
                    authors = ", ".join(doc.get("author_name", [])) or "Unknown author"
                    year = doc.get("first_publish_year", "")
                    st.markdown(f"**{doc.get('title', 'Untitled')}** {f'({year})' if year else ''}")
                    st.caption(authors)
                    if doc.get("ia"):
                        st.link_button("📖 Read / Download", f"https://archive.org/details/{doc['ia'][0]}")
        except Exception as e:
            st.error(f"Could not reach Open Library: {e}")
else:
    st.info("Type a topic above to search free books.")