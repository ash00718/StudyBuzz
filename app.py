import streamlit as st
import requests
import json
import re
import time
import random
from datetime import datetime, timedelta
from io import BytesIO

# ============== SESSION STATE INITIALIZATION ==============
def init_session_state():
    defaults = {
        'page': 'home',
        'study_mode': None,
        'quiz_type': 'multiple_choice',
        'current_topic': None,
        # Quiz states
        'quiz_data': None,
        'quiz_raw': None,
        'user_answers': {},
        'quiz_submitted': False,
        'tf_data': None,
        'fib_data': None,
        'fib_answers': {},
        # Flashcard states
        'flashcards_data': None,
        'flipped_cards': set(),
        'matching_pairs': None,
        'matched_pairs': set(),
        'matching_selected': None,
        # Study guide
        'study_guide_data': None,
        # Timer
        'timed_mode': False,
        'timer_duration': 60,
        'timer_start': None,
        'timer_expired': False,
        # Progress & Gamification
        'xp': 0,
        'total_quizzes': 0,
        'total_correct': 0,
        'total_questions': 0,
        'quiz_history': [],
        'achievements': set(),
        'study_streak': 0,
        'last_study_date': None,
        # Settings
        'subject': 'General',
        'grade_level': 'High School',
        'theme': 'dark',
        # AI Chat
        'chat_messages': [],
        'show_hints': {},
        'explanations': {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ============== PAGE CONFIG ==============
st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="📚",
    layout="wide"
)

# ============== THEME CSS ==============
def get_theme_css():
    if st.session_state.theme == 'dark':
        return """
        <style>
        .stApp { background-color: #0e1117; }
        .main-header { text-align: center; color: #ffffff !important; padding: 20px; }
        .subtitle { text-align: center; color: #b0b0b0 !important; font-size: 18px; margin-bottom: 30px; }
        .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
        p, span, div, label { color: #ffffff !important; }
        [data-testid="stSidebar"] { background-color: #1a1a2e; }
        [data-testid="stSidebar"] * { color: #ffffff !important; }
        .mode-card {
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
            border-radius: 20px; padding: 30px; text-align: center;
            border: 2px solid #3d3d5c; min-height: 180px;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            margin-bottom: 10px; transition: all 0.3s ease;
        }
        .mode-card:hover { border-color: #6366f1; box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3); }
        .mode-icon { font-size: 42px; margin-bottom: 15px; }
        .mode-title { font-size: 20px; font-weight: bold; color: #ffffff !important; margin-bottom: 8px; }
        .mode-description { font-size: 13px; color: #a0a0a0 !important; line-height: 1.4; }
        .flashcard {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
            border-radius: 15px; padding: 25px; min-height: 150px;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            text-align: center; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            border: 1px solid #3d7ab5; margin-bottom: 10px;
        }
        .flashcard-back {
            background: linear-gradient(135deg, #1a4731 0%, #2d7a4f 100%);
            border-color: #3db56a;
        }
        .flashcard-label { font-size: 12px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; opacity: 0.8; color: #a0c4e8 !important; }
        .flashcard-content { font-size: 18px; font-weight: 500; color: #ffffff !important; line-height: 1.5; }
        .quiz-question {
            background: linear-gradient(135deg, #2d2d44 0%, #3d3d5c 100%);
            border-radius: 12px; padding: 20px; margin: 15px 0; border-left: 4px solid #6366f1;
        }
        .quiz-question h4 { color: #ffffff !important; margin-bottom: 15px; }
        .correct-answer { background: linear-gradient(135deg, #1a4731 0%, #2d7a4f 100%) !important; border-left-color: #22c55e !important; }
        .incorrect-answer { background: linear-gradient(135deg, #4a1a1a 0%, #7a2d2d 100%) !important; border-left-color: #ef4444 !important; }
        .results-box {
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
            border-radius: 15px; padding: 30px; text-align: center; margin: 20px 0; border: 2px solid #6366f1;
        }
        .score-display { font-size: 48px; font-weight: bold; color: #6366f1 !important; margin: 10px 0; }
        .xp-bar { background: #2d2d44; border-radius: 10px; height: 24px; overflow: hidden; margin: 10px 0; }
        .xp-fill { background: linear-gradient(90deg, #6366f1, #8b5cf6); height: 100%; transition: width 0.5s ease; }
        .achievement { background: linear-gradient(135deg, #4a3f00 0%, #6b5a00 100%); border-radius: 10px; padding: 10px 15px; margin: 5px; display: inline-block; border: 1px solid #fbbf24; }
        .stat-card { background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%); border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #3d3d5c; }
        .timer-display { font-size: 36px; font-weight: bold; color: #ef4444 !important; text-align: center; padding: 10px; background: rgba(239, 68, 68, 0.1); border-radius: 10px; margin: 10px 0; }
        .hint-box { background: linear-gradient(135deg, #3d3d00 0%, #5a5a00 100%); border-radius: 10px; padding: 15px; margin: 10px 0; border-left: 4px solid #fbbf24; }
        .explanation-box { background: linear-gradient(135deg, #1a3a4a 0%, #2d5a6a 100%); border-radius: 10px; padding: 15px; margin: 10px 0; border-left: 4px solid #38bdf8; }
        .matching-card { background: linear-gradient(135deg, #2d2d44 0%, #3d3d5c 100%); border-radius: 10px; padding: 15px; margin: 5px; text-align: center; cursor: pointer; border: 2px solid #3d3d5c; transition: all 0.2s; }
        .matching-card:hover { border-color: #6366f1; }
        .matching-card.selected { border-color: #fbbf24; background: linear-gradient(135deg, #4a3f00 0%, #5a4f00 100%); }
        .matching-card.matched { border-color: #22c55e; background: linear-gradient(135deg, #1a4731 0%, #2d5a4f 100%); opacity: 0.7; }
        .footer { text-align: center; color: #888888 !important; padding: 20px; }
        .footer p { color: #888888 !important; }
        .stButton > button { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 500; }
        .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4); }
        .stRadio label { color: #ffffff !important; }
        .chat-message { padding: 15px; border-radius: 10px; margin: 10px 0; }
        .chat-user { background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); margin-left: 20%; }
        .chat-ai { background: linear-gradient(135deg, #2d2d44 0%, #3d3d5c 100%); margin-right: 20%; }
        </style>
        """
    else:
        return """
        <style>
        .stApp { background-color: #ffffff; }
        .main-header { text-align: center; color: #1e1e2e !important; padding: 20px; }
        .subtitle { text-align: center; color: #666666 !important; font-size: 18px; margin-bottom: 30px; }
        .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span, p, span, div, label { color: #1e1e2e !important; }
        [data-testid="stSidebar"] { background-color: #f0f2f6; }
        [data-testid="stSidebar"] * { color: #1e1e2e !important; }
        .mode-card { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 20px; padding: 30px; text-align: center; border: 2px solid #dee2e6; min-height: 180px; margin-bottom: 10px; }
        .mode-card:hover { border-color: #6366f1; }
        .mode-title { color: #1e1e2e !important; }
        .mode-description { color: #666666 !important; }
        .flashcard { background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); border-color: #2196f3; }
        .flashcard-back { background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); border-color: #4caf50; }
        .flashcard-label { color: #1565c0 !important; }
        .flashcard-content { color: #1e1e2e !important; }
        .quiz-question { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); }
        .quiz-question h4 { color: #1e1e2e !important; }
        .results-box { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-color: #6366f1; }
        .score-display { color: #6366f1 !important; }
        .stat-card { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-color: #dee2e6; }
        .footer p { color: #666666 !important; }
        </style>
        """

st.markdown(get_theme_css(), unsafe_allow_html=True)

# ============== HELPER FUNCTIONS ==============
ACHIEVEMENTS = {
    'first_quiz': {'name': '🎯 First Quiz', 'desc': 'Complete your first quiz', 'xp': 50},
    'perfect_score': {'name': '⭐ Perfect Score', 'desc': 'Get 100% on a quiz', 'xp': 100},
    'quiz_master': {'name': '🏆 Quiz Master', 'desc': 'Complete 10 quizzes', 'xp': 200},
    'streak_3': {'name': '🔥 On Fire', 'desc': '3 day study streak', 'xp': 150},
    'streak_7': {'name': '💪 Dedicated', 'desc': '7 day study streak', 'xp': 300},
    'flash_50': {'name': '🎴 Card Shark', 'desc': 'Flip 50 flashcards', 'xp': 100},
    'speed_demon': {'name': '⚡ Speed Demon', 'desc': 'Complete timed quiz with 80%+', 'xp': 150},
    'explorer': {'name': '🧭 Explorer', 'desc': 'Try all study modes', 'xp': 100},
}

def add_xp(amount):
    st.session_state.xp += amount

def check_achievements():
    new_achievements = []
    
    if st.session_state.total_quizzes >= 1 and 'first_quiz' not in st.session_state.achievements:
        st.session_state.achievements.add('first_quiz')
        new_achievements.append('first_quiz')
        add_xp(ACHIEVEMENTS['first_quiz']['xp'])
    
    if st.session_state.total_quizzes >= 10 and 'quiz_master' not in st.session_state.achievements:
        st.session_state.achievements.add('quiz_master')
        new_achievements.append('quiz_master')
        add_xp(ACHIEVEMENTS['quiz_master']['xp'])
    
    if st.session_state.study_streak >= 3 and 'streak_3' not in st.session_state.achievements:
        st.session_state.achievements.add('streak_3')
        new_achievements.append('streak_3')
        add_xp(ACHIEVEMENTS['streak_3']['xp'])
    
    if st.session_state.study_streak >= 7 and 'streak_7' not in st.session_state.achievements:
        st.session_state.achievements.add('streak_7')
        new_achievements.append('streak_7')
        add_xp(ACHIEVEMENTS['streak_7']['xp'])
    
    return new_achievements

def update_streak():
    today = datetime.now().date()
    if st.session_state.last_study_date:
        last_date = st.session_state.last_study_date
        if isinstance(last_date, str):
            last_date = datetime.fromisoformat(last_date).date()
        
        if today == last_date:
            return
        elif today - last_date == timedelta(days=1):
            st.session_state.study_streak += 1
        else:
            st.session_state.study_streak = 1
    else:
        st.session_state.study_streak = 1
    
    st.session_state.last_study_date = today.isoformat()

def get_level():
    xp = st.session_state.xp
    level = 1
    xp_needed = 100
    while xp >= xp_needed:
        xp -= xp_needed
        level += 1
        xp_needed = int(xp_needed * 1.5)
    return level, xp, xp_needed

def parse_quiz(quiz_text):
    questions = []
    q_pattern = r'Q\d+[:\.]?\s*'
    parts = re.split(q_pattern, quiz_text)
    
    for part in parts[1:]:
        if not part.strip():
            continue
        lines = part.strip().split('\n')
        question_text = ""
        options = {}
        correct_answer = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if 'correct' in line.lower() and 'answer' in line.lower():
                answer_match = re.search(r'[:\s]+([A-D])\b', line, re.IGNORECASE)
                if answer_match:
                    correct_answer = answer_match.group(1).upper()
                continue
            option_match = re.match(r'^\(?([A-D])\)?[\.\):]?\s*(.+)', line, re.IGNORECASE)
            if option_match:
                letter = option_match.group(1).upper()
                text = option_match.group(2).strip()
                options[letter] = text
            elif not options:
                question_text += line + " "
        
        if question_text and len(options) >= 2 and correct_answer:
            questions.append({'question': question_text.strip(), 'options': options, 'correct': correct_answer})
    return questions

def parse_tf_quiz(text):
    questions = []
    lines = text.strip().split('\n')
    current_q = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        q_match = re.match(r'^\d+[\.\)]\s*(.+)', line)
        if q_match:
            if current_q:
                questions.append(current_q)
            current_q = {'question': q_match.group(1), 'answer': None}
        elif current_q and ('true' in line.lower() or 'false' in line.lower()):
            if 'true' in line.lower() and 'false' not in line.lower():
                current_q['answer'] = True
            elif 'false' in line.lower():
                current_q['answer'] = False
    
    if current_q and current_q['answer'] is not None:
        questions.append(current_q)
    
    return questions

def parse_fib_quiz(text):
    questions = []
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        q_match = re.match(r'^\d+[\.\)]\s*(.+)', line)
        if q_match:
            content = q_match.group(1)
            blank_match = re.search(r'\[([^\]]+)\]|_+([^_]+)_+|\*\*([^\*]+)\*\*', content)
            if blank_match:
                answer = blank_match.group(1) or blank_match.group(2) or blank_match.group(3)
                question = re.sub(r'\[[^\]]+\]|_+[^_]+_+|\*\*[^\*]+\*\*', '_____', content)
                questions.append({'question': question, 'answer': answer.strip()})
    
    return questions

def parse_flashcards(flashcards_text):
    cards = []
    parts = re.split(r'CARD\s*\d*', flashcards_text, flags=re.IGNORECASE)
    
    for part in parts:
        if not part.strip():
            continue
        front_match = re.search(r'Front:\s*(.+?)(?=Back:|$)', part, re.DOTALL | re.IGNORECASE)
        back_match = re.search(r'Back:\s*(.+?)(?=Front:|CARD|$)', part, re.DOTALL | re.IGNORECASE)
        
        if front_match and back_match:
            front = front_match.group(1).strip()
            back = back_match.group(1).strip()
            if front and back:
                cards.append({'front': front, 'back': back})
    return cards

def reset_study_data():
    keys_to_reset = ['quiz_data', 'quiz_raw', 'user_answers', 'quiz_submitted', 'tf_data', 
                     'fib_data', 'fib_answers', 'flashcards_data', 'flipped_cards', 
                     'matching_pairs', 'matched_pairs', 'matching_selected', 'study_guide_data',
                     'timer_start', 'timer_expired', 'chat_messages', 'show_hints', 'explanations']
    for key in keys_to_reset:
        if key in ['flipped_cards', 'matched_pairs', 'achievements']:
            st.session_state[key] = set()
        elif key in ['user_answers', 'fib_answers', 'show_hints', 'explanations']:
            st.session_state[key] = {}
        elif key == 'chat_messages':
            st.session_state[key] = []
        else:
            st.session_state[key] = None

def go_home():
    st.session_state.page = "home"
    st.session_state.study_mode = None
    reset_study_data()

def call_ai(prompt, system_msg="You are a helpful educational assistant."):
    try:
        response = requests.post(
            "https://text.pollinations.ai/",
            json={"messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": prompt}], "model": "openai"},
            timeout=60
        )
        if response.status_code == 200:
            return response.text
    except:
        pass
    return None

