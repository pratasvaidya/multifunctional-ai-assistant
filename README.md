# Multifunctional AI Assistant
Demo video: https://drive.google.com/file/d/1AfqjYs1_6OqNzkyZbt_CiWr0XF4OT3vY/view?usp=sharing
A voice controlled, hardware based AI assistant built on a Raspberry Pi. It uses push to talk to process language commands, control Spotify playback, and manage Meross smart home devices with the Groq API.

## Hardware
* Raspberry Pi (Tested on ARMv6)
* USB Microphone and Bluetooth Speaker
* SSD1306 OLED Display (SPI interface)
* Push Button (BCM GPIO 17)

## API Requirements
* **Groq**: API key for Whisper (Speech-to-Text) and GPT (LLM processing).
* **Spotify Developer**: Client ID, Client Secret, and Redirect URI for `spotipy` integration.
* **Meross**: Account email and password for smart switch control.

## Features
* Functional AI assistant with memory
* Spotify playback with a graphic interface
* Smart home control (Meross)
* Fully automatic startup
* Proper shutdown sequence (Press button for >5 seconds)
  
