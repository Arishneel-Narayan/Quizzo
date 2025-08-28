# quiz_app.py
import streamlit as st
import random
import time
import json
import os
import asyncio # For async operations if needed, though fetch is sync here

# Use st.session_state to manage the app's state across user interactions.
if 'mode' not in st.session_state:
    st.session_state.mode = 'quiz_master'
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
if 'timer_stage' not in st.session_state:
    st.session_state.timer_stage = 'off'
if 'quiz_topic' not in st.session_state:
    st.session_state.quiz_topic = ""
if 'quiz_difficulty' not in st.session_state:
    st.session_state.quiz_difficulty = "Medium"

# --- Gemini API Integration ---
# This function calls the Gemini API to generate quiz questions.
# It uses exponential backoff for retries to handle potential API throttling.
def generate_quiz_questions_with_gemini(num_questions, topic, difficulty):
    prompt = (
        f"Generate {num_questions} quiz questions and answers on the topic of '{topic}' "
        f"with '{difficulty}' difficulty. Provide the output as a JSON array, "
        f"where each object has a 'question' and 'answer' field. "
        "Ensure the JSON is perfectly formatted and contains only the array."
    )
    
    chat_history = []
    # CORRECTED: Changed .push() to .append() for Python lists
    chat_history.append({"role": "user", "parts": [{"text": prompt}]})
    
    payload = {
        "contents": chat_history,
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "question": {"type": "STRING"},
                        "answer": {"type": "STRING"}
                    },
                    "propertyOrdering": ["question", "answer"]
                }
            }
        }
    }
    
    # Retrieve API key from Streamlit secrets
    api_key = st.secrets["GEMINI_API_KEY"] 
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"
    
    retries = 0
    max_retries = 5
    base_delay = 1 # seconds
    
    while retries < max_retries:
        try:
            # Actual fetch call for the Canvas environment
            # This part will be executed by the Canvas runtime.
            # Using st.experimental_connection for a more Streamlit-native way to make HTTP requests
            # For direct fetch, you'd typically use a library like `requests`
            # However, in this specific environment, the `fetch` tool is available.
            # We'll simulate `fetch` with `requests` for broader compatibility if this were outside Canvas.
            # For Canvas environment, this would be a direct fetch call.
            # Since the environment provides `fetch` directly, we'll use a placeholder structure
            # that would be replaced by the actual fetch call in the Canvas runtime.
            
            # --- Start Canvas-specific fetch call ---
            # In a real Canvas environment, this would be a direct fetch call.
            # For demonstration purposes, we'll simulate a successful API response.
            
            # This part would be replaced by the actual fetch call in the Canvas runtime.
            # Example of how the fetch call would look in JavaScript for Canvas:
            
            # The actual fetch call structure for the Canvas environment:
            response = st.experimental_connection("gemini_api", type="http").post(
                api_url,
                headers={'Content-Type': 'application/json'},
                json=payload
            )
            response.raise_for_status() # Raise an exception for HTTP errors
            result = response.json()

            if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                json_string = result["candidates"][0]["content"]["parts"][0]["text"]
                generated_questions = json.loads(json_string)
                if generated_questions and isinstance(generated_questions, list):
                    return generated_questions
                else:
                    raise ValueError("Gemini API response format is unexpected or not a list.")
            else:
                raise ValueError("Gemini API response structure is unexpected.")
            # --- End Canvas-specific fetch call ---

        except Exception as e:
            retries += 1
            if retries < max_retries:
                delay = base_delay * (2 ** (retries - 1))
                time.sleep(delay)
            else:
                st.error(f"Failed to generate questions after {max_retries} attempts: {e}")
                return []
    return []


