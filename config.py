import os
from dotenv import load_dotenv

load_dotenv()

# --- Hardware Pins (BCM Numbering) ---
BUTTON_PIN = 17
OLED_DC_PIN = 24
OLED_RST_PIN = 25

# --- Interaction & Audio Settings ---
SHUTDOWN_HOLD_SECONDS = 5
SAMPLE_RATE = 44100

# --- Groq API Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_STT_MODEL = "whisper-large-v3"
GROQ_CHAT_MODEL = "openai/gpt-oss-20b"

# --- Spotify API Configuration ---
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# --- Meross Smart Home Configuration ---
MEROSS_EMAIL = os.getenv("MEROSS_EMAIL")
MEROSS_PASSWORD = os.getenv("MEROSS_PASSWORD")

# --- AI System Prompt ---
SYSTEM_PROMPT = """You are a concise, highly capable AI assistant operating on a Raspberry Pi cyberdeck.
You can control Spotify playback and a bedroom light switch via provided tools.
Keep responses brief and direct.
Do not use markdown formatting like asterisks, hashtags, or backticks."""
