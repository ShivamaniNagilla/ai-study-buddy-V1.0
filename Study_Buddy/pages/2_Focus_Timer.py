import time
import streamlit as st

st.set_page_config(page_title="Focus Timer", page_icon="⏱️")
st.title("⏱️ Focus Timer (Pomodoro)")

st.session_state.setdefault("end", None)
st.session_state.setdefault("mode", "Focus")
st.session_state.setdefault("sessions", 0)

c1, c2 = st.columns(2)
focus_min = c1.number_input("Focus (minutes)", min_value=1, max_value=120, value=25)
break_min = c2.number_input("Break (minutes)", min_value=1, max_value=60, value=5)

b1, b2, b3 = st.columns(3)
if b1.button("▶️ Start focus", type="primary"):
    st.session_state.end = time.time() + focus_min * 60
    st.session_state.mode = "Focus"
if b2.button("☕ Start break"):
    st.session_state.end = time.time() + break_min * 60
    st.session_state.mode = "Break"
if b3.button("⏹️ Stop"):
    st.session_state.end = None


@st.fragment(run_every=1)  # refreshes every second without reloading the page
def countdown():
    end = st.session_state.end
    if end is None:
        st.info("Press **Start focus** to begin.")
    else:
        left = int(end - time.time())
        if left > 0:
            m, s = divmod(left, 60)
            st.metric(f"{st.session_state.mode} time left", f"{m:02d}:{s:02d}")
        else:
            if st.session_state.mode == "Focus":
                st.session_state.sessions += 1
                st.success("🎉 Focus session complete! Take a break.")
            else:
                st.success("Break is over. Back to studying!")
            st.session_state.end = None

    st.metric("Focus sessions completed", st.session_state.sessions)


countdown()