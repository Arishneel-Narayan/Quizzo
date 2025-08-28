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
import pandas as pd # New: Import pandas for Excel handling

# --- Beeper Sound Generation (Unchanged) ---
def generate_beep_sound():
    # ... (function content is the same as before)
    sample_rate = 44100
    duration_s = 0.5
    freq_hz = 880.0
    n_samples = int(sample_rate * duration_s)
    amplitude = 32767 * 0.5

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
def initialize_session_state():
    defaults = {
        'mode': 'quiz_master',
        'questions': [],
        'num_questions': 18,
        'available_questions': [],
        'current_question_index': None,
        'show_answer': False,
        'timers': {'x': 20, 'y': 15, 'z': 3},
        'timer_running': False,
        'timer_value': 0,
        'timer_start_time': None,
        'timer_stage': 'off',
        'quiz_topic': "",
        'sound_played': False,
        'team1_name': "Team A", # New: Team names
        'team2_name': "Team B",
        'scores': {"Team A": 0, "Team B": 0}, # New: Scoring
        'excel_file': None # New: For storing the excel file bytes
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()


# --- Gemini API Integration (Unchanged) ---
def generate_quiz_questions_with_gemini(num_questions, topic, difficulty):
    # ... (function content is the same as before, no changes needed here)
    if num_questions <= 0:
        return []
    prompt = (
        f"Generate {num_questions} quiz questions and answers on the topic of '{topic}' "
        f"with '{difficulty}' difficulty. Provide the output as a JSON array, "
        f"where each object has a 'question' and 'answer' field. "
        "Ensure the JSON is perfectly formatted and contains only the array."
    )
    
    chat_history = [{"role": "user", "parts": [{"text": prompt}]}]
    payload = {
        "contents": chat_history,
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    api_key = st.secrets["GEMINI_API_KEY"]
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    
    try:
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, json=payload)
        response.raise_for_status()
        result = response.json()
        json_string = result["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(json_string)
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError, IndexError) as e:
        st.error(f"Error generating '{difficulty}' questions: {e}")
        return []


# --- New: Function to generate questions with mixed difficulty ---
def generate_mixed_difficulty_questions(total_questions, topic):
    difficulty_mix = {
        'Easy': 0.3,
        'Medium': 0.4,
        'Hard': 0.3
    }
    
    num_easy = int(total_questions * difficulty_mix['Easy'])
    num_medium = int(total_questions * difficulty_mix['Medium'])
    num_hard = total_questions - num_easy - num_medium # Ensure total is correct

    all_questions = []
    with st.spinner("Generating questions... This may take a moment."):
        easy_q = generate_quiz_questions_with_gemini(num_easy, topic, "Easy")
        all_questions.extend(easy_q)
        
        medium_q = generate_quiz_questions_with_gemini(num_medium, topic, "Medium")
        all_questions.extend(medium_q)

        hard_q = generate_quiz_questions_with_gemini(num_hard, topic, "Hard")
        all_questions.extend(hard_q)

    random.shuffle(all_questions) # Shuffle to mix difficulties
    return all_questions


# --- New: Function to create an Excel file in memory ---
def create_excel_download(questions):
    if not questions:
        return None
    df = pd.DataFrame(questions)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Quiz Questions')
    return output.getvalue()


# --- CSS (Unchanged) ---
st.markdown("""
<style>
    /* ... (CSS content is the same as before) ... */
</style>
""", unsafe_allow_html=True)


# --- Quiz Master Mode (Modified) ---
def quiz_master_mode():
    st.image("https://placehold.co/800x200/F4C430/ffffff?text=Quizzo+Quiz+Master", use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>Welcome, Quiz Master!</h2>", unsafe_allow_html=True)
    
    with st.form(key='quiz_setup_form'):
        st.session_state.quiz_topic = st.text_input("Quiz Topic", value=st.session_state.quiz_topic)
        
        # New: Team Name Inputs
        st.subheader("Enter Team Names")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.session_state.team1_name = st.text_input("Team 1 Name", value=st.session_state.team1_name)
        with col_t2:
            st.session_state.team2_name = st.text_input("Team 2 Name", value=st.session_state.team2_name)

        st.session_state.num_questions = st.number_input(
            'Total Number of Questions', min_value=3, max_value=30,
            value=st.session_state.num_questions, step=1
        )
        
        st.markdown("---")
        st.subheader("Set the Timers (in seconds)")
        col_x, col_y, col_z = st.columns(3)
        with col_x:
            st.session_state.timers['x'] = st.number_input('First Timer (3 Pts)', value=20, min_value=1)
        with col_y:
            st.session_state.timers['y'] = st.number_input('Second Timer (2 Pts)', value=15, min_value=1)
        with col_z:
            st.session_state.timers['z'] = st.number_input('Third Timer (1 Pt)', value=10, min_value=1)
        
        if st.form_submit_button("Generate & Start Quiz!"):
            if st.session_state.quiz_topic and st.session_state.team1_name and st.session_state.team2_name:
                generated_questions = generate_mixed_difficulty_questions(
                    st.session_state.num_questions, st.session_state.quiz_topic
                )
                
                if generated_questions:
                    st.session_state.questions = generated_questions
                    st.session_state.num_questions = len(generated_questions)
                    st.session_state.available_questions = list(range(len(generated_questions)))
                    st.session_state.mode = 'quiz'
                    # New: Initialize scores and create Excel file
                    st.session_state.scores = {st.session_state.team1_name: 0, st.session_state.team2_name: 0}
                    st.session_state.excel_file = create_excel_download(generated_questions)
                    st.rerun()
                else:
                    st.error("Could not generate questions. Please check the topic and try again.")
            else:
                st.warning("Please enter a quiz topic and both team names.")


# --- Quiz Mode (Modified) ---
def quiz_mode():
    # --- New: Scoreboard and Download Button ---
    team1, team2 = st.session_state.team1_name, st.session_state.team2_name
    score1, score2 = st.session_state.scores[team1], st.session_state.scores[team2]

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.metric(label=f"**{team1}**", value=f"{score1} Points")
    with col2:
        st.metric(label=f"**{team2}**", value=f"{score2} Points")
    with col3:
        if st.session_state.excel_file:
            st.download_button(
                label="📥 Download Q&A",
                data=st.session_state.excel_file,
                file_name=f"{st.session_state.quiz_topic.replace(' ', '_')}_quiz.xlsx",
                mime="application/vnd.ms-excel"
            )

    st.markdown("---")
    
    if st.session_state.current_question_index is None:
        st.markdown("<h2 style='text-align: center;'>Choose a Question</h2>", unsafe_allow_html=True)
        cols = st.columns(6)
        # ... (rest of the question grid logic is unchanged)
    else:
        # --- Question Display and Timer Logic (with new scoring buttons) ---
        q_idx = st.session_state.current_question_index
        question_data = st.session_state.questions[q_idx]

        # ... (display for question text is the same)

        # New: Scoring logic and buttons
        points_to_award = 0
        if st.session_state.timer_stage == 'first_person':
            points_to_award = 3
        elif st.session_state.timer_stage == 'team':
            points_to_award = 2
        elif st.session_state.timer_stage == 'opposing_team':
            points_to_award = 1

        if points_to_award > 0 and st.session_state.timer_running:
            st.markdown(f"**Award {points_to_award} Points To:**")
            score_col1, score_col2 = st.columns(2)
            with score_col1:
                if st.button(f"✅ {st.session_state.team1_name}", use_container_width=True):
                    st.session_state.scores[st.session_state.team1_name] += points_to_award
                    # Go back to board after scoring
                    st.session_state.available_questions.remove(q_idx)
                    st.session_state.current_question_index = None
                    st.rerun()
            with score_col2:
                if st.button(f"✅ {st.session_state.team2_name}", use_container_width=True):
                    st.session_state.scores[st.session_state.team2_name] += points_to_award
                    st.session_state.available_questions.remove(q_idx)
                    st.session_state.current_question_index = None
                    st.rerun()

        # ... (timer logic and other buttons are mostly the same)
        # ... just ensure labels reflect points
        
        with col2: # The "Start Timer" column
            # ... update button labels to reflect points
            if st.session_state.timer_stage == 'off' and st.button("Start Timer (3 Pts)", use_container_width=True):
                 start_timer('first_person', 'x')
            elif st.session_state.timer_stage == 'first_person' and not st.session_state.timer_running and st.button("Start Timer (2 Pts)", use_container_width=True):
                 start_timer('team', 'y')
            elif st.session_state.timer_stage == 'team' and not st.session_state.timer_running and st.button("Start Timer (1 Pt)", use_container_width=True):
                 start_timer('opposing_team', 'z')
        
    if st.button("Reset Quiz (Go to Quiz Master Mode)"):
        st.session_state.clear()
        initialize_session_state() # Re-initialize with defaults
        st.rerun()


# --- Main App Logic ---
def main():
    if st.session_state.mode == 'quiz_master':
        quiz_master_mode()
    elif st.session_state.mode == 'quiz':
        quiz_mode()

if __name__ == '__main__':
    main()
