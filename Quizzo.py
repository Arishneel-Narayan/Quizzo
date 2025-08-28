# quiz_app.py
import streamlit as st
import random
import time
import json
import requests
import os
import base64
import wave
import struct
import math
import io

# --- New: Generate a beeper sound in memory ---
# This function creates a simple WAV audio file as bytes, then encodes it.
# This avoids needing a separate audio file.
def generate_beep_sound():
    sample_rate = 44100
    duration_s = 0.5
    freq_hz = 880.0
    n_samples = int(sample_rate * duration_s)
    amplitude = 32767 * 0.5  # Max amplitude for 16-bit audio

    wav_data = bytearray()
    for i in range(n_samples):
        angle = 2 * math.pi * i * freq_hz / sample_rate
        sample = int(amplitude * math.sin(angle))
        wav_data += struct.pack('<h', sample)

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(wav_data)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')

BEEP_WAV_BASE64 = generate_beep_sound()


# --- Session State Initialization ---
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
    st.session_state.timers = {'x': 20, 'y': 15, 'z': 3}
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
# New: Add a flag to ensure the sound plays only once per timer expiration.
if 'sound_played' not in st.session_state:
    st.session_state.sound_played = False


# --- Gemini API Integration (Unchanged) ---
def generate_quiz_questions_with_gemini(num_questions, topic, difficulty):
    prompt = (
        f"Generate {num_questions} quiz questions and answers on the topic of '{topic}' "
        f"with '{difficulty}' difficulty. Provide the output as a JSON array, "
        f"where each object has a 'question' and 'answer' field. "
        "Ensure the JSON is perfectly formatted and contains only the array."
    )
    
    chat_history = []
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
    
    api_key = st.secrets["GEMINI_API_KEY"] 
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    
    retries = 0
    max_retries = 5
    base_delay = 1
    
    while retries < max_retries:
        try:
            response = requests.post(api_url, headers={'Content-Type': 'application/json'}, json=payload)
            response.raise_for_status()
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

        except requests.exceptions.RequestException as e:
            retries += 1
            if retries < max_retries:
                delay = base_delay * (2 ** (retries - 1))
                time.sleep(delay)
            else:
                st.error(f"Failed to generate questions after {max_retries} attempts: {e}")
                return []
        except json.JSONDecodeError as e:
            st.error(f"Failed to decode JSON from Gemini API response: {e}")
            return []
        except ValueError as e:
            st.error(f"Error processing Gemini API response: {e}")
            return []
    return []