# --- CSS for styling ---
st.markdown("""
<style>
    /* Use Inter font as per best practices */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    /* Set a clean, solid background color */
    body {
        background-color: #f0f2f6; /* A very light gray for a clean look */
    }

    /* Reset the container styling to remove the old background */
    [data-testid="stAppViewContainer"] {
        background-color: transparent;
        border-radius: 0;
        backdrop-filter: none;
    }
    
    /* Style the main app container for better centering and background */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%; /* Ensure it uses full width on small screens */
    }

    /* Styles for the question cards with better aesthetics */
    .question-card {
        background-color: #ffffff;
        border: 2px solid #F4C430;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin: 10px;
        text-align: center;
        transition: all 0.2s ease-in-out;
        cursor: pointer;
    }

    .question-card:hover {
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
    }

    .question-number {
        font-size: 2.5rem;
        font-weight: 600;
        color: #F4C430;
    }
    
    .stButton>button {
        transition: all 0.3s ease;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        color: white;
        background-color: #F4C430;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton>button:hover {
        background-color: #FFD700;
        transform: translateY(-2px);
    }
    
    .stButton>button:disabled {
        background-color: #d3d3d3;
        cursor: not-allowed;
        box-shadow: none;
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
        background: linear-gradient(135deg, #FFD700, #F4C430);
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

    .timer-info-container {
        margin-top: 1rem;
    }

    .timer-label-text {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: 600;
    }

    .timer-value-text {
        font-size: 3rem;
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
    st.image("https://placehold.co/800x200/F4C430/ffffff?text=Quizzo+Quiz+Master", use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>Welcome, Quiz Master!</h2>", unsafe_allow_html=True)
    st.markdown("Enter quiz details and generate questions below.")
    
    # Form for quiz setup
    with st.form(key='quiz_setup_form'):
        st.session_state.quiz_topic = st.text_input("Quiz Topic", value=st.session_state.quiz_topic)
        st.session_state.quiz_difficulty = st.selectbox(
            "Difficulty", 
            options=["Easy", "Medium", "Hard"], 
            index=["Easy", "Medium", "Hard"].index(st.session_state.quiz_difficulty)
        )
        st.session_state.num_questions = st.number_input(
            'Number of Questions to Generate', 
            min_value=1, 
            max_value=20, # Limiting for faster generation and display
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
        
        if st.form_submit_button("Generate & Start Quiz!"):
            if st.session_state.quiz_topic and st.session_state.num_questions > 0:
                with st.spinner("Generating questions with Gemini AI... This might take a moment."):
                    generated_questions = generate_quiz_questions_with_gemini(
                        st.session_state.num_questions, 
                        st.session_state.quiz_topic, 
                        st.session_state.quiz_difficulty
                    )
                
                if generated_questions:
                    st.session_state.questions = generated_questions
                    st.session_state.num_questions = len(generated_questions) # Update actual count
                    st.session_state.mode = 'quiz'
                    st.session_state.available_questions = list(range(st.session_state.num_questions))
                    st.rerun()
                else:
                    st.error("Could not generate questions. Please try again or adjust your prompt.")
            else:
                st.warning("Please enter a quiz topic and number of questions.")

# --- Quiz Mode ---
def quiz_mode():
    st.image("https://placehold.co/800x200/FFD700/ffffff?text=Quizzo+Game+Board", use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>Choose a Question</h2>", unsafe_allow_html=True)
    
    if st.session_state.current_question_index is None:
        # Display the grid of numbers if no question is selected
        st.markdown("Choose a question number to begin.")
        
        # Display question numbers in a grid
        cols = st.columns(6) # Display 6 cards per row
        
        # Use a shuffled list of available questions to make the order feel random
        if not st.session_state.available_questions:
            st.warning("All questions have been answered! Please go back to the Quiz Master to start a new quiz.")
            
        shuffled_available = random.sample(st.session_state.available_questions, len(st.session_state.available_questions))
        
        for i in range(st.session_state.num_questions):
            with cols[i % 6]:
                # Use a unique key for each button to avoid re-rendering issues
                if i in st.session_state.available_questions:
                    if st.button(f"{i+1}", key=f"question_btn_{i}", use_container_width=True):
                        st.session_state.current_question_index = i
                        st.session_state.show_answer = False
                        st.session_state.timer_running = False
                        st.session_state.timer_stage = 'off'
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

        # Timer logic and display
        timer_placeholder = st.empty()
        
        if st.session_state.timer_running:
            # Calculate the time remaining
            elapsed_time = time.time() - st.session_state.timer_start_time
            remaining_time = st.session_state.timer_value - int(elapsed_time)
            
            # Update the metric and rerun if time is left
            if remaining_time > 0:
                timer_placeholder.markdown(f"""
                <div class="timer-info-container">
                    <div class="timer-label-text">
                        Timer for {st.session_state.timer_stage.replace('_', ' ').title()}
                    </div>
                    <div class="timer-value-text">{remaining_time}s</div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
                st.rerun()
            else:
                # Timer has run out, stop the timer and update the display
                st.session_state.timer_running = False
                timer_placeholder.markdown(f"""
                <div class="timer-info-container">
                    <div class="timer-label-text">Time's Up!</div>
                    <div class="timer-value-text">0s</div>
                </div>
                """, unsafe_allow_html=True)
                st.warning("Time's Up!")
                
        # Handle the state when the timer is not running
        if not st.session_state.timer_running:
            timer_label = st.session_state.timer_stage.replace('_', ' ').title() if st.session_state.timer_stage != 'off' else "No Timer Running"
            timer_placeholder.markdown(f"""
            <div class="timer-info-container">
                <div class="timer-label-text">{timer_label}</div>
                <div class="timer-value-text">--</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True) # close the inner and outer divs
        
        # Display the answer if the button is clicked
        if st.session_state.show_answer:
            st.markdown(f"""
            <div class="chosen-answer-text">
                Answer: {question_data['answer']}
            </div>
            """, unsafe_allow_html=True)

        # Buttons to control the quiz flow
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.session_state.timer_stage == 'off' and st.button("Start First Person Timer", use_container_width=True):
                st.session_state.timer_running = True
                st.session_state.timer_value = st.session_state.timers['x']
                st.session_state.timer_start_time = time.time()
                st.session_state.timer_stage = 'first_person'
                st.rerun()
            elif st.session_state.timer_stage == 'first_person' and not st.session_state.timer_running and st.button("Start Team Timer", use_container_width=True):
                st.session_state.timer_running = True
                st.session_state.timer_value = st.session_state.timers['y']
                st.session_state.timer_start_time = time.time()
                st.session_state.timer_stage = 'team'
                st.rerun()
            elif st.session_state.timer_stage == 'team' and not st.session_state.timer_running and st.button("Start Opposing Timer", use_container_width=True):
                st.session_state.timer_running = True
                st.session_state.timer_value = st.session_state.timers['z']
                st.session_state.timer_start_time = time.time()
                st.session_state.timer_stage = 'opposing_team'
                st.rerun()
        with col2:
            if st.button("Show Answer", use_container_width=True):
                st.session_state.show_answer = True
                st.session_state.timer_running = False
                st.rerun()
        with col3:
            if st.button("Back to Board", use_container_width=True):
                st.session_state.available_questions.remove(q_idx)
                st.session_state.current_question_index = None
                st.session_state.timer_running = False
                st.session_state.timer_value = 0
                st.session_state.timer_start_time = None
                st.session_state.timer_stage = 'off'
                st.rerun()

    # Button to go back to quiz master mode
    if st.button("Reset Quiz (Go to Quiz Master Mode)"):
        st.session_state.mode = 'quiz_master'
        st.session_state.questions = []
        st.session_state.num_questions = 18
        st.session_state.timer_running = False
        st.session_state.timer_value = 0
        st.session_state.timer_start_time = None
        st.session_state.timer_stage = 'off'
        st.session_state.quiz_topic = "" # Reset topic
        st.session_state.quiz_difficulty = "Medium" # Reset difficulty
        st.rerun()

# --- Main App Logic ---
def main():
    if st.session_state.mode == 'quiz_master':
        quiz_master_mode()
    elif st.session_state.mode == 'quiz':
        quiz_mode()

if __name__ == '__main__':
    main()
