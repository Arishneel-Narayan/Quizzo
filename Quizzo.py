# quiz_app.py
import streamlit as st
import random
import time

# Use st.session_state to manage the app's state across user interactions.
# This is crucial for a stateless framework like Streamlit.
# Initialize session state variables if they don't already exist.
if 'mode' not in st.session_state:
    st.session_state.mode = 'quiz_master' # Start in the quiz master mode
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'num_questions' not in st.session_state:
    st.session_state.num_questions = 18
if 'available_questions' not in st.session_state:
    st.session_state.available_questions = []
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'timers' not in st.session_state:
    st.session_state.timers = {'x': 60, 'y': 90, 'z': 30}
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
if 'timer_value' not in st.session_state:
    st.session_state.timer_value = 0
if 'timer_start_time' not in st.session_state:
    st.session_state.timer_start_time = None

# --- CSS for styling the cards and transitions ---
st.markdown("""
<style>
    /* Use Inter font as per best practices */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    /* Style the main app container for better centering and background */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%; /* Ensure it uses full width on small screens */
    }

    /* Styles for the question cards */
    .question-card {
        background-color: #f0f2f6; /* Light gray background */
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin: 10px;
        text-align: center;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        cursor: pointer;
    }

    .question-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
    }

    .question-number {
        font-size: 2.5rem;
        font-weight: 600;
        color: #4a4a4a;
    }

    /* Styles for the chosen question display */
    .chosen-question-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 80vh; /* Set a minimum height to fill the screen */
        text-align: center;
    }

    .chosen-question-card {
        background: linear-gradient(135deg, #6c80ff, #5a4ff5);
        color: white;
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        animation: fadeIn 0.5s ease-in-out;
        width: 100%; /* Use full width of container */
        max-width: 800px; /* Constrain on large screens */
    }

    .chosen-question-text {
        font-size: 2.5rem;
        font-weight: 600;
        word-wrap: break-word; /* Ensure long questions wrap correctly */
    }

    .chosen-answer-text {
        font-size: 1.5rem;
        font-weight: 400;
        margin-top: 1rem;
        background-color: rgba(255, 255, 255, 0.2);
        padding: 1rem;
        border-radius: 8px;
        animation: fadeIn 1s ease-in-out;
    }

    .timers-container {
        display: flex;
        justify-content: space-around;
        gap: 0.5rem;
        margin-top: 2rem;
        flex-wrap: wrap;
    }

    .timer-card {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 0.75rem;
        text-align: center;
        flex: 1;
        min-width: 80px;
        max-width: 120px;
    }

    .timer-label {
        font-size: 0.8rem;
        opacity: 0.8;
    }

    .timer-value {
        font-size: 1.2rem;
        font-weight: bold;
    }
    
    /* Animation for smooth appearance */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)


# --- Quiz Master Mode ---
def quiz_master_mode():
    st.title("👨‍🏫 Quiz Master Mode")
    st.markdown("Enter your questions and answers below to prepare the quiz.")
    
    # Form for quiz setup
    with st.form(key='quiz_setup_form'):
        # This number input allows the quiz master to easily "add" or "minus" questions.
        # It's a more streamlined way to handle a dynamic number of inputs than separate buttons.
        st.session_state.num_questions = st.number_input(
            'Number of Questions', 
            min_value=1, 
            max_value=100, 
            value=st.session_state.num_questions, 
            step=1
        )
        
        # Timers setup
        st.markdown("---")
        st.subheader("Set the Timers (in seconds)")
        col_x, col_y, col_z = st.columns(3)
        with col_x:
            st.session_state.timers['x'] = st.number_input('First Person Timer (X)', value=st.session_state.timers['x'], min_value=1)
        with col_y:
            st.session_state.timers['y'] = st.number_input('Team Timer (Y)', value=st.session_state.timers['y'], min_value=1)
        with col_z:
            st.session_state.timers['z'] = st.number_input('Opposing Team Timer (Z)', value=st.session_state.timers['z'], min_value=1)
        
        st.markdown("---")
        st.subheader("Questions and Answers")

        # The loop dynamically generates the input fields based on the number set above.
        for i in range(st.session_state.num_questions):
            st.markdown(f"**Question {i+1}**")
            q = st.text_area(f"Enter Question {i+1}", key=f"q_{i}", height=50)
            a = st.text_input(f"Enter Answer {i+1}", key=f"a_{i}")
            
            # Store the data in a temporary dictionary for submission
            if len(st.session_state.questions) <= i:
                st.session_state.questions.append({'question': '', 'answer': ''})
            st.session_state.questions[i]['question'] = q
            st.session_state.questions[i]['answer'] = a

        # Submit button for the form
        if st.form_submit_button("Start Quiz!"):
            # Check if all fields are filled
            if all(q['question'] and q['answer'] for q in st.session_state.questions[:st.session_state.num_questions]):
                st.session_state.mode = 'quiz'
                st.session_state.available_questions = list(range(st.session_state.num_questions))
                st.rerun()
            else:
                st.warning("Please fill in all questions and answers.")

# --- Quiz Mode ---
def quiz_mode():
    if st.session_state.current_question_index is None:
        # Display the grid of numbers if no question is selected
        st.title("🎲 The Quiz Board")
        st.markdown("Choose a question number to begin.")

        # Display question numbers in a grid
        cols = st.columns(6) # Display 6 cards per row
        
        # Use a shuffled list of available questions to make the order feel random
        shuffled_available = random.sample(st.session_state.available_questions, len(st.session_state.available_questions))
        
        for i in range(st.session_state.num_questions):
            with cols[i % 6]:
                # Use a unique key for each button to avoid re-rendering issues
                if i in st.session_state.available_questions:
                    if st.button(f"{i+1}", key=f"question_btn_{i}", use_container_width=True):
                        st.session_state.current_question_index = i
                        st.session_state.show_answer = False
                        # Reset timer state when a new question is selected
                        st.session_state.timer_running = False
                        st.session_state.timer_value = 0
                        st.session_state.timer_start_time = None
                        st.rerun()
                else:
                    # Display a disabled button or a placeholder for used questions
                    st.button("✅", key=f"question_btn_{i}", disabled=True, use_container_width=True)
    else:
        # Display the selected question in a visually pleasing container
        q_idx = st.session_state.current_question_index
        question_data = st.session_state.questions[q_idx]

        st.markdown(f"""
        <div class="chosen-question-container">
            <div class="chosen-question-card">
                <div class="chosen-question-text">{question_data['question']}</div>
        """, unsafe_allow_html=True)
        
        # Create a placeholder for the timer to be updated in place
        timer_placeholder = st.empty()

        # Display the countdown timer if it's running
        if st.session_state.timer_running:
            # Calculate the time remaining
            elapsed_time = time.time() - st.session_state.timer_start_time
            remaining_time = st.session_state.timer_value - int(elapsed_time)
            
            if remaining_time > 0:
                timer_placeholder.metric(label="Time Remaining", value=f"{remaining_time}s")
                # Rerun the script every second to update the timer display
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.timer_running = False
                timer_placeholder.metric(label="Time Remaining", value="Time's Up!")
                st.warning("Time's Up!")
        else:
            # Display the initial timer value when the timer is not running
            timer_placeholder.metric(label="Time Remaining", value=f"{st.session_state.timers['x']}s")

        # Display the answer if the button is clicked
        if st.session_state.show_answer:
            st.markdown(f"""
            <div class="chosen-answer-text">
                Answer: {question_data['answer']}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True) # close the inner and outer divs
        
        # Buttons to start the timer and show the answer
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("Start First Person Timer", use_container_width=True, disabled=st.session_state.timer_running):
                st.session_state.timer_running = True
                st.session_state.timer_value = st.session_state.timers['x']
                st.session_state.timer_start_time = time.time()
                st.rerun()
        with col2:
            if st.button("Start Team Timer", use_container_width=True, disabled=st.session_state.timer_running):
                st.session_state.timer_running = True
                st.session_state.timer_value = st.session_state.timers['y']
                st.session_state.timer_start_time = time.time()
                st.rerun()
        with col3:
            if st.button("Start Opposing Timer", use_container_width=True, disabled=st.session_state.timer_running):
                st.session_state.timer_running = True
                st.session_state.timer_value = st.session_state.timers['z']
                st.session_state.timer_start_time = time.time()
                st.rerun()
        with col4:
            if st.button("Show Answer", use_container_width=True):
                st.session_state.show_answer = True
                # Stop timer when answer is shown
                st.session_state.timer_running = False
                st.rerun()
        with col5:
            if st.button("Back to Board", use_container_width=True):
                # Remove the current question from the available list
                st.session_state.available_questions.remove(q_idx)
                st.session_state.current_question_index = None
                # Reset timer state
                st.session_state.timer_running = False
                st.session_state.timer_value = 0
                st.session_state.timer_start_time = None
                st.rerun()
    
    # Button to go back to quiz master mode
    if st.button("Reset Quiz (Go to Quiz Master Mode)"):
        st.session_state.mode = 'quiz_master'
        st.session_state.questions = []
        st.session_state.num_questions = 18
        st.session_state.timer_running = False
        st.session_state.timer_value = 0
        st.session_state.timer_start_time = None
        st.rerun()

# --- Main App Logic ---
def main():
    if st.session_state.mode == 'quiz_master':
        quiz_master_mode()
    elif st.session_state.mode == 'quiz':
        quiz_mode()

if __name__ == '__main__':
    main()
