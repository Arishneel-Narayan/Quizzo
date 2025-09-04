import streamlit as st

st.set_page_config(page_title="Quiz Board", layout="centered")

# Initialize session state for questions
if 'questions' not in st.session_state:
    st.session_state.questions = [False] * 9  # False = available, True = used

st.title("Quiz Question Board")
st.markdown("Select a question to mark it as used. Used questions are marked with ❌.")

# Display questions in a 3x3 grid
cols = st.columns(3)
for i in range(9):
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
