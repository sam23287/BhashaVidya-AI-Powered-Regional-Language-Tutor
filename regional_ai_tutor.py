import streamlit as st
import os
import tempfile
import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
from openai import OpenAI, OpenAIError
from pydub import AudioSegment
from dotenv import load_dotenv
import logging
import openai

# Load environment variables from a specific file (e.g., 'api.env')
load_dotenv('api.env')

# Get the Groq API key from the environment variable
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize OpenAI client for Groq endpoint
try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_api_key)
except OpenAIError as e:
    print(f"An error occurred while initializing the OpenAI client: {str(e)}")

# ✅ Subjects and topics
subjects = {
    "Science": [
        "Cell Structure", "Photosynthesis", "Light", "Combustion", 
        "Atoms and Molecules", "Gravity", "Electricity", "Magnetism", "Human Digestive System"
    ],
    "Math": [
        "Fractions", "Linear Equations", "Area of Circle", 
        "Geometry", "Probability", "Statistics", "Trigonometry", "Calculus"
    ],
    "Social Science": [
        "Indian Constitution", "Resources", "Democracy", "World Wars", 
        "Climate Change", "Nationalism", "Economic Development", "Cultural Heritage"
    ],
    "History": [
        "Ancient Civilizations", "World War I", "World War II", 
        "Indian Independence Movement", "Renaissance", "French Revolution"
    ],
    "Geography": [
        "Earth's Layers", "Rivers", "Mountains", "Oceans", "Climate Zones", "Map Reading", "Natural Resources"
    ],
    "Literature": [
        "Shakespeare's Works", "Poetry", "Fiction", "Non-Fiction", 
        "Literary Devices", "Narrative Techniques"
    ]
}

# ✅ Language options with ISO codes
languages = {
    "Hindi": "hi", 
    "Tamil": "ta", 
    "Kannada": "kn", 
    "Marathi": "mr", 
    "English": "en",
    "Bengali": "bn", 
    "Gujarati": "gu", 
    "Punjabi": "pa", 
    "Telugu": "te", 
    "Urdu": "ur", 
    "Arabic": "ar", 
    "French": "fr", 
    "Spanish": "es", 
    "German": "de", 
    "Russian": "ru", 
    "Chinese (Simplified)": "zh-cn", 
    "Japanese": "ja", 
    "Korean": "ko", 
    "Portuguese": "pt", 
    "Italian": "it", 
    "Dutch": "nl", 
    "Swedish": "sv", 
    "Finnish": "fi", 
    "Greek": "el", 
    "Turkish": "tr"
}

