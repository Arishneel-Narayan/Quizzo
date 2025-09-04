import streamlit as st

st.set_page_config(page_title="Quiz Board", layout="centered")


# Initialize session state for questions and labels
if 'questions' not in st.session_state:
    st.session_state.questions = [False] * 9  # False = available, True = used
if 'question_labels' not in st.session_state:
    st.session_state.question_labels = [f"Q{i+1}" for i in range(9)]

st.title("Quiz Question Board")

# Let user set their own question labels
with st.form("set_labels_form"):
    st.markdown("**Enter your question labels below:**")
    cols = st.columns(3)
    new_labels = []
    for i in range(9):
        col = cols[i % 3]
        with col:
            label = st.text_input(f"Label {i+1}", value=st.session_state.question_labels[i], key=f"label_{i}")
            new_labels.append(label)
    submitted = st.form_submit_button("Set Questions")
    if submitted:
        st.session_state.question_labels = new_labels


# Display questions in a 3x3 grid with custom labels
cols = st.columns(3)
for i in range(9):
    col = cols[i % 3]
    with col:
        label = st.session_state.question_labels[i]
        if st.session_state.questions[i]:
            st.button(f"❌ {label}", key=f"used_{i}", disabled=True, use_container_width=True)
        else:
            if st.button(label, key=f"q_{i}", use_container_width=True):
                st.session_state.questions[i] = True

st.markdown("---")
