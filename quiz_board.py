import streamlit as st

st.set_page_config(page_title="Quiz Board", layout="centered")


# Only show number input if not set yet
if 'num_questions' not in st.session_state:
    num_questions = st.number_input("Number of Questions", min_value=1, max_value=30, value=9, step=1, key="num_questions_input")
    if st.button("Set Number of Questions"):
        st.session_state.num_questions = num_questions
        st.session_state.questions = [False] * num_questions
        st.experimental_rerun()
    st.stop()
else:
    num_questions = st.session_state.num_questions
    if 'questions' not in st.session_state or len(st.session_state.questions) != num_questions:
        st.session_state.questions = [False] * num_questions

st.title("Quiz Question Board")


# Display questions in a 3x3 grid (or more if needed)
cols = st.columns(3)
for i in range(num_questions):
    col = cols[i % 3]
    with col:
        label = f"Q{i+1}"
        if st.session_state.questions[i]:
            st.button(f"❌ {label}", key=f"used_{i}", disabled=True, use_container_width=True)
        else:
            if st.button(label, key=f"q_{i}", use_container_width=True):
                st.session_state.questions[i] = True

st.markdown("---")
if st.button("Reset Board", use_container_width=True):
    st.session_state.questions = [False] * 9
    st.experimental_rerun()