# ============== HOME PAGE ==============
if st.session_state.page == "home":
    st.markdown("<h1 class='main-header'>📚 AI Study Buddy</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Your AI-powered study companion with quizzes, flashcards, and more!</p>", unsafe_allow_html=True)
    
    # Stats bar
    level, current_xp, xp_needed = get_level()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='stat-card'><h3>⭐ Level {level}</h3><p>{current_xp}/{xp_needed} XP</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='stat-card'><h3>🔥 {st.session_state.study_streak} Day Streak</h3></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='stat-card'><h3>📝 {st.session_state.total_quizzes} Quizzes</h3></div>", unsafe_allow_html=True)
    with col4:
        accuracy = (st.session_state.total_correct / st.session_state.total_questions * 100) if st.session_state.total_questions > 0 else 0
        st.markdown(f"<div class='stat-card'><h3>🎯 {accuracy:.0f}% Accuracy</h3></div>", unsafe_allow_html=True)
    
    st.markdown("")
    
    # Mode selection
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""<div class='mode-card'><div class='mode-icon'>📝</div><div class='mode-title'>Quiz Mode</div>
        <div class='mode-description'>Multiple choice, True/False, and Fill-in-the-blank questions with timer option!</div></div>""", unsafe_allow_html=True)
        if st.button("Start Quiz", key="quiz_btn", use_container_width=True):
            st.session_state.page = "study"
            st.session_state.study_mode = "Quiz"
            st.rerun()
    
    with col2:
        st.markdown("""<div class='mode-card'><div class='mode-icon'>🎴</div><div class='mode-title'>Flashcards</div>
        <div class='mode-description'>Flip cards and matching game for effective memorization!</div></div>""", unsafe_allow_html=True)
        if st.button("Start Flashcards", key="flash_btn", use_container_width=True):
            st.session_state.page = "study"
            st.session_state.study_mode = "Flashcards"
            st.rerun()
    
    with col3:
        st.markdown("""<div class='mode-card'><div class='mode-icon'>📖</div><div class='mode-title'>Study Guide</div>
        <div class='mode-description'>Comprehensive guides with key concepts and AI chat!</div></div>""", unsafe_allow_html=True)
        if st.button("Start Study Guide", key="guide_btn", use_container_width=True):
            st.session_state.page = "study"
            st.session_state.study_mode = "Study Guide"
            st.rerun()
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown("""<div class='mode-card'><div class='mode-icon'>🚀</div><div class='mode-title'>All-In-One</div>
        <div class='mode-description'>Generate quiz, flashcards, and study guide together!</div></div>""", unsafe_allow_html=True)
        if st.button("Start All-In-One", key="all_btn", use_container_width=True):
            st.session_state.page = "study"
            st.session_state.study_mode = "All Three"
            st.rerun()
    
    with col5:
        st.markdown("""<div class='mode-card'><div class='mode-icon'>🏆</div><div class='mode-title'>Achievements</div>
        <div class='mode-description'>View your badges and track your progress!</div></div>""", unsafe_allow_html=True)
        if st.button("View Achievements", key="ach_btn", use_container_width=True):
            st.session_state.page = "achievements"
            st.rerun()
    
    with col6:
        st.markdown("""<div class='mode-card'><div class='mode-icon'>📊</div><div class='mode-title'>Statistics</div>
        <div class='mode-description'>View your study history and performance!</div></div>""", unsafe_allow_html=True)
        if st.button("View Statistics", key="stats_btn", use_container_width=True):
            st.session_state.page = "statistics"
            st.rerun()
    
    # Theme toggle in sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        theme = st.selectbox("🎨 Theme", ["Dark", "Light"], index=0 if st.session_state.theme == 'dark' else 1)
        if theme.lower() != st.session_state.theme:
            st.session_state.theme = theme.lower()
            st.rerun()
        
        st.session_state.subject = st.selectbox("📚 Subject", ["General", "Math", "Science", "History", "Language", "Computer Science", "Art", "Music"])
        st.session_state.grade_level = st.selectbox("🎓 Grade Level", ["Elementary", "Middle School", "High School", "College", "Professional"])
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("Powered by **Pollinations.AI** 🌸")

# ============== ACHIEVEMENTS PAGE ==============
elif st.session_state.page == "achievements":
    st.markdown("<h1 class='main-header'>🏆 Achievements</h1>", unsafe_allow_html=True)
    
    with st.sidebar:
        if st.button("← Back to Home", use_container_width=True):
            go_home()
            st.rerun()
    
    # XP Progress
    level, current_xp, xp_needed = get_level()
    st.markdown(f"### ⭐ Level {level}")
    st.progress(current_xp / xp_needed)
    st.markdown(f"**{current_xp} / {xp_needed} XP** to next level")
    
    st.markdown("---")
    st.markdown("### 🎖️ Your Badges")
    
    cols = st.columns(4)
    for i, (key, ach) in enumerate(ACHIEVEMENTS.items()):
        with cols[i % 4]:
            earned = key in st.session_state.achievements
            opacity = "1" if earned else "0.4"
            st.markdown(f"""
            <div class='achievement' style='opacity: {opacity}'>
                <h4>{ach['name']}</h4>
                <p style='font-size: 12px;'>{ach['desc']}</p>
                <p style='font-size: 11px; color: #fbbf24;'>+{ach['xp']} XP</p>
            </div>
            """, unsafe_allow_html=True)

# ============== STATISTICS PAGE ==============
elif st.session_state.page == "statistics":
    st.markdown("<h1 class='main-header'>📊 Statistics</h1>", unsafe_allow_html=True)
    
    with st.sidebar:
        if st.button("← Back to Home", use_container_width=True):
            go_home()
            st.rerun()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Quizzes", st.session_state.total_quizzes)
    with col2:
        st.metric("Questions Answered", st.session_state.total_questions)
    with col3:
        st.metric("Correct Answers", st.session_state.total_correct)
    with col4:
        accuracy = (st.session_state.total_correct / st.session_state.total_questions * 100) if st.session_state.total_questions > 0 else 0
        st.metric("Accuracy", f"{accuracy:.1f}%")
    
    st.markdown("---")
    st.markdown("### 📈 Recent Quiz History")
    
    if st.session_state.quiz_history:
        for i, quiz in enumerate(reversed(st.session_state.quiz_history[-10:])):
            st.markdown(f"**{quiz['topic']}** - {quiz['score']}/{quiz['total']} ({quiz['percentage']:.0f}%) - {quiz['date']}")
    else:
        st.info("No quiz history yet. Complete a quiz to see your progress!")

# ============== STUDY PAGE ==============
elif st.session_state.page == "study":
    study_mode = st.session_state.study_mode
    
    # Sidebar
    with st.sidebar:
        if st.button("← Back to Home", use_container_width=True):
            go_home()
            st.rerun()
        
        st.markdown("---")
        st.header("⚙️ Settings")
        st.markdown(f"**Mode:** {study_mode}")
        
        if study_mode in ["Quiz", "All Three"]:
            st.session_state.quiz_type = st.selectbox("Quiz Type", ["Multiple Choice", "True/False", "Fill in the Blank"])
            difficulty = st.select_slider("Difficulty", options=["Easy", "Medium", "Hard"])
            num_questions = st.slider("Questions", 3, 15, 5)
            st.session_state.timed_mode = st.checkbox("⏱️ Timed Mode")
            if st.session_state.timed_mode:
                st.session_state.timer_duration = st.slider("Time (seconds)", 30, 300, 60)
        else:
            difficulty = "Medium"
            num_questions = 5
        
        if study_mode in ["Flashcards", "All Three"]:
            num_flashcards = st.slider("Flashcards", 5, 20, 10)
            flashcard_mode = st.selectbox("Flashcard Mode", ["Flip Cards", "Matching Game"])
        else:
            num_flashcards = 10
            flashcard_mode = "Flip Cards"
        
        st.markdown("---")
        st.markdown(f"**Subject:** {st.session_state.subject}")
        st.markdown(f"**Level:** {st.session_state.grade_level}")
    
    # Header
    mode_icons = {"Quiz": "📝", "Flashcards": "🎴", "Study Guide": "📖", "All Three": "🚀"}
    st.markdown(f"<h1 class='main-header'>{mode_icons.get(study_mode, '📚')} {study_mode} Mode</h1>", unsafe_allow_html=True)
    
    # Topic input
    topic = st.text_input("📖 Enter a topic to study:", placeholder="e.g., Photosynthesis, World War 2, Quadratic Equations")
    
    # Generate button
    if st.button("🚀 Generate Study Materials", type="primary"):
        if not topic:
            st.warning("Please enter a topic first!")
        else:
            reset_study_data()
            st.session_state.current_topic = topic
            update_streak()
            
            with st.spinner("🤖 AI is preparing your study materials..."):
                subject_context = f"for {st.session_state.grade_level} level {st.session_state.subject}" if st.session_state.subject != "General" else ""
                
                # Generate Quiz
                if study_mode in ["Quiz", "All Three"]:
                    quiz_type = st.session_state.quiz_type
                    
                    if quiz_type == "Multiple Choice":
                        prompt = f"""Generate a {difficulty} difficulty quiz about {topic} {subject_context} with {num_questions} multiple choice questions.

