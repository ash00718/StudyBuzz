import streamlit as st
import requests
import json
import re
from datetime import datetime

# Initialize session state
if 'flipped_cards' not in st.session_state:
    st.session_state.flipped_cards = set()
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None
if 'quiz_raw' not in st.session_state:
    st.session_state.quiz_raw = None
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False
if 'flashcards_data' not in st.session_state:
    st.session_state.flashcards_data = None

# Page config
st.set_page_config(
    page_title="AI Study Buddy",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for better UI with white text and flip cards
st.markdown("""
    <style>
    /* Dark theme with white text */
    .stApp {
        background-color: #0e1117;
    }
    
    .main-header {
        text-align: center;
        color: #ffffff !important;
        padding: 20px;
    }
    
    .subtitle {
        text-align: center;
        color: #b0b0b0 !important;
    }
    
    /* Ensure all text is white/light */
    .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
    p, span, div, label {
        color: #ffffff !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #1a1a2e;
    }
    
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Flashcard styles */
    .flashcard-container {
        perspective: 1000px;
        margin: 10px 0;
    }
    
    .flashcard {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        border-radius: 15px;
        padding: 25px;
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        border: 1px solid #3d7ab5;
        transition: all 0.3s ease;
    }
    
    .flashcard:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
    }
    
    .flashcard-front {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
    }
    
    .flashcard-back {
        background: linear-gradient(135deg, #1a4731 0%, #2d7a4f 100%);
        border-color: #3db56a;
    }
    
    .flashcard-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 10px;
        opacity: 0.8;
        color: #a0c4e8 !important;
    }
    
    .flashcard-back .flashcard-label {
        color: #a0e8c4 !important;
    }
    
    .flashcard-content {
        font-size: 18px;
        font-weight: 500;
        color: #ffffff !important;
        line-height: 1.5;
    }
    
    .flashcard-number {
        position: absolute;
        top: 10px;
        left: 15px;
        font-size: 14px;
        opacity: 0.6;
        color: #ffffff !important;
    }
    
    /* Quiz styles */
    .quiz-question {
        background: linear-gradient(135deg, #2d2d44 0%, #3d3d5c 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        border-left: 4px solid #6366f1;
    }
    
    .quiz-question h4 {
        color: #ffffff !important;
        margin-bottom: 15px;
    }
    
    .correct-answer {
        background: linear-gradient(135deg, #1a4731 0%, #2d7a4f 100%) !important;
        border-left-color: #22c55e !important;
    }
    
    .incorrect-answer {
        background: linear-gradient(135deg, #4a1a1a 0%, #7a2d2d 100%) !important;
        border-left-color: #ef4444 !important;
    }
    
    /* Results box */
    .results-box {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
        border: 2px solid #6366f1;
    }
    
    .score-display {
        font-size: 48px;
        font-weight: bold;
        color: #6366f1 !important;
        margin: 10px 0;
    }
    
    /* Progress bar */
    .progress-container {
        background: #2d2d44;
        border-radius: 10px;
        padding: 3px;
        margin: 10px 0;
    }
    
    .progress-bar {
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        border-radius: 8px;
        height: 20px;
        transition: width 0.3s ease;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #888888 !important;
        padding: 20px;
    }
    
    .footer p {
        color: #888888 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }
    
    /* Radio button styling */
    .stRadio > div {
        background: transparent;
    }
    
    .stRadio label {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("<h1 class='main-header'>📚 AI Study Buddy</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Generate quizzes, flashcards, and study guides for any topic!</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    study_mode = st.selectbox(
        "Study Mode",
        ["Quiz", "Flashcards", "Study Guide", "All Three"]
    )
    
    if study_mode in ["Quiz", "All Three"]:
        difficulty = st.select_slider(
            "Quiz Difficulty",
            options=["Easy", "Medium", "Hard"]
        )
        num_questions = st.slider("Number of Questions", 3, 10, 5)
    else:
        difficulty = "Medium"
        num_questions = 5
    
    if study_mode in ["Flashcards", "All Three"]:
        num_flashcards = st.slider("Number of Flashcards", 5, 20, 10)
    else:
        num_flashcards = 10
    
    generate_diagram = st.checkbox("Generate Study Diagram", value=True)
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("Powered by **Pollinations.AI** 🌸")
    st.markdown("Built to help students study smarter!")

def parse_quiz(quiz_text):
    """Parse quiz text into structured format"""
    questions = []
    
    # Split by question patterns
    q_pattern = r'Q\d+[:\.]?\s*'
    parts = re.split(q_pattern, quiz_text)
    
    for part in parts[1:]:  # Skip first empty part
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
            
            # Check for correct answer FIRST (before options check)
            if 'correct' in line.lower() and 'answer' in line.lower():
                answer_match = re.search(r'[:\s]+([A-D])\b', line, re.IGNORECASE)
                if answer_match:
                    correct_answer = answer_match.group(1).upper()
                continue
            
            # Check for options (A), A., A:, or A) format
            option_match = re.match(r'^\(?([A-D])\)?[\.\):]?\s*(.+)', line, re.IGNORECASE)
            if option_match:
                letter = option_match.group(1).upper()
                text = option_match.group(2).strip()
                options[letter] = text
            # Otherwise it's the question
            elif not options:
                question_text += line + " "
        
        if question_text and len(options) >= 2 and correct_answer:
            questions.append({
                'question': question_text.strip(),
                'options': options,
                'correct': correct_answer
            })
    
    return questions

def parse_flashcards(flashcards_text):
    """Parse flashcards text into structured format"""
    cards = []
    
    # Split by CARD patterns
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

# Main content
topic = st.text_input("📖 Enter a topic to study:", placeholder="e.g., Photosynthesis, World War 2, Quadratic Equations")

if st.button("🚀 Generate Study Materials", type="primary"):
    if not topic:
        st.warning("Please enter a topic first!")
    else:
        # Reset states for new generation
        st.session_state.quiz_data = None
        st.session_state.quiz_raw = None
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.flipped_cards = set()
        st.session_state.flashcards_data = None
        
        with st.spinner("🤖 AI is preparing your study materials..."):
            
            # Generate Quiz
            if study_mode in ["Quiz", "All Three"]:
                try:
                    quiz_prompt = f"""Generate a {difficulty} difficulty quiz about {topic} with {num_questions} multiple choice questions.
                    
Format your response EXACTLY like this:
Q1: [Question]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Correct Answer: [A/B/C/D]

Q2: [Question]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Correct Answer: [A/B/C/D]

Continue for all {num_questions} questions."""
                    
                    response = requests.post(
                        "https://text.pollinations.ai/",
                        json={
                            "messages": [
                                {"role": "system", "content": "You are a helpful educational assistant that creates clear, accurate study materials."},
                                {"role": "user", "content": quiz_prompt}
                            ],
                            "model": "openai"
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        quiz_text = response.text
                        parsed = parse_quiz(quiz_text)
                        if parsed:
                            st.session_state.quiz_data = parsed
                        else:
                            # Fallback: store raw text if parsing fails
                            st.session_state.quiz_raw = quiz_text
                            st.warning("Quiz generated but couldn't be parsed into interactive format. Showing raw quiz.")
                    else:
                        st.error(f"Failed to generate quiz (Status: {response.status_code}). Please try again.")
                        
                except Exception as e:
                    st.error(f"Error generating quiz: {str(e)}")
            
            # Generate Flashcards
            if study_mode in ["Flashcards", "All Three"]:
                try:
                    flashcard_prompt = f"""Generate {num_flashcards} flashcards about {topic}.
                    
Format your response EXACTLY like this:
CARD 1
Front: [Question or term]
Back: [Answer or definition]

CARD 2
Front: [Question or term]
Back: [Answer or definition]

Continue for all {num_flashcards} flashcards."""
                    
                    response = requests.post(
                        "https://text.pollinations.ai/",
                        json={
                            "messages": [
                                {"role": "system", "content": "You are a helpful educational assistant that creates clear, concise flashcards."},
                                {"role": "user", "content": flashcard_prompt}
                            ],
                            "model": "openai"
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        st.session_state.flashcards_data = parse_flashcards(response.text)
                    else:
                        st.error("Failed to generate flashcards. Please try again.")
                        
                except Exception as e:
                    st.error(f"Error generating flashcards: {str(e)}")
            
            # Generate Study Guide
            if study_mode in ["Study Guide", "All Three"]:
                st.markdown("---")
                st.header("📖 Study Guide")
                
                try:
                    guide_prompt = f"""Create a comprehensive study guide about {topic}.

Include:
1. Key Concepts (3-5 main ideas)
2. Important Terms and Definitions
3. Summary/Overview
4. Practice Tips

Make it clear, organized, and easy to understand for students."""
                    
                    response = requests.post(
                        "https://text.pollinations.ai/",
                        json={
                            "messages": [
                                {"role": "system", "content": "You are a helpful educational assistant that creates comprehensive study guides."},
                                {"role": "user", "content": guide_prompt}
                            ],
                            "model": "openai"
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        guide_text = response.text
                        st.markdown(guide_text)
                    else:
                        st.error("Failed to generate study guide. Please try again.")
                        
                except Exception as e:
                    st.error(f"Error generating study guide: {str(e)}")
            
            # Generate Diagram
            if generate_diagram:
                st.markdown("---")
                st.header("🖼️ Study Diagram")
                
                try:
                    diagram_prompt = f"educational diagram explaining {topic}, clear labels, simple illustration style, whiteboard drawing"
                    image_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(diagram_prompt)}?width=1024&height=768&model=flux&nologo=true"
                    
                    st.image(image_url, caption=f"Visual Guide: {topic}", use_container_width=True)
                    st.markdown(f"[Download Diagram]({image_url})")
                    
                except Exception as e:
                    st.error(f"Error generating diagram: {str(e)}")
            
            st.success("✅ Study materials generated successfully!")
            st.balloons()
            
            # Rerun to display the generated content
            st.rerun()

# Display Quiz (outside the generate button to persist)
if st.session_state.quiz_data and study_mode in ["Quiz", "All Three"]:
    st.markdown("---")
    st.header("📝 Quiz")
    
    questions = st.session_state.quiz_data
    
    if not st.session_state.quiz_submitted:
        st.markdown(f"**Answer all {len(questions)} questions, then submit to see your results!**")
        st.markdown("")
        
        # Display each question
        for i, q in enumerate(questions):
            st.markdown(f"""
            <div class='quiz-question'>
                <h4>Question {i + 1}: {q['question']}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Create options list
            options = [f"{letter}) {text}" for letter, text in sorted(q['options'].items())]
            
            # Radio button for answer selection
            selected = st.radio(
                f"Select your answer for Question {i + 1}:",
                options,
                key=f"q_{i}",
                index=None,
                label_visibility="collapsed"
            )
            
            if selected:
                # Extract the letter from the selection
                st.session_state.user_answers[i] = selected[0]
            
            st.markdown("")
        
        # Submit button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            answered = len(st.session_state.user_answers)
            total = len(questions)
            
            st.markdown(f"**Questions answered: {answered}/{total}**")
            
            if st.button("📊 Submit Quiz", type="primary", use_container_width=True):
                if answered < total:
                    st.warning(f"Please answer all questions before submitting. You've answered {answered}/{total}.")
                else:
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
            
            # Style based on correctness
            status_class = "correct-answer" if is_correct else "incorrect-answer"
            status_icon = "✅" if is_correct else "❌"
            
            st.markdown(f"""
            <div class='quiz-question {status_class}'>
                <h4>{status_icon} Question {i + 1}: {q['question']}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Show options with highlighting
            for letter, text in sorted(q['options'].items()):
                if letter == q['correct']:
                    st.markdown(f"✅ **{letter}) {text}** *(Correct Answer)*")
                elif letter == user_answer and not is_correct:
                    st.markdown(f"❌ ~~{letter}) {text}~~ *(Your Answer)*")
                else:
                    st.markdown(f"{letter}) {text}")
            
            st.markdown("")
        
        # Results summary
        score_percentage = (correct_count / len(questions)) * 100
        
        st.markdown("---")
        st.markdown(f"""
        <div class='results-box'>
            <h2 style='color: #ffffff !important;'>📊 Quiz Results</h2>
            <div class='score-display'>{correct_count}/{len(questions)}</div>
            <p style='font-size: 24px; color: #b0b0b0 !important;'>{score_percentage:.0f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Feedback message
        if score_percentage == 100:
            st.success("🎉 Perfect score! You've mastered this topic!")
        elif score_percentage >= 80:
            st.success("🌟 Great job! You have a strong understanding of this topic!")
        elif score_percentage >= 60:
            st.info("👍 Good effort! Review the questions you missed and try again.")
        else:
            st.warning("📚 Keep studying! Review the material and try the quiz again.")
        
        # Retry button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Retake Quiz", use_container_width=True):
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()

# Fallback: Display raw quiz if parsing failed
elif st.session_state.quiz_raw and study_mode in ["Quiz", "All Three"]:
    st.markdown("---")
    st.header("📝 Quiz")
    st.markdown(st.session_state.quiz_raw)

# Display Flashcards (outside the generate button to persist)
if st.session_state.flashcards_data and study_mode in ["Flashcards", "All Three"]:
    st.markdown("---")
    st.header("🎴 Flashcards")
    
    cards = st.session_state.flashcards_data
    total_cards = len(cards)
    flipped_count = len(st.session_state.flipped_cards)
    
    # Progress bar
    progress = flipped_count / total_cards if total_cards > 0 else 0
    st.markdown(f"**Progress: {flipped_count}/{total_cards} cards flipped**")
    st.progress(progress)
    
    # Reset button
    if st.button("🔄 Reset All Cards"):
        st.session_state.flipped_cards = set()
        st.rerun()
    
    st.markdown("")
    
    # Display cards in grid
    cols = st.columns(2)
    for idx, card in enumerate(cards):
        with cols[idx % 2]:
            card_id = f"card_{idx}"
            is_flipped = card_id in st.session_state.flipped_cards
            
            if not is_flipped:
                # Show front
                st.markdown(f"""
                <div class='flashcard flashcard-front'>
                    <div class='flashcard-label'>Question / Term</div>
                    <div class='flashcard-content'>{card['front']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🔄 Flip Card", key=f"flip_{idx}"):
                    st.session_state.flipped_cards.add(card_id)
                    st.rerun()
            else:
                # Show back
                st.markdown(f"""
                <div class='flashcard flashcard-back'>
                    <div class='flashcard-label'>Answer / Definition</div>
                    <div class='flashcard-content'>{card['back']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"↩️ Flip Back", key=f"unflip_{idx}"):
                    st.session_state.flipped_cards.remove(card_id)
                    st.rerun()
            
            st.markdown("")

# Footer
st.markdown("---")
st.markdown("""
    <div class='footer'>
        <p>Made with ❤️ for students everywhere</p>
        <p>Powered by Pollinations.AI | Free & Open Source</p>
    </div>
""", unsafe_allow_html=True)