# ✅ Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Get explanation from Groq using llama3
def get_explanation_from_groq(subject, topic):
    try:
        prompt = f"Explain the topic '{topic}' from the subject {subject} to a class 8 student in very simple language."
        
        response = client.chat.completions.create(
            model="llama3-70b-8192",  # ✅ Updated from deprecated mixtral model
            messages=[
                {"role": "system", "content": "You are a helpful teacher for school students."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error occurred while fetching explanation: {e}")
        return "Sorry, an error occurred while fetching the explanation."

# ✅ Translate text to selected language
def translate_text(text, target_lang_code):
    try:
        return GoogleTranslator(source="auto", target=target_lang_code).translate(text)
    except Exception as e:
        logging.error(f"Error occurred while translating text: {e}")
        return "Sorry, an error occurred while translating the text."

# ✅ Convert translated text to speech
def speak_text(text, lang_code):
    try:
        tts = gTTS(text=text, lang=lang_code)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        logging.error(f"Error occurred while converting text to speech: {e}")
        return "Sorry, an error occurred while converting the text to speech."

# ✅ Convert Uploaded Audio to WAV
def convert_audio(uploaded_file):
    try:
        if uploaded_file.size > 5 * 1024 * 1024:  # 5MB max size for security
            raise ValueError("File is too large. Please upload a smaller file.")
        
        if not uploaded_file.name.endswith(".wav"):
            raise ValueError("Only WAV files are allowed.")
        
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_input.write(uploaded_file.read())
        audio = AudioSegment.from_file(temp_input.name)
        wav_path = temp_input.name
        return wav_path
    except Exception as e:
        logging.error(f"Error occurred while converting audio: {e}")
        return "Sorry, an error occurred while processing the audio file."

# ✅ Speech-to-Text
def speech_to_text(audio_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, could not understand audio."
    except sr.RequestError:
        return "Speech recognition service failed."
    except Exception as e:
        logging.error(f"Error occurred during speech recognition: {e}")
        return "Sorry, an error occurred during speech recognition."

# ✅ Extract subject and topic from user query (simplified matching)
def extract_subject_and_topic(user_query):
    for subject, topics in subjects.items():
        for topic in topics:
            if topic.lower() in user_query.lower():
                return subject, topic
    return None, None  # If no match is found

# ✅ Streamlit UI
st.set_page_config(page_title="AI Tutor", page_icon="🎙️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
        body {
            background-color: #f0f0f5;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
            font-size: 16px;
            padding: 10px;
            border-radius: 8px;
        }
        .stButton button:hover {
            background-color: #45a049;
        }
        .stSelectbox select, .stFileUploader input {
            background-color: #e0f7fa;
            font-size: 14px;
        }
        .stHeader {
            text-align: center;
            font-family: 'Helvetica', sans-serif;
            color: #212121;
            font-size: 24px;
        }
        .stText {
            font-family: 'Arial', sans-serif;
        }
    </style>
""", unsafe_allow_html=True)
st.image("logo.png", width=200)  # Add logo
st.title("🎙️ BhashaVidya - Voice-enabled Regional AI Tutor")
st.subheader("🇮🇳 Ask Your Question or Choose a Topic Below")

tab1, tab2 = st.tabs(["🎤 Speak Your Question", "📚 Choose Topic"])

# ✅ Tab 1: Voice Input
with tab1:
    st.markdown("<h2>Ask Your Question by Speaking 🎤</h2>", unsafe_allow_html=True)
    uploaded_audio = st.file_uploader("Upload your voice question (WAV)", type=["wav"])
    language = st.selectbox("Select Language", list(languages.keys()), key="lang1")

    if st.button("🎓 Explain from Voice"):
        if uploaded_audio:
            with st.spinner("Processing voice input..."):
                audio_path = convert_audio(uploaded_audio)
                if isinstance(audio_path, str) and "Sorry" in audio_path:
                    st.error(audio_path)
                else:
                    user_query = speech_to_text(audio_path)
                    st.markdown(f"**You said:** `{user_query}`")

                    # Extract subject and topic
                    subject, topic = extract_subject_and_topic(user_query)
                    
                    if subject and topic:
                        explanation = get_explanation_from_groq(subject, topic)
                        st.subheader("📘 Explanation in English:")
                        st.write(explanation)
                        
                        translated = translate_text(explanation, languages[language])
                        st.subheader(f"📙 Explanation in {language}:")
                        st.write(translated)

                        audio_path = speak_text(translated, languages[language])
                        st.subheader("🔊 Audio Explanation:")
                        st.audio(audio_path)
                    else:
                        st.error("Sorry, I could not understand the subject or topic from your question.")
        else:
            st.warning("Please upload a WAV audio file.")

# ✅ Tab 2: Predefined Topics
with tab2:
    st.markdown("<h2>Choose a Topic 📚</h2>", unsafe_allow_html=True)
    subject = st.selectbox("Select Subject", list(subjects.keys()))
    topic = st.selectbox("Select Topic", subjects[subject])
    language = st.selectbox("Select Language", list(languages.keys()), key="lang2")

    if st.button("🎓 Explain Topic"):
        with st.spinner("Generating explanation..."):
            explanation = get_explanation_from_groq(subject, topic)
            st.subheader("📘 Explanation in English:")
            st.write(explanation)

            translated = translate_text(explanation, languages[language])
            st.subheader(f"📙 Explanation in {language}:")
            st.write(translated)

            audio_path = speak_text(translated, languages[language])
            st.subheader("🔊 Audio Explanation:")
            st.audio(audio_path)