Format EXACTLY like this:
Q1: [Question]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Correct Answer: [A/B/C/D]

Q2: [Question]
..."""
                        result = call_ai(prompt)
                        if result:
                            st.session_state.quiz_data = parse_quiz(result)
                    
                    elif quiz_type == "True/False":
                        prompt = f"""Generate {num_questions} True/False questions about {topic} {subject_context}.

Format EXACTLY like this:
1. [Statement that is either true or false]
Answer: True

2. [Statement that is either true or false]
Answer: False

Continue for all {num_questions} questions."""
                        result = call_ai(prompt)
                        if result:
                            st.session_state.tf_data = parse_tf_quiz(result)
                    
                    elif quiz_type == "Fill in the Blank":
                        prompt = f"""Generate {num_questions} fill-in-the-blank questions about {topic} {subject_context}.

Format EXACTLY like this:
1. The process of [photosynthesis] converts sunlight into energy.
2. The capital of France is [Paris].

Put the answer in [brackets]. Continue for all {num_questions} questions."""
                        result = call_ai(prompt)
                        if result:
                            st.session_state.fib_data = parse_fib_quiz(result)
                    
                    if st.session_state.timed_mode:
                        st.session_state.timer_start = time.time()
                
                # Generate Flashcards
                if study_mode in ["Flashcards", "All Three"]:
                    prompt = f"""Generate {num_flashcards} flashcards about {topic} {subject_context}.

