import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config

# Define scope for both controlling playback and reading the current track
scope = "user-modify-playback-state user-read-playback-state"

# Initialize Spotipy client globally
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=config.SPOTIPY_CLIENT_ID,
    client_secret=config.SPOTIPY_CLIENT_SECRET,
    redirect_uri=config.SPOTIPY_REDIRECT_URI,
    scope=scope,
    cache_path="/home/pratas/cyberdeckai/.cache",
    open_browser=False
))

def play_track_or_artist(query):
    try:
        result = sp.search(q=query, type='track', limit=1)
        tracks = result['tracks']['items']
        if tracks:
            track_uri = tracks[0]['uri']
            sp.start_playback(uris=[track_uri])
            return f"Playing {tracks[0]['name']} by {tracks[0]['artists'][0]['name']}."
        return "No results found."
    except Exception as e:
        return f"Error playing Spotify: {e}"

def pause_playback():
    try:
        sp.pause_playback()
        return "Playback paused."
    except Exception as e:
        return f"Error pausing Spotify: {e}"

def skip_playback():
    try:
        sp.next_track()
        return "Skipped to next track."
    except Exception as e:
        return f"Error skipping Spotify: {e}"

def get_current_playback():
    try:
        playback = sp.current_playback()
        
        # Spotify API returns None if playback is completely stopped/inactive
        if playback and playback.get("is_playing") and playback.get("item"):
            item = playback["item"]
            return {
                "name": item["name"],
                "artist": item["artists"][0]["name"],
                "progress_ms": playback["progress_ms"],
                "duration_ms": item["duration_ms"]
            }
    except Exception as e:
        print(f"Spotify Poll Error: {e}")
        
    return None
