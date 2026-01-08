import streamlit as st
import json
import re
import time
import random
from datetime import datetime, timedelta
from openai import OpenAI

# ============== API CLIENT SETUP ==============
@st.cache_resource
def get_openai_client():
    """Initialize OpenAI client for Pollinations API"""
    return OpenAI(
        api_key="pollinations",
        base_url="https://text.pollinations.ai/openai",
    )

# ============== SESSION STATE INITIALIZATION ==============
def init_session_state():
    defaults = {
        'page': 'home',
        'study_mode': None,
        'quiz_type': 'multiple_choice',
        'current_topic': None,
        # Quiz states
        'quiz_data': None,
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
        # Debug
        'debug_mode': False,
        'last_api_error': None,
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
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        .stApp { 
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0f0f1a 100%);
            font-family: 'Space Grotesk', sans-serif;
        }
        .main-header { 
            text-align: center; 
            color: #ffffff !important; 
            padding: 20px;
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle { 
            text-align: center; 
            color: #94a3b8 !important; 
            font-size: 1.1rem; 
            margin-bottom: 2rem;
            letter-spacing: 0.5px;
        }
        .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
        p, span, div, label { color: #e2e8f0 !important; }
        
        [data-testid="stSidebar"] { 
            background: linear-gradient(180deg, #1e1e2e 0%, #2d2d44 100%);
            border-right: 1px solid rgba(99, 102, 241, 0.2);
        }
        [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
        
        .mode-card {
            background: linear-gradient(135deg, rgba(30, 30, 46, 0.8) 0%, rgba(45, 45, 68, 0.8) 100%);
            backdrop-filter: blur(10px);
            border-radius: 20px; 
            padding: 30px; 
            text-align: center;
            border: 1px solid rgba(99, 102, 241, 0.3);
            min-height: 200px;
            display: flex; 
            flex-direction: column; 
            justify-content: center; 
            align-items: center;
            margin-bottom: 10px; 
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        .mode-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
            opacity: 0;
            transition: opacity 0.4s ease;
        }
        .mode-card:hover {
            border-color: #6366f1;
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.3);
        }
        .mode-card:hover::before { opacity: 1; }
        .mode-icon { font-size: 48px; margin-bottom: 15px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3)); }
        .mode-title { font-size: 1.3rem; font-weight: 600; color: #ffffff !important; margin-bottom: 10px; }
        .mode-description { font-size: 0.9rem; color: #94a3b8 !important; line-height: 1.5; }
        
        .flashcard {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
            border-radius: 16px; 
            padding: 30px; 
            min-height: 180px;
            display: flex; 
            flex-direction: column; 
            justify-content: center; 
            align-items: center;
            text-align: center; 
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(61, 122, 181, 0.5);
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }
        .flashcard:hover { transform: scale(1.02); }
        .flashcard-back {
            background: linear-gradient(135deg, #1a4731 0%, #2d7a4f 100%);
            border-color: rgba(61, 181, 106, 0.5);
        }
        .flashcard-label { 
            font-size: 0.7rem; 
            text-transform: uppercase; 
            letter-spacing: 3px; 
            margin-bottom: 15px; 
            opacity: 0.7;
            color: #a0c4e8 !important;
            font-weight: 500;
        }
        .flashcard-content { 
            font-size: 1.2rem; 
            font-weight: 500; 
            color: #ffffff !important; 
            line-height: 1.6;
        }
        
        .quiz-question {
            background: linear-gradient(135deg, rgba(45, 45, 68, 0.9) 0%, rgba(61, 61, 92, 0.9) 100%);
            border-radius: 16px; 
            padding: 25px; 
            margin: 20px 0;
            border-left: 4px solid #6366f1;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }
        .quiz-question h4 { color: #ffffff !important; margin-bottom: 15px; font-weight: 600; }
        .correct-answer { 
            background: linear-gradient(135deg, rgba(26, 71, 49, 0.9) 0%, rgba(45, 122, 79, 0.9) 100%) !important;
            border-left-color: #22c55e !important;
        }
        .incorrect-answer { 
            background: linear-gradient(135deg, rgba(74, 26, 26, 0.9) 0%, rgba(122, 45, 45, 0.9) 100%) !important;
            border-left-color: #ef4444 !important;
        }
        
        .results-box {
            background: linear-gradient(135deg, rgba(30, 30, 46, 0.95) 0%, rgba(45, 45, 68, 0.95) 100%);
            border-radius: 20px; 
            padding: 40px; 
            text-align: center; 
            margin: 30px 0;
            border: 2px solid #6366f1;
            box-shadow: 0 10px 40px rgba(99, 102, 241, 0.3);
        }
        .score-display { 
            font-size: 4rem; 
            font-weight: 700;
            background: linear-gradient(135deg, #6366f1, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 15px 0;
        }
        
        .stat-card { 
            background: linear-gradient(135deg, rgba(30, 30, 46, 0.8) 0%, rgba(45, 45, 68, 0.8) 100%);
            border-radius: 16px; 
            padding: 25px; 
            text-align: center;
            border: 1px solid rgba(99, 102, 241, 0.2);
            transition: all 0.3s ease;
        }
        .stat-card:hover { border-color: rgba(99, 102, 241, 0.5); }
        .stat-card h3 { color: #ffffff !important; font-size: 1.1rem; margin-bottom: 5px; }
        .stat-card p { color: #94a3b8 !important; font-size: 0.9rem; }
        
        .timer-display { 
            font-size: 2.5rem; 
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: #ef4444 !important; 
            text-align: center; 
            padding: 15px;
            background: rgba(239, 68, 68, 0.1);
            border-radius: 12px;
            margin: 15px 0;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        .hint-box { 
            background: linear-gradient(135deg, rgba(61, 61, 0, 0.8) 0%, rgba(90, 90, 0, 0.8) 100%);
            border-radius: 12px; 
            padding: 20px; 
            margin: 15px 0;
            border-left: 4px solid #fbbf24;
        }
        .explanation-box { 
            background: linear-gradient(135deg, rgba(26, 58, 74, 0.8) 0%, rgba(45, 90, 106, 0.8) 100%);
            border-radius: 12px; 
            padding: 20px; 
            margin: 15px 0;
            border-left: 4px solid #38bdf8;
        }
        
        .achievement { 
            background: linear-gradient(135deg, rgba(74, 63, 0, 0.9) 0%, rgba(107, 90, 0, 0.9) 100%);
            border-radius: 12px; 
            padding: 15px 20px; 
            margin: 8px;
            display: inline-block;
            border: 1px solid #fbbf24;
            transition: all 0.3s ease;
        }
        .achievement:hover { transform: scale(1.05); }
        
        .footer { text-align: center; color: #64748b !important; padding: 30px; }
        .footer p { color: #64748b !important; }
        
        .stButton > button { 
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white !important;
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            font-weight: 600;
            font-family: 'Space Grotesk', sans-serif;
            transition: all 0.3s ease;
        }
        .stButton > button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
        }
        
        .chat-message { 
            padding: 18px; 
            border-radius: 12px; 
            margin: 12px 0;
            line-height: 1.6;
        }
        .chat-user { 
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
            margin-left: 15%;
        }
        .chat-ai { 
            background: linear-gradient(135deg, #2d2d44 0%, #3d3d5c 100%);
            margin-right: 15%;
        }
        
        .debug-box {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
        }
        </style>
        """
    else:
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        .stApp { 
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            font-family: 'Space Grotesk', sans-serif;
        }
        .main-header { 
            text-align: center; 
            padding: 20px;
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, #4f46e5, #7c3aed, #db2777);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle { text-align: center; color: #64748b !important; font-size: 1.1rem; margin-bottom: 2rem; }
        .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span, p, span, div, label { color: #1e293b !important; }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%); }
        [data-testid="stSidebar"] * { color: #1e293b !important; }
        .mode-card { 
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 20px; 
            padding: 30px; 
            text-align: center;
            border: 1px solid #e2e8f0;
            min-height: 200px; 
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }
        .mode-card:hover { border-color: #6366f1; box-shadow: 0 10px 30px rgba(99, 102, 241, 0.15); }
        .mode-title { color: #1e293b !important; }
        .mode-description { color: #64748b !important; }
        .flashcard { background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-color: #3b82f6; }
        .flashcard-back { background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border-color: #22c55e; }
        .flashcard-label { color: #1d4ed8 !important; }
        .flashcard-content { color: #1e293b !important; }
        .quiz-question { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); }
        .quiz-question h4 { color: #1e293b !important; }
        .results-box { background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); border-color: #6366f1; }
        .stat-card { background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); border-color: #e2e8f0; }
        .stat-card h3 { color: #1e293b !important; }
        .footer p { color: #64748b !important; }
        </style>
        """

st.markdown(get_theme_css(), unsafe_allow_html=True)

# ============== AI API FUNCTIONS ==============
def call_ai_json(prompt, system_msg, max_retries=2):
    """Call AI API and expect JSON response"""
    client = get_openai_client()
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="openai",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            
            content = response.choices[0].message.content.strip()
            
            if st.session_state.debug_mode:
                st.markdown(f"<div class='debug-box'><strong>Raw API Response:</strong><br>{content[:500]}...</div>", unsafe_allow_html=True)
            
            # Clean up common JSON formatting issues
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON
            data = json.loads(content)
            return data
            
        except json.JSONDecodeError as e:
            st.session_state.last_api_error = f"JSON Parse Error: {str(e)}"
            if st.session_state.debug_mode:
                st.error(f"JSON Parse Error (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return None
            
        except Exception as e:
            st.session_state.last_api_error = f"API Error: {str(e)}"
            if st.session_state.debug_mode:
                st.error(f"API Error (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return None
    
    return None

def call_ai_text(prompt, system_msg="You are a helpful educational assistant."):
    """Call AI API and expect text response"""
    client = get_openai_client()
    
    try:
        response = client.chat.completions.create(
            model="openai",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        content = response.choices[0].message.content.strip()
        return content
        
    except Exception as e:
        st.session_state.last_api_error = f"API Error: {str(e)}"
        if st.session_state.debug_mode:
            st.error(f"API Error: {str(e)}")
        return None

# ============== QUIZ GENERATION FUNCTIONS ==============
def generate_multiple_choice_quiz(topic, num_questions, difficulty, subject_context):
    """Generate multiple choice quiz with structured JSON"""
    system_msg = """You are a quiz generator. Output ONLY a valid JSON object with no additional text.
Format:
{
    "questions": [
        {
            "question": "Question text here",
            "options": {
                "A": "First option",
                "B": "Second option", 
                "C": "Third option",
                "D": "Fourth option"
            },
            "correct": "A"
        }
    ]
}
Ensure all questions are educational and appropriate. The "correct" field must be A, B, C, or D."""

    prompt = f"""Create a {difficulty} difficulty quiz about "{topic}" {subject_context} with exactly {num_questions} multiple choice questions.
Each question should have 4 options (A, B, C, D) with one correct answer.
Make questions educational and engaging."""

    data = call_ai_json(prompt, system_msg)
    
    if data and "questions" in data:
        return data["questions"]
    return None

def generate_true_false_quiz(topic, num_questions, difficulty, subject_context):
    """Generate true/false quiz with structured JSON"""
    system_msg = """You are a quiz generator. Output ONLY a valid JSON object with no additional text.
Format:
{
    "questions": [
        {
            "statement": "A statement that is either true or false",
            "answer": true
        }
    ]
}
The "answer" field must be a boolean (true or false, not strings)."""

    prompt = f"""Create a {difficulty} difficulty true/false quiz about "{topic}" {subject_context} with exactly {num_questions} statements.
Mix true and false statements roughly equally.
Make statements clear and educational."""

    data = call_ai_json(prompt, system_msg)
    
    if data and "questions" in data:
        return data["questions"]
    return None

def generate_fill_blank_quiz(topic, num_questions, difficulty, subject_context):
    """Generate fill-in-the-blank quiz with structured JSON"""
    system_msg = """You are a quiz generator. Output ONLY a valid JSON object with no additional text.
Format:
{
    "questions": [
        {
            "sentence": "The process of _____ converts sunlight into energy.",
            "answer": "photosynthesis"
        }
    ]
}
Use _____ (5 underscores) to mark the blank. Keep answers to 1-3 words."""

    prompt = f"""Create a {difficulty} difficulty fill-in-the-blank quiz about "{topic}" {subject_context} with exactly {num_questions} sentences.
Each sentence should have exactly one blank marked with _____.
Keep answers concise (1-3 words)."""

    data = call_ai_json(prompt, system_msg)
    
    if data and "questions" in data:
        return data["questions"]
    return None

def generate_flashcards(topic, num_cards, subject_context):
    """Generate flashcards with structured JSON"""
    system_msg = """You are a flashcard generator. Output ONLY a valid JSON object with no additional text.
Format:
{
    "flashcards": [
        {
            "front": "Term or question",
            "back": "Definition or answer"
        }
    ]
}
Make flashcards educational and concise."""

    prompt = f"""Create {num_cards} educational flashcards about "{topic}" {subject_context}.
Include a mix of:
- Key terms and definitions
- Important concepts
- Facts to remember
Keep the back side concise but informative."""

    data = call_ai_json(prompt, system_msg)
    
    if data and "flashcards" in data:
        return data["flashcards"]
    return None

def generate_study_guide(topic, subject_context):
    """Generate comprehensive study guide as text"""
    system_msg = """You are an educational content creator. Create comprehensive, well-organized study guides.
Use clear headings, bullet points, and organized sections.
Make content engaging and easy to understand."""

    prompt = f"""Create a comprehensive study guide about "{topic}" {subject_context}.

Include these sections:
1. **Overview** - A brief 2-3 sentence introduction
2. **Key Concepts** - 5 main ideas with clear explanations
3. **Important Terms** - Definitions of key vocabulary
4. **Common Misconceptions** - What people often get wrong
5. **Study Tips** - How to effectively learn this material
6. **Related Topics** - What to explore next

Make it engaging and suitable for students."""

    return call_ai_text(prompt, system_msg)

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

def reset_study_data():
    keys_to_reset = ['quiz_data', 'user_answers', 'quiz_submitted', 'tf_data', 
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
    
    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Settings")
        theme = st.selectbox("🎨 Theme", ["Dark", "Light"], index=0 if st.session_state.theme == 'dark' else 1)
        if theme.lower() != st.session_state.theme:
            st.session_state.theme = theme.lower()
            st.rerun()
        
        st.session_state.subject = st.selectbox("📚 Subject", ["General", "Math", "Science", "History", "Language", "Computer Science", "Art", "Music"])
        st.session_state.grade_level = st.selectbox("🎓 Grade Level", ["Elementary", "Middle School", "High School", "College", "Professional"])
        
        st.markdown("---")
        st.session_state.debug_mode = st.checkbox("🐛 Debug Mode", value=st.session_state.debug_mode)
        
        if st.session_state.last_api_error:
            st.error(f"Last Error: {st.session_state.last_api_error}")
        
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
        
        st.markdown("---")
        st.session_state.debug_mode = st.checkbox("🐛 Debug Mode", value=st.session_state.debug_mode)
        
        # API Test button
        if st.button("🧪 Test API Connection"):
            with st.spinner("Testing..."):
                test_result = call_ai_text("Say 'API connection successful!' in exactly those words.")
                if test_result:
                    st.success(f"✅ {test_result[:100]}")
                else:
                    st.error("❌ API connection failed")
    
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
            
            subject_context = f"for {st.session_state.grade_level} level {st.session_state.subject}" if st.session_state.subject != "General" else f"for {st.session_state.grade_level} students"
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Generate Quiz
            if study_mode in ["Quiz", "All Three"]:
                quiz_type = st.session_state.quiz_type
                status_text.text(f"Generating {quiz_type} quiz...")
                
                if quiz_type == "Multiple Choice":
                    result = generate_multiple_choice_quiz(topic, num_questions, difficulty, subject_context)
                    if result:
                        st.session_state.quiz_data = result
                        progress_bar.progress(33)
                    else:
                        st.error("Failed to generate multiple choice quiz. Please try again.")
                
                elif quiz_type == "True/False":
                    result = generate_true_false_quiz(topic, num_questions, difficulty, subject_context)
                    if result:
                        st.session_state.tf_data = result
                        progress_bar.progress(33)
                    else:
                        st.error("Failed to generate true/false quiz. Please try again.")
                
                elif quiz_type == "Fill in the Blank":
                    result = generate_fill_blank_quiz(topic, num_questions, difficulty, subject_context)
                    if result:
                        st.session_state.fib_data = result
                        progress_bar.progress(33)
                    else:
                        st.error("Failed to generate fill-in-the-blank quiz. Please try again.")
                
                if st.session_state.timed_mode:
                    st.session_state.timer_start = time.time()
            
            # Generate Flashcards
            if study_mode in ["Flashcards", "All Three"]:
                status_text.text("Generating flashcards...")
                cards = generate_flashcards(topic, num_flashcards, subject_context)
                if cards:
                    st.session_state.flashcards_data = cards
                    if flashcard_mode == "Matching Game" and cards:
                        random.shuffle(cards)
                        st.session_state.matching_pairs = cards[:min(6, len(cards))]
                    progress_bar.progress(66)
                else:
                    st.error("Failed to generate flashcards. Please try again.")
            
            # Generate Study Guide
            if study_mode in ["Study Guide", "All Three"]:
                status_text.text("Generating study guide...")
                guide = generate_study_guide(topic, subject_context)
                if guide:
                    st.session_state.study_guide_data = guide
                    progress_bar.progress(100)
                else:
                    st.error("Failed to generate study guide. Please try again.")
            
            progress_bar.progress(100)
            status_text.text("✅ Study materials generated!")
            
            # Check if anything was generated
            has_content = (st.session_state.quiz_data or st.session_state.tf_data or 
                          st.session_state.fib_data or st.session_state.flashcards_data or 
                          st.session_state.study_guide_data)
            
            if has_content:
                st.balloons()
                new_achs = check_achievements()
                for ach in new_achs:
                    st.toast(f"🏆 Achievement Unlocked: {ACHIEVEMENTS[ach]['name']}")
                st.rerun()
            else:
                st.error("No content was generated. Please check your internet connection and try again.")
    
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
                        hint = call_ai_text(f"Give a brief hint (1 sentence) for this question without revealing the answer: {q['question']}")
                        st.session_state.show_hints[i] = hint or "Think about the key concepts related to this topic."
                    st.rerun()
                
                if i in st.session_state.show_hints:
                    st.markdown(f"<div class='hint-box'>💡 {st.session_state.show_hints[i]}</div>", unsafe_allow_html=True)
                
                # Handle both dict and list formats for options
                if isinstance(q['options'], dict):
                    options = [f"{letter}) {text}" for letter, text in sorted(q['options'].items())]
                else:
                    options = [f"{chr(65+j)}) {opt}" for j, opt in enumerate(q['options'])]
                
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
                correct = q['correct']
                is_correct = user_answer == correct
                if is_correct:
                    correct_count += 1
                
                status = "correct-answer" if is_correct else "incorrect-answer"
                icon = "✅" if is_correct else "❌"
                st.markdown(f"<div class='quiz-question {status}'><h4>{icon} Q{i+1}: {q['question']}</h4></div>", unsafe_allow_html=True)
                
                # Handle both dict and list formats
                if isinstance(q['options'], dict):
                    for letter, text in sorted(q['options'].items()):
                        if letter == correct:
                            st.markdown(f"✅ **{letter}) {text}** *(Correct)*")
                        elif letter == user_answer and not is_correct:
                            st.markdown(f"❌ ~~{letter}) {text}~~ *(Your Answer)*")
                        else:
                            st.markdown(f"{letter}) {text}")
                else:
                    for j, opt in enumerate(q['options']):
                        letter = chr(65 + j)
                        if letter == correct:
                            st.markdown(f"✅ **{letter}) {opt}** *(Correct)*")
                        elif letter == user_answer and not is_correct:
                            st.markdown(f"❌ ~~{letter}) {opt}~~ *(Your Answer)*")
                        else:
                            st.markdown(f"{letter}) {opt}")
                
                # Explain wrong answer
                if not is_correct:
                    if st.button(f"🤔 Explain Why", key=f"explain_{i}"):
                        if i not in st.session_state.explanations:
                            if isinstance(q['options'], dict):
                                correct_text = q['options'].get(correct, correct)
                                user_text = q['options'].get(user_answer, 'not answered')
                            else:
                                correct_idx = ord(correct) - 65
                                correct_text = q['options'][correct_idx] if correct_idx < len(q['options']) else correct
                                user_idx = ord(user_answer) - 65 if user_answer else -1
                                user_text = q['options'][user_idx] if 0 <= user_idx < len(q['options']) else 'not answered'
                            
                            exp = call_ai_text(f"Explain why the answer to '{q['question']}' is '{correct_text}' and not '{user_text}'. Keep it brief (2-3 sentences).")
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
                st.markdown(f"<div class='quiz-question'><h4>Q{i+1}: {q['statement']}</h4></div>", unsafe_allow_html=True)
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
                st.markdown(f"<div class='quiz-question {status}'><h4>{icon} {q['statement']}</h4><p>Correct Answer: {q['answer']}</p></div>", unsafe_allow_html=True)
            
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
                st.markdown(f"**{i+1}. {q['sentence']}**")
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
                st.markdown(f"{icon} **{q['sentence']}**")
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
                
                response = call_ai_text(
                    f"The user is studying {st.session_state.current_topic}. Answer their question: {user_question}",
                    "You are a helpful educational tutor. Give clear, concise answers to help students understand concepts."
                )
                if response:
                    st.session_state.chat_messages.append({'role': 'ai', 'content': response})
                
                st.rerun()
    
    # ============== RELATED TOPICS ==============
    if st.session_state.current_topic and (st.session_state.quiz_data or st.session_state.study_guide_data or st.session_state.flashcards_data or st.session_state.tf_data or st.session_state.fib_data):
        st.markdown("---")
        st.markdown("### 🔗 Related Topics to Explore")
        if st.button("Get Suggestions"):
            related = call_ai_text(f"List 5 related topics to {st.session_state.current_topic} that a student might want to study next. Just list the topics, one per line.")
            if related:
                st.markdown(related)
    
    # Footer
    st.markdown("---")
    st.markdown("<div class='footer'><p>Made with ❤️ for students everywhere | Powered by Pollinations.AI 🌸</p></div>", unsafe_allow_html=True)
