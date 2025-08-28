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
import pandas as pd

# --- Beeper Sound Generation (Unchanged) ---
def generate_beep_sound():
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
        'team1_name': "Team A",
        'team2_name': "Team B",
        'scores': {"Team A": 0, "Team B": 0},
        'excel_file': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()


# --- Gemini API Integration (Modified Prompt) ---
def generate_quiz_questions_with_gemini(num_questions, topic, difficulty):
    if num_questions <= 0:
        return []
    prompt = (
        f"Generate {num_questions} quiz questions and answers on the topic of '{topic}' "
        f"with '{difficulty}' difficulty. "
        "Crucially, each answer must be a maximum of three words. "
        "Provide the output as a JSON array, "
        "where each object has a 'question' and 'answer' field. "
        "Ensure the JSON is perfectly formatted and contains only the array."
    )
    
    chat_history = [{"role": "user", "parts": [{"text": prompt}]}]
    payload = { "contents": chat_history, "generationConfig": {"responseMimeType": "application/json"} }
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

# --- Mixed Difficulty Question Generation (Unchanged) ---
def generate_mixed_difficulty_questions(total_questions, topic):
    difficulty_mix = {'Easy': 0.3, 'Medium': 0.4, 'Hard': 0.3}
    num_easy = int(total_questions * difficulty_mix['Easy'])
    num_medium = int(total_questions * difficulty_mix['Medium'])
    num_hard = total_questions - num_easy - num_medium

    all_questions = []
    with st.spinner("Generating questions... This may take a moment."):
        all_questions.extend(generate_quiz_questions_with_gemini(num_easy, topic, "Easy"))
        all_questions.extend(generate_quiz_questions_with_gemini(num_medium, topic, "Medium"))
        all_questions.extend(generate_quiz_questions_with_gemini(num_hard, topic, "Hard"))

    random.shuffle(all_questions)
    return all_questions

# --- Excel File Creation (Unchanged) ---
def create_excel_download(questions):
    if not questions: return None
    df = pd.DataFrame(questions)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Quiz Questions')
    return output.getvalue()


