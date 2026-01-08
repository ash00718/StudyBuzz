import streamlit as st
import requests
import re
import random
from datetime import datetime

# Page config
st.set_page_config(page_title="StudyBuzz", page_icon="📚", layout="wide")

# Session state
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None
if 'flashcards_data' not in st.session_state:
    st.session_state.flashcards_data = None
if 'study_guide_data' not in st.session_state:
    st.session_state.study_guide_data = None
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False
if 'flipped_cards' not in st.session_state:
    st.session_state.flipped_cards = set()
if 'debug_log' not in st.session_state:
    st.session_state.debug_log = []

# CSS
st.markdown("""
<style>
.stApp { background-color: #0e1117; }
.main-header { text-align: center; color: #ffffff !important; padding: 20px; }
p, span, div, label, h1, h2, h3, h4 { color: #ffffff !important; }
[data-testid="stSidebar"] { background-color: #1a1a2e; }
[data-testid="stSidebar"] * { color: #ffffff !important; }
.flashcard {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
    border-radius: 15px; padding: 25px; min-height: 120px;
    text-align: center; margin: 10px 0; border: 1px solid #3d7ab5;
}
.flashcard-back {
    background: linear-gradient(135deg, #1a4731 0%, #2d7a4f 100%);
    border-color: #3db56a;
}
.quiz-box {
    background: linear-gradient(135deg, #2d2d44 0%, #3d3d5c 100%);
    border-radius: 12px; padding: 20px; margin: 15px 0;
    border-left: 4px solid #6366f1;
}
.debug-box {
    background: #1a1a1a; border: 1px solid #333; padding: 10px;
    border-radius: 5px; font-family: monospace; font-size: 12px;
    max-height: 200px; overflow-y: auto; color: #00ff00 !important;
}
</style>
""", unsafe_allow_html=True)

def log_debug(msg):
    st.session_state.debug_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    if len(st.session_state.debug_log) > 20:
        st.session_state.debug_log = st.session_state.debug_log[-20:]

