# quiz_app.py
import streamlit as st
import time
import base64
import wave
import struct
import math
import io
import streamlit.components.v1 as components # New: Import components library

# --- Sound file URL from GitHub ---
GITHUB_SOUND_URL = "https://raw.githubusercontent.com/Arishneel-Narayan/Quizzo/main/times-up-omagod"

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

def play_github_sound():
    """Embeds an HTML audio player for the GitHub-hosted sound file. Plays on user action (button click)."""
    components.html(f"""
        <audio id='timer-audio' src='{GITHUB_SOUND_URL}'></audio>
        <script>
        // Attach click handler to the play button
        window.addEventListener('DOMContentLoaded', function() {{
            var btn = window.parent.document.getElementById('play-timer-audio-btn');
            if(btn) {{
                btn.onclick = function() {{
                    var audio = document.getElementById('timer-audio');
                    if(audio) audio.play();
                }}
            }}
        }});
        </script>
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

    # --- Display Scoreboard (edit controls handled at bottom) ---
    cols = st.columns(3)
    for i, team in enumerate(team_names):
        with cols[i]:
            st.metric(label=f"**{team}**", value=f"{scores.get(team, 0)} Points")
    st.markdown("---")

    # ...existing code...

    # Place the edit toggle and controls at the very bottom, after all other controls

    # ...existing code for timer, scoring, and control buttons...

    # BOTTOM: Score Edit Controls
    st.markdown("---")
    show_edit = st.checkbox("Edit", value=False, key="show_edit_scores")
    if show_edit:
        st.markdown("<h4>Edit Scores</h4>", unsafe_allow_html=True)
        cols = st.columns(3)
        for i, team in enumerate(team_names):
            with cols[i]:
                st.write(f"**{team}**")
                col1, col2 = st.columns([1,1])
                with col1:
                    if st.button(f"➖", key=f"dec_{team}"):
                        st.session_state.scores[team] = max(0, st.session_state.scores[team] - 1)
                        st.rerun()
                with col2:
                    if st.button(f"➕", key=f"inc_{team}"):
                        st.session_state.scores[team] += 1
                        st.rerun()

    # --- Show current question stage and team ---
    stage_map = {
        'off': 'Ready for Next Question',
        'first_person': f"{current_team} (3 Points)",
        'team': f"{current_team} (2 Points)",
        'opposing_team': f"{team_names[(current_team_idx+1)%3]} & {team_names[(current_team_idx+2)%3]} (1 Point)"
    }
    st.markdown(f"<h3 style='text-align:center;'>Current Turn: <span style='color:#F4C430'>{stage_map.get(st.session_state.timer_stage, '')}</span></h3>", unsafe_allow_html=True)

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
                st.markdown("""
                    <div style='text-align:center; margin: 20px 0;'>
                        <span style='font-size:2rem; color:#F44336;'>⏰ Time's up!</span><br>
                        <button id='play-timer-audio-btn' style='margin-top:15px; font-size:1.2rem; background:#F4C430; color:white; border:none; border-radius:8px; padding:12px 32px; cursor:pointer;'>🔊 Play Time's Up Sound</button>
                    </div>
                """, unsafe_allow_html=True)
                play_github_sound()
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
        st.session_state.timer_running = False  # Stop timer immediately
        # Advance to next team if 3-point question, else stay for 2/1-point attempts
        if st.session_state.timer_stage == 'first_person':
            # After 3-point question, next team gets their 3-point question
            st.session_state.current_team_idx = (st.session_state.current_team_idx + 1) % 3
            st.session_state.timer_stage = 'off'
        else:
            # After 2 or 1 point, just reset to off for same team
            st.session_state.timer_stage = 'off'
        st.rerun()

    points_map = {'first_person': 3, 'team': 2, 'opposing_team': 1}
    points_to_award = points_map.get(st.session_state.timer_stage, 0)

    if points_to_award > 0:
        st.markdown(f"**Award {points_to_award} Points To:**")
        if st.session_state.timer_stage == 'first_person':
            # Only current team can get 3 points
            score_cols = st.columns(3)
            for i, team in enumerate(team_names):
                if i == current_team_idx:
                    if score_cols[i].button(f"✅ {team}", use_container_width=True, disabled=st.session_state.points_awarded):
                        award_points(team, points_to_award)
                else:
                    score_cols[i].button(f"{team}", use_container_width=True, disabled=True)
        elif st.session_state.timer_stage == 'team':
            # Only current team can get 2 points
            score_cols = st.columns(3)
            for i, team in enumerate(team_names):
                if i == current_team_idx:
                    if score_cols[i].button(f"✅ {team}", use_container_width=True, disabled=st.session_state.points_awarded):
                        award_points(team, points_to_award)
                else:
                    score_cols[i].button(f"{team}", use_container_width=True, disabled=True)
        elif st.session_state.timer_stage == 'opposing_team':
            # Only the two non-current teams can get 1 point
            score_cols = st.columns(3)
            for i, team in enumerate(team_names):
                if i != current_team_idx:
                    if score_cols[i].button(f"✅ {team}", use_container_width=True, disabled=st.session_state.points_awarded):
                        award_points(team, points_to_award)
                else:
                    score_cols[i].button(f"{team}", use_container_width=True, disabled=True)

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
        if ctrl_cols[0].button(f"Start Timer (3 Pts) for {current_team}", use_container_width=True):
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

    if ctrl_cols[3].button("Reset Game"):
        st.session_state.clear()
        initialize_session_state()
        st.rerun()

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

