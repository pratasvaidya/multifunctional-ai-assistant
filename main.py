import os
import time
import wave
import subprocess
import tempfile
import textwrap
import json
import re
import RPi.GPIO as GPIO
import sounddevice as sd
import numpy as np
from groq import Groq
from luma.core.interface.serial import spi
from luma.oled.device import ssd1306
from luma.core.render import canvas

import config
import spotify_control
import smarthome

# ---------- Setup ----------

HISTORY_FILE = "/home/pratas/cyberdeckai/chat_history.json"

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(config.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

oled_serial = spi(port=0, device=0, gpio_DC=config.OLED_DC_PIN, gpio_RST=config.OLED_RST_PIN)
oled = ssd1306(oled_serial, rotate=2)

client = Groq(api_key=config.GROQ_API_KEY)

# ---------- Tools Definition ----------

tools = [
    {
        "type": "function",
        "function": {
            "name": "play_spotify",
            "description": "Play a specific song or artist on Spotify. Extract strictly the track or artist name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The song title or artist to search and play."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pause_spotify",
            "description": "Pause the current Spotify playback.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "skip_spotify",
            "description": "Skip to the next track on Spotify.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_bedroom_light",
            "description": "Turn the bedroom light switch on or off.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["on", "off"],
                        "description": "Whether to turn the light on or off."
                    }
                },
                "required": ["action"]
            }
        }
    }
]

# ---------- Functions ----------

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return [{"role": "system", "content": config.SYSTEM_PROMPT}]
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"History load error: {e}")
        return [{"role": "system", "content": config.SYSTEM_PROMPT}]

def save_history(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)
    except Exception as e:
        print(f"History save error: {e}")

chat_history = load_history()

