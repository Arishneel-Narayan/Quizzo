# quiz_app.py
import streamlit as st
import time
import base64
import wave
import struct
import math
import io
import streamlit.components.v1 as components # New: Import components library

# --- Beeper Sound Generation ---
def generate_beep_sound():
    """Generates a WAV beep sound in memory and returns it as a Base64 string."""
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

# --- New: Function to reliably play the beep sound ---
def play_beep_sound():
    """Embeds an HTML audio player that is triggered to play by JavaScript."""
    components.html(f"""
        <audio autoplay>
        <source src="data:audio/wav;base64,{BEEP_WAV_BASE64}" type="audio/wav">
        </audio>
    """, height=0)


# --- Session State Initialization ---
def initialize_session_state():
    """Sets up the default values for the session state."""
    defaults = {
        'mode': 'setup',
        'timers': {'x': 20, 'y': 15, 'z': 10},
        'timer_running': False,
        'timer_value': 0,
        'timer_start_time': None,
        'timer_stage': 'off',
        'sound_played': False,
        'team_names': ["Team A", "Team B", "Team C"],
        'scores': {"Team A": 0, "Team B": 0, "Team C": 0},
        'points_awarded': False,
        'current_team_idx': 0
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()


# --- CSS Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    
    .stButton>button {
        transition: all 0.3s ease; border-radius: 8px; border: none;
        font-weight: 600; color: white; background-color: #F4C430;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: 50px;
    }
    .stButton>button:hover { background-color: #FFD700; transform: translateY(-2px); }
    .stButton>button:disabled {
        background-color: #d3d3d3 !important;
        color: #888888 !important;
        cursor: not-allowed;
    }

    .timer-container {
        background: linear-gradient(135deg, #FFD700, #F4C430);
        color: white;
        border-radius: 16px;
        padding: 30px;
        text-align: center;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
    }
    .timer-label-text { font-size: 1.5rem; opacity: 0.9; font-weight: 600; }
    .timer-value-text { font-size: 5rem; font-weight: 700; line-height: 1.1; }
</style>
""", unsafe_allow_html=True)


# --- UI Mode: Setup Screen ---
def setup_mode():
    """Renders the initial setup screen for team names and timers."""
    st.image("https://placehold.co/800x200/F4C430/ffffff?text=ScoreMaster", use_container_width=True)
    st.markdown("<h2 style='text-align: center;'>Game Setup</h2>", unsafe_allow_html=True)
    
    with st.form(key='setup_form'):
        st.subheader("Enter Team Names")
        col_t1, col_t2, col_t3 = st.columns(3)
        team_names = st.session_state.team_names
        with col_t1:
            team_names[0] = st.text_input("Team 1 Name", team_names[0])
        with col_t2:
            team_names[1] = st.text_input("Team 2 Name", team_names[1])
        with col_t3:
            team_names[2] = st.text_input("Team 3 Name", team_names[2])
        st.session_state.team_names = team_names

        st.markdown("---")
        st.subheader("Set the Timers (in seconds)")
        col_x, col_y, col_z = st.columns(3)
        with col_x: st.session_state.timers['x'] = st.number_input('Timer for 3 Pts', value=20, min_value=1)
        with col_y: st.session_state.timers['y'] = st.number_input('Timer for 2 Pts', value=15, min_value=1)
        with col_z: st.session_state.timers['z'] = st.number_input('Timer for 1 Pt', value=10, min_value=1)

        if st.form_submit_button("Start Game!"):
            if all(name.strip() for name in st.session_state.team_names):
                st.session_state.scores = {name: 0 for name in st.session_state.team_names}
                st.session_state.current_team_idx = 0
                st.session_state.mode = 'scoring'
                st.rerun()
            else:
                st.warning("Please enter all three team names.")

# --- UI Mode: Scoring & Timing Dashboard ---
def scoring_mode():
    """Renders the main dashboard for scoring and timing."""
    team_names = st.session_state.team_names
    scores = st.session_state.scores
    current_team_idx = st.session_state.current_team_idx
    current_team = team_names[current_team_idx]

    # --- Display Scoreboard ---
    cols = st.columns(3)
    for i, team in enumerate(team_names):
        with cols[i]:
            st.metric(label=f"**{team}**", value=f"{scores.get(team, 0)} Points")
    st.markdown("---")

    # --- Display Timer ---
    st.markdown('<div class="timer-container">', unsafe_allow_html=True)
    timer_placeholder = st.empty()
    if st.session_state.timer_running:
        elapsed = time.time() - st.session_state.timer_start_time
        remaining = st.session_state.timer_value - elapsed
        if remaining > 0:
            timer_placeholder.markdown(f'<div class="timer-label-text">Time Remaining</div><div class="timer-value-text">{int(remaining)}s</div>', unsafe_allow_html=True)
        else:
            st.session_state.timer_running = False
            timer_placeholder.markdown(f'<div class="timer-label-text">Time\'s Up!</div><div class="timer-value-text">0s</div>', unsafe_allow_html=True)
            if not st.session_state.sound_played:
                # New: Call the reliable sound playing function
                play_beep_sound()
                st.session_state.sound_played = True
            st.rerun()
    else:
        timer_placeholder.markdown('<div class="timer-label-text">Timer Off</div><div class="timer-value-text">--</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Scoring Logic and Buttons ---
    def award_points(team_name, points):
        st.session_state.scores[team_name] += points
        st.session_state.points_awarded = True
        st.rerun()

    points_map = {'first_person': 3, 'team': 2, 'opposing_team': 1}
    points_to_award = points_map.get(st.session_state.timer_stage, 0)

    if points_to_award > 0:
        st.markdown(f"**Award {points_to_award} Points To:**")
        score_cols = st.columns(3)
        for i, team in enumerate(team_names):
            if score_cols[i].button(f"✅ {team}", use_container_width=True, disabled=st.session_state.points_awarded):
                award_points(team, points_to_award)

    st.markdown("---")

    # --- Control Buttons ---
    def start_timer(stage, duration_key):
        st.session_state.timer_running, st.session_state.sound_played = True, False
        st.session_state.timer_value = st.session_state.timers[duration_key]
        st.session_state.timer_start_time = time.time()
        st.session_state.timer_stage = stage
        st.session_state.points_awarded = False
        st.rerun()

    ctrl_cols = st.columns(4)
    if st.session_state.timer_stage == 'off':
        if ctrl_cols[0].button("Start Timer (3 Pts)", use_container_width=True):
            start_timer('first_person', 'x')
    elif st.session_state.timer_stage == 'first_person':
        if ctrl_cols[0].button("Start Timer (2 Pts)", use_container_width=True):
            start_timer('team', 'y')
    elif st.session_state.timer_stage == 'team':
        if ctrl_cols[0].button("Start Timer (1 Pt)", use_container_width=True):
            start_timer('opposing_team', 'z')

    if ctrl_cols[1].button("Stop Timer", use_container_width=True, disabled=not st.session_state.timer_running):
        st.session_state.timer_running = False
        st.rerun()

    # Remove Next Team button. Instead, automatically advance to next team after each round.

    if ctrl_cols[3].button("Reset Game"):
        st.session_state.clear()
        initialize_session_state()
        st.rerun()

    # Automatically advance to next team when timer_stage is reset to 'off' after a round
    if (
        not st.session_state.timer_running
        and st.session_state.timer_stage == 'off'
        and not st.session_state.points_awarded
        and 'last_team_idx' in st.session_state
        and st.session_state.last_team_idx != st.session_state.current_team_idx
    ):
        st.session_state.current_team_idx = (st.session_state.current_team_idx + 1) % 3
        st.session_state.last_team_idx = st.session_state.current_team_idx
        st.rerun()
    elif 'last_team_idx' not in st.session_state:
        st.session_state.last_team_idx = st.session_state.current_team_idx

    if st.session_state.timer_running:
        time.sleep(1)
        st.rerun()

    # Ensure beep sound is played at timer end (already handled in timer display logic)

# --- Main App Logic ---
def main():
    """Main function to control which UI mode to display."""
    if st.session_state.mode == 'setup':
        setup_mode()
    elif st.session_state.mode == 'scoring':
        scoring_mode()

if __name__ == '__main__':
    main()