# --- CSS for styling (Unchanged) ---
st.markdown("""
<style>
    /* Use Inter font as per best practices */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }
    body {
        background-color: #f0f2f6;
    }
    [data-testid="stAppViewContainer"] {
        background-color: transparent;
        border-radius: 0;
        backdrop-filter: none;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
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
    .chosen-question-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 80vh;
        text-align: center;
    }
    .chosen-question-card {
        background: linear-gradient(135deg, #FFD700, #F4C430);
        color: white;
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        animation: fadeIn 0.5s ease-in-out;
        width: 100%;
        max-width: 800px;
    }
    .chosen-question-text {
        font-size: 2.5rem;
        font-weight: 600;
        word-wrap: break-word;
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
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)


# --- Quiz Master Mode (Unchanged) ---
def quiz_master_mode():
    st.image("https://placehold.co/800x200/F4C430/ffffff?text=Quizzo+Quiz+Master", use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>Welcome, Quiz Master!</h2>", unsafe_allow_html=True)
    st.markdown("Enter quiz details and generate questions below.")
    
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
            max_value=20,
            value=st.session_state.num_questions, 
            step=1
        )
        
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
                    st.session_state.num_questions = len(generated_questions)
                    st.session_state.mode = 'quiz'
                    st.session_state.available_questions = list(range(st.session_state.num_questions))
                    st.rerun()
                else:
                    st.error("Could not generate questions. Please try again or adjust your prompt.")
            else:
                st.warning("Please enter a quiz topic and number of questions.")


# --- Quiz Mode (Heavily Modified) ---
def quiz_mode():
    st.image("https://placehold.co/800x200/FFD700/ffffff?text=Quizzo+Game+Board", use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>Choose a Question</h2>", unsafe_allow_html=True)
    
    if st.session_state.current_question_index is None:
        st.markdown("Choose a question number to begin.")
        
        cols = st.columns(6)
        
        if not st.session_state.available_questions:
            st.warning("All questions have been answered! Please go back to the Quiz Master to start a new quiz.")
            
        shuffled_available = random.sample(st.session_state.available_questions, len(st.session_state.available_questions))
        
        for i in range(st.session_state.num_questions):
            with cols[i % 6]:
                if i in st.session_state.available_questions:
                    if st.button(f"{i+1}", key=f"question_btn_{i}", use_container_width=True):
                        st.session_state.current_question_index = i
                        st.session_state.show_answer = False
                        st.session_state.timer_running = False
                        st.session_state.timer_stage = 'off'
                        st.session_state.timer_value = 0
                        st.session_state.timer_start_time = None
                        st.session_state.sound_played = False # Reset sound flag
                        st.rerun()
                else:
                    st.button("✅", key=f"question_btn_{i}", disabled=True, use_container_width=True)
    else:
        q_idx = st.session_state.current_question_index
        question_data = st.session_state.questions[q_idx]

        st.markdown(f"""
        <div class="chosen-question-container">
            <div class="chosen-question-card">
                <div class="chosen-question-text">{question_data['question']}</div>
        """, unsafe_allow_html=True)

        timer_placeholder = st.empty()
        sound_placeholder = st.empty()

        # New: Reworked timer logic without a blocking `while` loop.
        if st.session_state.timer_running:
            elapsed_time = time.time() - st.session_state.timer_start_time
            remaining_time = st.session_state.timer_value - elapsed_time
            
            if remaining_time > 0:
                timer_placeholder.markdown(f"""
                <div class="timer-info-container">
                    <div class="timer-label-text">Timer for {st.session_state.timer_stage.replace('_', ' ').title()}</div>
                    <div class="timer-value-text">{int(remaining_time)}s</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.session_state.timer_running = False
                timer_placeholder.markdown(f"""
                <div class="timer-info-container">
                    <div class="timer-label-text">Time's Up!</div>
                    <div class="timer-value-text">0s</div>
                </div>""", unsafe_allow_html=True)
                
                # New: Play the beep sound when time runs out.
                if not st.session_state.sound_played:
                    sound_html = f'<audio autoplay><source src="data:audio/wav;base64,{BEEP_WAV_BASE64}" type="audio/wav"></audio>'
                    sound_placeholder.markdown(sound_html, unsafe_allow_html=True)
                    st.session_state.sound_played = True
                
                st.warning("Time's Up!")
                st.rerun() # Rerun once to update button states.
        else:
            timer_label = st.session_state.timer_stage.replace('_', ' ').title() if st.session_state.timer_stage != 'off' else "No Timer Running"
            timer_placeholder.markdown(f"""
            <div class="timer-info-container">
                <div class="timer-label-text">{timer_label}</div>
                <div class="timer-value-text">--</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True)
        
        if st.session_state.show_answer:
            st.markdown(f"""
            <div class="chosen-answer-text">Answer: {question_data['answer']}</div>
            """, unsafe_allow_html=True)

        # Buttons are now always rendered and available to be clicked.
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            if st.button("End Current Timer", use_container_width=True, disabled=not st.session_state.timer_running):
                st.session_state.timer_running = False
                st.session_state.timer_stage = 'off'
                st.info("Timer stopped!")
                st.rerun()

        with col2:
            def start_timer(stage, duration_key):
                st.session_state.timer_running = True
                st.session_state.timer_value = st.session_state.timers[duration_key]
                st.session_state.timer_start_time = time.time()
                st.session_state.timer_stage = stage
                st.session_state.sound_played = False # Reset sound flag
                st.rerun()

            if st.session_state.timer_stage == 'off' and st.button("Start First Person Timer", use_container_width=True):
                start_timer('first_person', 'x')
            elif st.session_state.timer_stage == 'first_person' and not st.session_state.timer_running and st.button("Start Team Timer", use_container_width=True):
                start_timer('team', 'y')
            elif st.session_state.timer_stage == 'team' and not st.session_state.timer_running and st.button("Start Opposing Timer", use_container_width=True):
                start_timer('opposing_team', 'z')

        with col3:
            if st.button("Show Answer", use_container_width=True):
                st.session_state.show_answer = True
                st.session_state.timer_running = False
                st.session_state.timer_stage = 'off'
                st.rerun()

        with col4:
            if st.button("Back to Board", use_container_width=True):
                st.session_state.available_questions.remove(q_idx)
                st.session_state.current_question_index = None
                st.session_state.timer_running = False
                st.session_state.timer_value = 0
                st.session_state.timer_start_time = None
                st.session_state.timer_stage = 'off'
                st.rerun()

        # New: This is the key to the non-blocking timer update.
        if st.session_state.timer_running:
            time.sleep(1)
            st.rerun()

    if st.button("Reset Quiz (Go to Quiz Master Mode)"):
        # Reset all relevant session state variables
        st.session_state.clear() # A simpler way to reset everything
        st.rerun()


# --- Main App Logic ---
def main():
    if st.session_state.mode == 'quiz_master':
        quiz_master_mode()
    elif st.session_state.mode == 'quiz':
        quiz_mode()

if __name__ == '__main__':
    main()