def call_ai(prompt):
    """Call Pollinations AI API with fast models and fallbacks"""
    import time
    
    # Priority: openai-fast -> gemini-fast -> mistral -> openai
    models = ["openai-fast", "gemini-fast", "mistral", "openai"]
    
    for i, model in enumerate(models):
        log_debug(f"Trying model: {model}")
        
        # Add delay between retries to avoid rate limits
        if i > 0:
            time.sleep(2)
        
        try:
            # Using the newer gen.pollinations.ai endpoint
            response = requests.post(
                "https://gen.pollinations.ai/openai/chat/completions",
                json={
                    "messages": [
                        {"role": "system", "content": "You are a helpful study assistant. Follow the exact format requested. Be concise but thorough."},
                        {"role": "user", "content": prompt}
                    ],
                    "model": model
                },
                headers={
                    "Content-Type": "application/json"
                },
                timeout=60
            )
            
            log_debug(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    # New endpoint returns JSON in OpenAI format
                    data = response.json()
                    text = data["choices"][0]["message"]["content"].strip()
                except:
                    # Fallback to raw text
                    text = response.text.strip()
                
                if text and len(text) > 50:
                    log_debug(f"Success with {model}! {len(text)} chars")
                    return text
                else:
                    log_debug(f"Empty response from {model}, trying next...")
                    continue
            elif response.status_code == 429:
                log_debug(f"Rate limited on {model}, waiting 5s...")
                time.sleep(5)
                continue
            else:
                log_debug(f"Error {response.status_code} from {model}, trying next...")
                continue
                    
        except requests.exceptions.Timeout:
            log_debug(f"Timeout with {model}, trying next...")
            continue
        except Exception as e:
            log_debug(f"Error with {model}: {str(e)}")
            continue
    
    log_debug("All models failed! You may be rate limited. Wait a minute and try again.")
    return None

def parse_quiz(text):
    """Parse quiz text into questions"""
    questions = []
    parts = re.split(r'Q\d+[:\.]?\s*', text)
    
    for part in parts[1:]:
        if not part.strip():
            continue
        lines = part.strip().split('\n')
        question = ""
        options = {}
        correct = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if 'correct' in line.lower() and 'answer' in line.lower():
                match = re.search(r'([A-D])', line, re.IGNORECASE)
                if match:
                    correct = match.group(1).upper()
            elif re.match(r'^[A-D][\)\.\:]', line, re.IGNORECASE):
                letter = line[0].upper()
                options[letter] = line[2:].strip()
            elif not options:
                question += line + " "
        
        if question and options and correct:
            questions.append({"question": question.strip(), "options": options, "correct": correct})
    
    return questions

def parse_flashcards(text):
    """Parse flashcards text"""
    cards = []
    parts = re.split(r'CARD\s*\d*', text, flags=re.IGNORECASE)
    
    for part in parts:
        front = re.search(r'Front:\s*(.+?)(?=Back:|$)', part, re.DOTALL | re.IGNORECASE)
        back = re.search(r'Back:\s*(.+?)(?=CARD|$)', part, re.DOTALL | re.IGNORECASE)
        if front and back:
            f = front.group(1).strip()
            b = back.group(1).strip()
            if f and b:
                cards.append({"front": f, "back": b})
    return cards

# Header
st.markdown("<h1 class='main-header'>📚 StudyBuzz</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888;'>AI-Powered Study Materials Generator</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    study_mode = st.selectbox("Study Mode", ["Quiz", "Flashcards", "Study Guide", "All Three"])
    difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"])
    num_questions = st.slider("Questions", 3, 10, 5)
    num_flashcards = st.slider("Flashcards", 3, 15, 8)
    
    st.markdown("---")
    show_debug = st.checkbox("Show Debug Log")
    
    st.markdown("---")
    st.markdown("⚠️ **Note:** Free API has rate limits. If generation fails, wait 1-2 minutes.")
    
    if st.button("🗑️ Clear All"):
        st.session_state.quiz_data = None
        st.session_state.flashcards_data = None
        st.session_state.study_guide_data = None
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.flipped_cards = set()
        st.session_state.debug_log = []
        st.rerun()

# Debug log display
if show_debug and st.session_state.debug_log:
    st.markdown("### 🔧 Debug Log")
    st.markdown(f"<div class='debug-box'>{'<br>'.join(st.session_state.debug_log)}</div>", unsafe_allow_html=True)

# Main input
topic = st.text_input("📖 Enter a topic to study:", placeholder="e.g., Photosynthesis, World War 2")

col1, col2 = st.columns([1, 4])
with col1:
    generate_btn = st.button("🚀 Generate", type="primary")

if generate_btn:
    if not topic:
        st.warning("Please enter a topic!")
    else:
        # Clear previous data
        st.session_state.quiz_data = None
        st.session_state.flashcards_data = None
        st.session_state.study_guide_data = None
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.flipped_cards = set()
        
        log_debug(f"Starting generation for: {topic}")
        
        # Generate Quiz
        if study_mode in ["Quiz", "All Three"]:
            with st.spinner("📝 Generating quiz..."):
                prompt = f"""Create a {difficulty} difficulty quiz about {topic} with {num_questions} multiple choice questions.

Format each question exactly like this:
Q1: [Question text]
A) [Option]
B) [Option]
C) [Option]
D) [Option]
Correct Answer: [A, B, C, or D]

Generate all {num_questions} questions now."""
                
                result = call_ai(prompt)
                if result:
                    log_debug("Quiz response received, parsing...")
                    parsed = parse_quiz(result)
                    log_debug(f"Parsed {len(parsed)} questions")
                    if parsed:
                        st.session_state.quiz_data = parsed
                        st.success(f"✅ Generated {len(parsed)} quiz questions!")
                    else:
                        st.error("Could not parse quiz. Raw response:")
                        st.code(result[:500])
                else:
                    st.error("❌ Failed to generate quiz. You may be rate limited. Wait 1-2 minutes and try again.")
        
        # Generate Flashcards
        if study_mode in ["Flashcards", "All Three"]:
            with st.spinner("🎴 Generating flashcards..."):
                prompt = f"""Create {num_flashcards} flashcards about {topic}.

Format each card exactly like this:
CARD 1
Front: [Term or question]
Back: [Definition or answer]

CARD 2
Front: [Term or question]
Back: [Definition or answer]

Generate all {num_flashcards} flashcards now."""
                
                result = call_ai(prompt)
                if result:
                    log_debug("Flashcards response received, parsing...")
                    parsed = parse_flashcards(result)
                    log_debug(f"Parsed {len(parsed)} flashcards")
                    if parsed:
                        st.session_state.flashcards_data = parsed
                        st.success(f"✅ Generated {len(parsed)} flashcards!")
                    else:
                        st.error("Could not parse flashcards. Raw response:")
                        st.code(result[:500])
                else:
                    st.error("❌ Failed to generate flashcards. You may be rate limited. Wait 1-2 minutes and try again.")
        
        # Generate Study Guide
        if study_mode in ["Study Guide", "All Three"]:
            with st.spinner("📖 Generating study guide..."):
                prompt = f"""Create a comprehensive study guide about {topic}.

Include:
1. Overview (2-3 sentences)
2. Key Concepts (5 main points with explanations)
3. Important Terms and Definitions
4. Study Tips

Make it clear and helpful for students."""
                
                result = call_ai(prompt)
                if result:
                    log_debug("Study guide received")
                    st.session_state.study_guide_data = result
                    st.success("✅ Generated study guide!")
                else:
                    st.error("❌ Failed to generate study guide. You may be rate limited. Wait 1-2 minutes and try again.")

# Display Quiz
if st.session_state.quiz_data:
    st.markdown("---")
    st.markdown("## 📝 Quiz")
    
    questions = st.session_state.quiz_data
    
    if not st.session_state.quiz_submitted:
        for i, q in enumerate(questions):
            st.markdown(f"<div class='quiz-box'><strong>Q{i+1}:</strong> {q['question']}</div>", unsafe_allow_html=True)
            options = [f"{k}) {v}" for k, v in sorted(q['options'].items())]
            answer = st.radio(f"Answer {i+1}:", options, key=f"q_{i}", index=None, label_visibility="collapsed")
            if answer:
                st.session_state.user_answers[i] = answer[0]
        
        if st.button("📊 Submit Quiz"):
            if len(st.session_state.user_answers) < len(questions):
                st.warning("Please answer all questions first!")
            else:
                st.session_state.quiz_submitted = True
                st.rerun()
    else:
        correct = 0
        for i, q in enumerate(questions):
            user_ans = st.session_state.user_answers.get(i, "")
            is_correct = user_ans == q['correct']
            if is_correct:
                correct += 1
            icon = "✅" if is_correct else "❌"
            st.markdown(f"{icon} **Q{i+1}:** {q['question']}")
            st.markdown(f"Your answer: **{user_ans}** | Correct: **{q['correct']}**")
        
        score = (correct / len(questions)) * 100
        st.markdown(f"### Score: {correct}/{len(questions)} ({score:.0f}%)")
        
        if st.button("🔄 Retake Quiz"):
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.rerun()

# Display Flashcards
if st.session_state.flashcards_data:
    st.markdown("---")
    st.markdown("## 🎴 Flashcards")
    
    cards = st.session_state.flashcards_data
    flipped = len(st.session_state.flipped_cards)
    st.progress(flipped / len(cards))
    st.markdown(f"**{flipped}/{len(cards)} cards flipped**")
    
    if st.button("🔄 Reset Cards"):
        st.session_state.flipped_cards = set()
        st.rerun()
    
    cols = st.columns(2)
    for i, card in enumerate(cards):
        with cols[i % 2]:
            is_flipped = i in st.session_state.flipped_cards
            if is_flipped:
                st.markdown(f"<div class='flashcard flashcard-back'><small>ANSWER</small><br><br>{card['back']}</div>", unsafe_allow_html=True)
                if st.button("↩️ Flip Back", key=f"unflip_{i}"):
                    st.session_state.flipped_cards.discard(i)
                    st.rerun()
            else:
                st.markdown(f"<div class='flashcard'><small>QUESTION</small><br><br>{card['front']}</div>", unsafe_allow_html=True)
                if st.button("🔄 Flip", key=f"flip_{i}"):
                    st.session_state.flipped_cards.add(i)
                    st.rerun()

# Display Study Guide
if st.session_state.study_guide_data:
    st.markdown("---")
    st.markdown("## 📖 Study Guide")
    st.markdown(st.session_state.study_guide_data)

# Footer
st.markdown("---")
st.markdown("<p style='text-align:center; color:#666;'>Powered by Pollinations.AI 🌸</p>", unsafe_allow_html=True)