# --- CSS (Unchanged from previous fix) ---
st.markdown("""
<style>
    /* General Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    
    /* General Button Styles */
    .stButton>button {
        transition: all 0.3s ease; border-radius: 8px; border: none;
        font-weight: 600; color: white; background-color: #F4C430;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { background-color: #FFD700; transform: translateY(-2px); }

    /* Question Grid Button Styles */
    .question-grid-cell button {
        background-color: #ffffff !important; border: 2px solid #F4C430 !important;
        color: #333333 !important; font-size: 2rem; font-weight: bold; height: 100px;
        transition: all 0.2s ease-in-out;
    }
    .question-grid-cell button:hover { transform: translateY(-5px); box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2); }
    .question-grid-cell button:disabled {
        background-color: #f0f2f6 !important; color: #adc6a0 !important;
        border-color: #d3d3d3 !important;
    }
    
    /* Chosen Question Display Styles */
    .chosen-question-container { text-align: center; }
    .chosen-question-card {
        background: linear-gradient(135deg, #FFD700, #F4C430); color: white;
        border-radius: 16px; padding: 30px; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        max-width: 800px; margin: auto;
    }
    .chosen-question-text { font-size: 2.5rem; font-weight: 600; word-wrap: break-word; }
    .chosen-answer-text {
        font-size: 1.5rem; margin-top: 1rem; background-color: rgba(255, 255, 255, 0.2);
        padding: 1rem; border-radius: 8px;
    }
    .timer-label-text { font-size: 1.2rem; opacity: 0.9; font-weight: 600; }
    .timer-value-text { font-size: 3rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# --- Quiz Master Mode (Unchanged) ---
def quiz_master_mode():
    st.image("https://placehold.co/800x200/F4C430/ffffff?text=Quizzo+Quiz+Master", use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>Welcome, Quiz Master!</h2>", unsafe_allow_html=True)
    
    with st.form(key='quiz_setup_form'):
        st.session_state.quiz_topic = st.text_input("Quiz Topic", value=st.session_state.quiz_topic)
        st.subheader("Enter Team Names")
        col_t1, col_t2 = st.columns(2)
        with col_t1: st.session_state.team1_name = st.text_input("Team 1 Name", st.session_state.team1_name)
        with col_t2: st.session_state.team2_name = st.text_input("Team 2 Name", st.session_state.team2_name)

        st.session_state.num_questions = st.number_input( 'Total Number of Questions', min_value=3, max_value=30, value=st.session_state.num_questions, step=1 )
        
        st.markdown("---")
        st.subheader("Set the Timers (in seconds)")
        col_x, col_y, col_z = st.columns(3)
        with col_x: st.session_state.timers['x'] = st.number_input('First Timer (3 Pts)', value=20, min_value=1)
        with col_y: st.session_state.timers['y'] = st.number_input('Second Timer (2 Pts)', value=15, min_value=1)
        with col_z: st.session_state.timers['z'] = st.number_input('Third Timer (1 Pt)', value=10, min_value=1)
        
        if st.form_submit_button("Generate & Start Quiz!"):
            if st.session_state.quiz_topic and st.session_state.team1_name and st.session_state.team2_name:
                gen_qs = generate_mixed_difficulty_questions(st.session_state.num_questions, st.session_state.quiz_topic)
                if gen_qs:
                    st.session_state.questions = gen_qs
                    st.session_state.num_questions = len(gen_qs)
                    st.session_state.available_questions = list(range(len(gen_qs)))
                    st.session_state.mode = 'quiz'
                    st.session_state.scores = {st.session_state.team1_name: 0, st.session_state.team2_name: 0}
                    st.session_state.excel_file = create_excel_download(gen_qs)
                    st.rerun()
                else: st.error("Could not generate questions. Please check the topic and try again.")
            else: st.warning("Please enter a quiz topic and both team names.")

# --- Quiz Mode (Corrected) ---
def quiz_mode():
    team1, team2 = st.session_state.team1_name, st.session_state.team2_name
    score1, score2 = st.session_state.scores.get(team1, 0), st.session_state.scores.get(team2, 0)

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1: st.metric(label=f"**{team1}**", value=f"{score1} Points")
    with col2: st.metric(label=f"**{team2}**", value=f"{score2} Points")
    with col3:
        if st.session_state.excel_file:
            st.download_button( label="📥 Download Q&A", data=st.session_state.excel_file, file_name=f"{st.session_state.quiz_topic.replace(' ', '_')}_quiz.xlsx", mime="application/vnd.ms-excel" )
    st.markdown("---")
    
    if st.session_state.current_question_index is None:
        st.markdown("<h2 style='text-align: center;'>Choose a Question</h2>", unsafe_allow_html=True)
        cols = st.columns(6)
        for i in range(st.session_state.num_questions):
            with cols[i % 6]:
                st.markdown('<div class="question-grid-cell">', unsafe_allow_html=True)
                if i in st.session_state.available_questions:
                    if st.button(f"{i+1}", key=f"q_btn_{i}", use_container_width=True):
                        st.session_state.current_question_index = i
                        st.session_state.show_answer, st.session_state.sound_played = False, False
                        st.session_state.timer_stage = 'off'
                        st.rerun()
                else: st.button("✅", key=f"q_btn_{i}", disabled=True, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        # --- This is the block that was missing. It is now restored. ---
        q_idx = st.session_state.current_question_index
        question_data = st.session_state.questions[q_idx]

        st.markdown(f"""
        <div class="chosen-question-container">
            <div class="chosen-question-card">
                <div class="chosen-question-text">{question_data['question']}</div>
        """, unsafe_allow_html=True)

        timer_placeholder, sound_placeholder = st.empty(), st.empty()

        if st.session_state.timer_running:
            elapsed = time.time() - st.session_state.timer_start_time
            remaining = st.session_state.timer_value - elapsed
            if remaining > 0:
                timer_placeholder.markdown(f'<div class="timer-label-text">Timer</div><div class="timer-value-text">{int(remaining)}s</div>', unsafe_allow_html=True)
            else:
                st.session_state.timer_running = False
                timer_placeholder.markdown(f'<div class="timer-label-text">Time\'s Up!</div><div class="timer-value-text">0s</div>', unsafe_allow_html=True)
                if not st.session_state.sound_played:
                    sound_html = f'<audio autoplay><source src="data:audio/wav;base64,{BEEP_WAV_BASE64}" type="audio/wav"></audio>'
                    sound_placeholder.markdown(sound_html, unsafe_allow_html=True)
                    st.session_state.sound_played = True
                st.rerun()
        else:
            timer_placeholder.markdown('<div class="timer-label-text">No Timer Running</div><div class="timer-value-text">--</div>', unsafe_allow_html=True)

        st.markdown("</div></div>", unsafe_allow_html=True) # Close card and container
        
        if st.session_state.show_answer:
            st.markdown(f"<div class='chosen-answer-text'>Answer: {question_data['answer']}</div>", unsafe_allow_html=True)

        # Scoring Logic
        points_map = {'first_person': 3, 'team': 2, 'opposing_team': 1}
        points_to_award = points_map.get(st.session_state.timer_stage, 0)

        def award_points_and_go_back(team_name, points):
            st.session_state.scores[team_name] += points
            st.session_state.available_questions.remove(q_idx)
            st.session_state.current_question_index = None
            st.rerun()

        if points_to_award > 0 and st.session_state.timer_running:
            st.markdown(f"**Award {points_to_award} Points To:**")
            score_col1, score_col2 = st.columns(2)
            if score_col1.button(f"✅ {team1}", use_container_width=True):
                award_points_and_go_back(team1, points_to_award)
            if score_col2.button(f"✅ {team2}", use_container_width=True):
                award_points_and_go_back(team2, points_to_award)

        # Control Buttons
        ctrl_cols = st.columns(4)
        if ctrl_cols[0].button("End Timer", use_container_width=True, disabled=not st.session_state.timer_running):
            st.session_state.timer_running, st.session_state.timer_stage = False, 'off'
            st.rerun()
            
        def start_timer(stage, duration_key):
            st.session_state.timer_running, st.session_state.sound_played = True, False
            st.session_state.timer_value = st.session_state.timers[duration_key]
            st.session_state.timer_start_time = time.time()
            st.session_state.timer_stage = stage
            st.rerun()

        if st.session_state.timer_stage == 'off':
            if ctrl_cols[1].button("Start Timer (3 Pts)", use_container_width=True): start_timer('first_person', 'x')
        elif st.session_state.timer_stage == 'first_person' and not st.session_state.timer_running:
            if ctrl_cols[1].button("Start Timer (2 Pts)", use_container_width=True): start_timer('team', 'y')
        elif st.session_state.timer_stage == 'team' and not st.session_state.timer_running:
            if ctrl_cols[1].button("Start Timer (1 Pt)", use_container_width=True): start_timer('opposing_team', 'z')
        
        if ctrl_cols[2].button("Show Answer", use_container_width=True):
            st.session_state.show_answer, st.session_state.timer_running = True, False
            st.rerun()

        if ctrl_cols[3].button("Back to Board", use_container_width=True):
            if q_idx in st.session_state.available_questions: st.session_state.available_questions.remove(q_idx)
            st.session_state.current_question_index = None
            st.rerun()

        if st.session_state.timer_running:
            time.sleep(1)
            st.rerun()
        # --- End of restored block ---

    if st.button("Reset Quiz (Go to Quiz Master Mode)"):
        st.session_state.clear()
        initialize_session_state()
        st.rerun()

# --- Main App Logic ---
def main():
    if st.session_state.mode == 'quiz_master': quiz_master_mode()
    elif st.session_state.mode == 'quiz': quiz_mode()

if __name__ == '__main__': main()