def sanitize_history(history):
    if len(history) > 7:
        history = [history[0]] + history[-6:]

    clean_history = []
    for msg in history:
        if isinstance(msg, dict):
            clean_msg = {k: v for k, v in msg.items() if k in ['role', 'content', 'tool_calls', 'tool_call_id', 'name']}
            clean_history.append(clean_msg)
        else:
            clean_msg = {"role": msg.role, "content": getattr(msg, 'content', "") or ""}
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                clean_msg["tool_calls"] = [
                    {"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ]
            clean_history.append(clean_msg)
    return clean_history

def show_text(text, max_lines=8, chars_per_line=21):
    clean_text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    clean_text = clean_text.replace("*", "").replace("#", "").replace("`", "")
    clean_text = clean_text.encode('ascii', 'ignore').decode('ascii')

    wrapped = textwrap.wrap(clean_text, width=chars_per_line)[:max_lines]
    with canvas(oled) as draw:
        for i, line in enumerate(wrapped):
            draw.text((0, i * 8), line, fill="white")

def record_audio_until_stopped():
    frames = []
    def callback(indata, frames_count, time_info, status):
        frames.append(indata.copy())

    stream = sd.InputStream(device=0, samplerate=config.SAMPLE_RATE, channels=1, dtype="int16", callback=callback)
    stream.start()
    show_text("Listening...")

    with stream:
        while GPIO.input(config.BUTTON_PIN) == GPIO.HIGH:
            time.sleep(0.05)

    tmp_path = tempfile.mktemp(suffix=".wav")
    with wave.open(tmp_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(config.SAMPLE_RATE)
        wf.writeframes(np.concatenate(frames, axis=0).tobytes())
    return tmp_path

def transcribe(audio_path):
    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio_path, file.read()),
            model=config.GROQ_STT_MODEL,
        )
    return transcription.text.strip()

def speak(text):
    try:
        # Uses Flite for offline, low-latency TTS. 'rms' is the male US voice.
        subprocess.run(["flite", "-voice", "rms", "-t", text], check=True)
    except Exception as e:
        print(f"TTS Error: {e}")
        subprocess.run(["espeak-ng", "-v", "en-us", "-s", "150", text])

# ---------- Main loop ----------

def main():
    global chat_history
    print("Cyberdeck ready. Short press: toggle talk. Long press: shutdown.")
    show_text("Ready. Press to talk.")

    try:
        last_ui_update = 0

        while True:
            # Idle loop: polls Spotify and updates OLED without blocking the button
            while GPIO.input(config.BUTTON_PIN) == GPIO.HIGH:
                now = time.time()

                # Update screen every 5 seconds to avoid Spotify rate limits
                if now - last_ui_update > 5.0:
                    try:
                        spotify_info = spotify_control.get_current_playback()

                        if spotify_info:
                            with canvas(oled) as draw:
                                # Draw Text (truncate to fit screen width)
                                draw.text((0, 0), "Now Playing:", fill="white")
                                draw.text((0, 16), spotify_info["name"][:20], fill="white")
                                draw.text((0, 32), spotify_info["artist"][:20], fill="white")

                                # Draw Progress Bar
                                pct = spotify_info["progress_ms"] / spotify_info["duration_ms"]
                                bar_width = int(127 * pct)
                                draw.rectangle((0, 50, 127, 60), outline="white")  # Border
                                draw.rectangle((0, 50, bar_width, 60), fill="white") # Fill
                        else:
                            show_text("Ready. Press to talk.")
                    except Exception as e:
                        print(f"Spotify UI Poll Error: {e}")
                        show_text("Ready. Press to talk.")

                    last_ui_update = now

                time.sleep(0.05)

            # Button is pressed, start interaction
            start_press = time.time()
            while GPIO.input(config.BUTTON_PIN) == GPIO.LOW:
                time.sleep(0.05)
            duration = time.time() - start_press

            if duration >= config.SHUTDOWN_HOLD_SECONDS:
                show_text("Shutting down...")
                subprocess.run(["sudo", "shutdown", "-h", "now"])
                break

            audio_path = record_audio_until_stopped()

            show_text("Thinking...")
            transcript = transcribe(audio_path)
            os.remove(audio_path)

            if transcript:
                print(f"You said: {transcript}")

                chat_history.append({"role": "user", "content": transcript})

                try:
                    response = client.chat.completions.create(
                        messages=sanitize_history(chat_history),
                        model=config.GROQ_CHAT_MODEL,
                        tools=tools,
                        tool_choice="auto",
                        parallel_tool_calls=False
                    )
                except Exception as e:
                    if "tool_use_failed" in str(e) or "Failed to call a function" in str(e):
                        print("Model hallucinated a tool. Retrying as plain text...")
                        response = client.chat.completions.create(
                            messages=sanitize_history(chat_history),
                            model=config.GROQ_CHAT_MODEL
                        )
                    else:
                        print(f"API Error: {e}")
                        chat_history.pop()
                        speak("I encountered an error connecting to the network.")
                        show_text("Network Error")
                        continue

                response_message = response.choices[0].message

                if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
                    chat_history.append(response_message.model_dump())

                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        tool_result = ""
                        if function_name == "play_spotify":
                            tool_result = spotify_control.play_track_or_artist(function_args.get("query"))
                        elif function_name == "pause_spotify":
                            tool_result = spotify_control.pause_playback()
                        elif function_name == "skip_spotify":
                            tool_result = spotify_control.skip_playback()
                        elif function_name == "control_bedroom_light":
                            tool_result = smarthome.control_bedroom_light(function_args.get("action"))

                        chat_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": tool_result
                        })

                    second_response = client.chat.completions.create(
                        messages=sanitize_history(chat_history),
                        model=config.GROQ_CHAT_MODEL
                    )
                    reply = second_response.choices[0].message.content.strip()
                else:
                    reply = response_message.content.strip()

                reply = re.sub(r'[*#_`]', '', reply)
                chat_history.append({"role": "assistant", "content": reply})

                show_text(reply)
                speak(reply)
                save_history(chat_history)

            # Immediately force UI update after interacting
            last_ui_update = 0

    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