Format EXACTLY like this:
CARD 1
Front: [Question or term]
Back: [Answer or definition]

CARD 2
Front: [Question or term]
Back: [Answer or definition]"""
                    result = call_ai(prompt)
                    if result:
                        cards = parse_flashcards(result)
                        st.session_state.flashcards_data = cards
                        if flashcard_mode == "Matching Game" and cards:
                            random.shuffle(cards)
                            st.session_state.matching_pairs = cards[:min(6, len(cards))]
                
                # Generate Study Guide
                if study_mode in ["Study Guide", "All Three"]:
                    prompt = f"""Create a comprehensive study guide about {topic} {subject_context}.

Include:
1. Overview (2-3 sentences)
2. Key Concepts (5 main ideas with explanations)
3. Important Terms and Definitions
4. Common Misconceptions
5. Practice Tips
6. Related Topics to Explore

Make it clear and engaging for students."""
                    result = call_ai(prompt)
                    if result:
                        st.session_state.study_guide_data = result
                
                st.success("✅ Study materials generated!")
                st.balloons()
                new_achs = check_achievements()
                for ach in new_achs:
                    st.toast(f"🏆 Achievement Unlocked: {ACHIEVEMENTS[ach]['name']}")
                st.rerun()
    
    # ============== DISPLAY TIMER ==============
    if st.session_state.timed_mode and st.session_state.timer_start and not st.session_state.quiz_submitted:
        elapsed = time.time() - st.session_state.timer_start
        remaining = max(0, st.session_state.timer_duration - int(elapsed))
        
        if remaining > 0:
            mins, secs = divmod(remaining, 60)
            st.markdown(f"<div class='timer-display'>⏱️ {mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
        else:
            st.session_state.timer_expired = True
            st.warning("⏰ Time's up! Submitting your quiz...")
            st.session_state.quiz_submitted = True
            st.rerun()
    
    # ============== DISPLAY MULTIPLE CHOICE QUIZ ==============
    if st.session_state.quiz_data and study_mode in ["Quiz", "All Three"]:
        st.markdown("---")
        st.header("📝 Multiple Choice Quiz")
        
        questions = st.session_state.quiz_data
        
        if not st.session_state.quiz_submitted:
            for i, q in enumerate(questions):
                st.markdown(f"<div class='quiz-question'><h4>Q{i+1}: {q['question']}</h4></div>", unsafe_allow_html=True)
                
                # Hint button
                if st.button(f"💡 Hint", key=f"hint_{i}"):
                    if i not in st.session_state.show_hints:
                        hint = call_ai(f"Give a brief hint (1 sentence) for this question without revealing the answer: {q['question']}")
                        st.session_state.show_hints[i] = hint or "Think about the key concepts related to this topic."
                    st.rerun()
                
                if i in st.session_state.show_hints:
                    st.markdown(f"<div class='hint-box'>💡 {st.session_state.show_hints[i]}</div>", unsafe_allow_html=True)
                
                options = [f"{letter}) {text}" for letter, text in sorted(q['options'].items())]
                selected = st.radio(f"Answer for Q{i+1}:", options, key=f"q_{i}", index=None, label_visibility="collapsed")
                if selected:
                    st.session_state.user_answers[i] = selected[0]
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                answered = len(st.session_state.user_answers)
                st.markdown(f"**Answered: {answered}/{len(questions)}**")
                if st.button("📊 Submit Quiz", type="primary", use_container_width=True):
                    st.session_state.quiz_submitted = True
                    st.rerun()
        
        else:
            # Show results
            correct_count = 0
            for i, q in enumerate(questions):
                user_answer = st.session_state.user_answers.get(i, "")
                is_correct = user_answer == q['correct']
                if is_correct:
                    correct_count += 1
                
                status = "correct-answer" if is_correct else "incorrect-answer"
                icon = "✅" if is_correct else "❌"
                st.markdown(f"<div class='quiz-question {status}'><h4>{icon} Q{i+1}: {q['question']}</h4></div>", unsafe_allow_html=True)
                
                for letter, text in sorted(q['options'].items()):
                    if letter == q['correct']:
                        st.markdown(f"✅ **{letter}) {text}** *(Correct)*")
                    elif letter == user_answer and not is_correct:
                        st.markdown(f"❌ ~~{letter}) {text}~~ *(Your Answer)*")
                    else:
                        st.markdown(f"{letter}) {text}")
                
                # Explain wrong answer
                if not is_correct:
                    if st.button(f"🤔 Explain Why", key=f"explain_{i}"):
                        if i not in st.session_state.explanations:
                            exp = call_ai(f"Explain why the answer to '{q['question']}' is '{q['options'][q['correct']]}' and not '{q['options'].get(user_answer, 'not answered')}'. Keep it brief (2-3 sentences).")
                            st.session_state.explanations[i] = exp or "The correct answer is based on the fundamental concepts of this topic."
                        st.rerun()
                    
                    if i in st.session_state.explanations:
                        st.markdown(f"<div class='explanation-box'>📚 {st.session_state.explanations[i]}</div>", unsafe_allow_html=True)
            
            # Update stats
            st.session_state.total_quizzes += 1
            st.session_state.total_correct += correct_count
            st.session_state.total_questions += len(questions)
            
            score_pct = (correct_count / len(questions)) * 100
            st.session_state.quiz_history.append({
                'topic': st.session_state.current_topic,
                'score': correct_count,
                'total': len(questions),
                'percentage': score_pct,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            
            # XP reward
            xp_earned = correct_count * 10
            if score_pct == 100:
                xp_earned += 50
                if 'perfect_score' not in st.session_state.achievements:
                    st.session_state.achievements.add('perfect_score')
                    add_xp(ACHIEVEMENTS['perfect_score']['xp'])
                    st.toast("🏆 Achievement: Perfect Score!")
            
            if st.session_state.timed_mode and score_pct >= 80:
                if 'speed_demon' not in st.session_state.achievements:
                    st.session_state.achievements.add('speed_demon')
                    add_xp(ACHIEVEMENTS['speed_demon']['xp'])
                    st.toast("🏆 Achievement: Speed Demon!")
            
            add_xp(xp_earned)
            
            st.markdown(f"""
            <div class='results-box'>
                <h2>📊 Quiz Results</h2>
                <div class='score-display'>{correct_count}/{len(questions)}</div>
                <p style='font-size: 24px;'>{score_pct:.0f}%</p>
                <p style='color: #6366f1;'>+{xp_earned} XP earned!</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Retake Quiz", use_container_width=True):
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.show_hints = {}
                st.session_state.explanations = {}
                if st.session_state.timed_mode:
                    st.session_state.timer_start = time.time()
                st.rerun()
    
    # ============== DISPLAY TRUE/FALSE QUIZ ==============
    if st.session_state.tf_data and study_mode in ["Quiz", "All Three"]:
        st.markdown("---")
        st.header("📝 True/False Quiz")
        
        questions = st.session_state.tf_data
        
        if not st.session_state.quiz_submitted:
            for i, q in enumerate(questions):
                st.markdown(f"<div class='quiz-question'><h4>Q{i+1}: {q['question']}</h4></div>", unsafe_allow_html=True)
                selected = st.radio(f"Answer:", ["True", "False"], key=f"tf_{i}", index=None, horizontal=True)
                if selected:
                    st.session_state.user_answers[i] = selected == "True"
            
            if st.button("📊 Submit Quiz", type="primary"):
                st.session_state.quiz_submitted = True
                st.rerun()
        
        else:
            correct_count = 0
            for i, q in enumerate(questions):
                user_answer = st.session_state.user_answers.get(i)
                is_correct = user_answer == q['answer']
                if is_correct:
                    correct_count += 1
                
                status = "correct-answer" if is_correct else "incorrect-answer"
                icon = "✅" if is_correct else "❌"
                st.markdown(f"<div class='quiz-question {status}'><h4>{icon} {q['question']}</h4><p>Correct Answer: {q['answer']}</p></div>", unsafe_allow_html=True)
            
            score_pct = (correct_count / len(questions)) * 100
            add_xp(correct_count * 10)
            
            st.markdown(f"<div class='results-box'><h2>Score: {correct_count}/{len(questions)} ({score_pct:.0f}%)</h2></div>", unsafe_allow_html=True)
    
    # ============== DISPLAY FILL IN THE BLANK ==============
    if st.session_state.fib_data and study_mode in ["Quiz", "All Three"]:
        st.markdown("---")
        st.header("📝 Fill in the Blank")
        
        questions = st.session_state.fib_data
        
        if not st.session_state.quiz_submitted:
            for i, q in enumerate(questions):
                st.markdown(f"**{i+1}. {q['question']}**")
                answer = st.text_input(f"Your answer:", key=f"fib_{i}", label_visibility="collapsed")
                st.session_state.fib_answers[i] = answer
            
            if st.button("📊 Submit Quiz", type="primary"):
                st.session_state.quiz_submitted = True
                st.rerun()
        
        else:
            correct_count = 0
            for i, q in enumerate(questions):
                user_answer = st.session_state.fib_answers.get(i, "").strip().lower()
                correct_answer = q['answer'].lower()
                is_correct = user_answer == correct_answer
                if is_correct:
                    correct_count += 1
                
                icon = "✅" if is_correct else "❌"
                st.markdown(f"{icon} **{q['question']}**")
                st.markdown(f"Your answer: {st.session_state.fib_answers.get(i, 'No answer')} | Correct: **{q['answer']}**")
            
            score_pct = (correct_count / len(questions)) * 100
            add_xp(correct_count * 10)
            st.markdown(f"<div class='results-box'><h2>Score: {correct_count}/{len(questions)} ({score_pct:.0f}%)</h2></div>", unsafe_allow_html=True)
    
    # ============== DISPLAY FLASHCARDS ==============
    if st.session_state.flashcards_data and study_mode in ["Flashcards", "All Three"]:
        st.markdown("---")
        st.header("🎴 Flashcards")
        
        cards = st.session_state.flashcards_data
        
        # Check which mode
        if st.session_state.matching_pairs:
            # Matching Game
            st.markdown("### Match the terms with their definitions!")
            pairs = st.session_state.matching_pairs
            
            # Create shuffled lists
            terms = [p['front'] for p in pairs]
            definitions = [p['back'] for p in pairs]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Terms:**")
                for i, term in enumerate(terms):
                    matched = i in st.session_state.matched_pairs
                    if matched:
                        st.markdown(f"<div class='matching-card matched'>✅ {term}</div>", unsafe_allow_html=True)
                    else:
                        if st.button(term, key=f"term_{i}"):
                            st.session_state.matching_selected = ('term', i, term)
                            st.rerun()
            
            with col2:
                st.markdown("**Definitions:**")
                for i, defn in enumerate(definitions):
                    matched = i in st.session_state.matched_pairs
                    if matched:
                        st.markdown(f"<div class='matching-card matched'>✅ {defn[:50]}...</div>", unsafe_allow_html=True)
                    else:
                        if st.button(defn[:50] + "...", key=f"def_{i}"):
                            if st.session_state.matching_selected and st.session_state.matching_selected[0] == 'term':
                                term_idx = st.session_state.matching_selected[1]
                                if pairs[term_idx]['back'] == defn:
                                    st.session_state.matched_pairs.add(term_idx)
                                    add_xp(5)
                                    st.success("✅ Correct match!")
                                else:
                                    st.error("❌ Try again!")
                                st.session_state.matching_selected = None
                            st.rerun()
            
            if len(st.session_state.matched_pairs) == len(pairs):
                st.balloons()
                st.success("🎉 All matched! Great job!")
        
        else:
            # Regular Flip Cards
            total_cards = len(cards)
            flipped_count = len(st.session_state.flipped_cards)
            
            st.progress(flipped_count / total_cards)
            st.markdown(f"**Progress: {flipped_count}/{total_cards} cards**")
            
            if st.button("🔄 Reset All"):
                st.session_state.flipped_cards = set()
                st.rerun()
            
            cols = st.columns(2)
            for idx, card in enumerate(cards):
                with cols[idx % 2]:
                    card_id = f"card_{idx}"
                    is_flipped = card_id in st.session_state.flipped_cards
                    
                    if not is_flipped:
                        st.markdown(f"<div class='flashcard'><div class='flashcard-label'>Term</div><div class='flashcard-content'>{card['front']}</div></div>", unsafe_allow_html=True)
                        if st.button("🔄 Flip", key=f"flip_{idx}"):
                            st.session_state.flipped_cards.add(card_id)
                            st.rerun()
                    else:
                        st.markdown(f"<div class='flashcard flashcard-back'><div class='flashcard-label'>Definition</div><div class='flashcard-content'>{card['back']}</div></div>", unsafe_allow_html=True)
                        if st.button("↩️ Back", key=f"unflip_{idx}"):
                            st.session_state.flipped_cards.remove(card_id)
                            st.rerun()
    
    # ============== DISPLAY STUDY GUIDE ==============
    if st.session_state.study_guide_data and study_mode in ["Study Guide", "All Three"]:
        st.markdown("---")
        st.header("📖 Study Guide")
        st.markdown(st.session_state.study_guide_data)
        
        # AI Chat for follow-up questions
        st.markdown("---")
        st.markdown("### 💬 Ask Follow-up Questions")
        
        for msg in st.session_state.chat_messages:
            role_class = "chat-user" if msg['role'] == 'user' else "chat-ai"
            st.markdown(f"<div class='chat-message {role_class}'>{msg['content']}</div>", unsafe_allow_html=True)
        
        user_question = st.text_input("Ask a question about this topic:", key="chat_input")
        if st.button("Send", key="chat_send"):
            if user_question:
                st.session_state.chat_messages.append({'role': 'user', 'content': user_question})
                
                response = call_ai(f"The user is studying {st.session_state.current_topic}. Answer their question: {user_question}")
                if response:
                    st.session_state.chat_messages.append({'role': 'ai', 'content': response})
                
                st.rerun()
    
    # ============== RELATED TOPICS ==============
    if st.session_state.current_topic and (st.session_state.quiz_data or st.session_state.study_guide_data or st.session_state.flashcards_data):
        st.markdown("---")
        st.markdown("### 🔗 Related Topics to Explore")
        if st.button("Get Suggestions"):
            related = call_ai(f"List 5 related topics to {st.session_state.current_topic} that a student might want to study next. Just list the topics, one per line.")
            if related:
                st.markdown(related)
    
    # ============== DIAGRAM COMING SOON ==============
    if st.session_state.quiz_data or st.session_state.flashcards_data or st.session_state.study_guide_data:
        st.markdown("---")
        st.header("🖼️ Study Diagram")
        st.markdown("""
        <div style='background: linear-gradient(135deg, #2d2d44 0%, #3d3d5c 100%); 
                    border-radius: 15px; padding: 40px; text-align: center; border: 2px dashed #6366f1;'>
            <p style='font-size: 48px;'>🎨</p>
            <h3>Coming Soon!</h3>
            <p style='color: #a0a0a0;'>AI-generated study diagrams will be available in a future update.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("<div class='footer'><p>Made with ❤️ for students everywhere | Powered by Pollinations.AI</p></div>", unsafe_allow_html=True)
