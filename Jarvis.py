import datetime
import os
import platform
import subprocess
import sys
import threading
import time
import webbrowser
from typing import Optional

from bs4 import BeautifulSoup
import pystray
from PIL import Image, ImageDraw
from openai import OpenAI
import pyttsx3
import requests
import speech_recognition as sr
import wikipedia


class BackgroundVoiceAssistant:
    """A persistent, multi-threaded background voice assistant with a system tray interface."""

    POPULAR_WEBSITES = {
        "google": "https://google.com",
        "w3schools": "https://w3schools.com",
        "w3 schools": "https://w3schools.com",
        "gemini": "https://gemini.google.com",
        "claude": "https://claude.ai",
        "chat gpt": "https://chatgpt.com",
        "chatgpt": "https://chatgpt.com",
        "openai": "https://chatgpt.com",
        "netlify": "https://netlify.com",
        "github": "https://github.com",
        "git": "https://github.com"
    }

    def __init__(self, openai_api_key: Optional[str] = None):
        self.is_running = True
        self.icon = None
        self.WAKE_WORD = "jarvis"  # Keep this lowercase
        
        # Audio Engine Lock to prevent the background thread from listening to its own voice
        self.audio_lock = threading.Lock()

        # Initialize Text-to-Speech Engine Safely
        try:
            self.engine = pyttsx3.init('sapi5')
            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)
        except Exception as e:
            print(f"Warning: Driver-specific speech engine failed ({e}). Falling back to default.")
            self.engine = pyttsx3.init()

        # Initialize Speech Recognizer and calibrate audio parameters
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

        # Initialize OpenAI Client if key is provided
        self.ai_client = None
        if openai_api_key:
            try:
                self.ai_client = OpenAI(api_key=openai_api_key)
                print("AI features activated successfully.")
            except Exception as e:
                print(f"Failed to initialize OpenAI client: {e}")

    # ==========================================
    # CORE AUDIO / CAPTURE SYSTEMS
    # ==========================================

    def speak(self, text: str) -> None:
        """Handles audio synthesis and prints output to the console."""
        print(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen_command(self) -> str:
        """Captures an active audio stream and converts it into a text string."""
        with sr.Microphone() as source:
            print("\n[Active Mode] Listening for intent...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self.recognizer.pause_threshold = 1.0
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                return "none"

        try:
            print("Recognizing intent...")
            query = self.recognizer.recognize_google(audio, language='en-in')
            print(f"User Spoke: {query}")
            return query.lower().strip()
        except sr.UnknownValueError:
            return "none"
        except sr.RequestError:
            print("Network Error: Google Speech Recognition API is down.")
            return "none"

    def listen_for_wake_word(self) -> None:
        """Runs continuously in a background thread checking for the activation keyword."""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            print(f"Background worker active. Passively listening for wake word: '{self.WAKE_WORD}'...")

            while self.is_running:
                # If the assistant is actively interacting, bypass passive listening to avoid collision
                if self.audio_lock.locked():
                    time.sleep(1)
                    continue

                try:
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=3)
                    
                    if self.audio_lock.locked():
                        continue
                        
                    text = self.recognizer.recognize_google(audio, language='en-in').lower().strip()
                    
                    if self.WAKE_WORD in text:
                        print(f"Wake word activated via audio sequence: '{text}'")
                        self.trigger_assistant_action()
                        
                except sr.UnknownValueError:
                    continue  # Noise didn't translate to coherent speech
                except sr.RequestError:
                    print("Network dropped. Retrying ambient wake listener stream...")
                    time.sleep(5)
                except Exception as e:
                    print(f"Background worker loop error: {e}")

    def trigger_assistant_action(self) -> None:
        """Acquires a thread lock and steps into active intent processing mode."""
        with self.audio_lock:
            # Play a native system chime sound alert to show active listening mode
            sys.stdout.write('\a')
            sys.stdout.flush()
            
            self.speak("How can I help you?")
            query = self.listen_command()
            
            if query != "none":
                self.handle_query(query)

    # ==========================================
    # HARDWARE & AUTOMATION MODULES
    # ==========================================

    def set_system_volume(self, level: int) -> str:
        """Adjusts master volume values safely cross-platform across OS layers."""
        level = max(0, min(100, level))
        os_name = platform.system().lower()

        try:
            if "windows" in os_name:
                cmd = f"(Get-AudioDevice -Playback).Volume = {level}"
                subprocess.run(["powershell", "-Command", cmd], capture_output=True, check=True)
            elif "darwin" in os_name:  # macOS
                mac_level = int((level / 100) * 7)
                subprocess.run(["osascript", "-e", f"set volume {mac_level}"], check=True)
            elif "linux" in os_name:
                subprocess.run(["amixer", "-D", "pulse", "sset", "Master", f"{level}%"], capture_output=True, check=True)
            return f"System volume adjusted to {level} percent."
        except Exception as e:
            print(f"Hardware automation failure: {e}")
            return "I was unable to modify your system audio level configurations."

    def launch_app(self, app_name: str) -> str:
        """Launches target local desktop applications using global environment paths."""
        app_name = app_name.lower().strip()
        os_name = platform.system().lower()

        windows_apps = {"notepad": "notepad.exe", "calculator": "calc.exe", "task manager": "taskmgr.exe", "cmd": "cmd.exe"}
        mac_apps = {"calculator": "Calculator", "notes": "Notes", "safari": "Safari"}

        try:
            if "windows" in os_name:
                target = windows_apps.get(app_name, f"{app_name}.exe")
                os.startfile(target)
                return f"Opening execution sequence for {app_name}."
            elif "darwin" in os_name:
                target = mac_apps.get(app_name, app_name.title())
                subprocess.run(["open", "-a", target], check=True)
                return f"Opening local instance of {app_name}."
            elif "linux" in os_name:
                subprocess.Popen([app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Booting background Linux process for {app_name}."
        except Exception:
            return f"I couldn't locate {app_name} mapped on your desktop application paths."

    def scrape_google(self, query: str) -> str:
        """Scrapes the quick answers snippet block elements directly off Google search query nodes."""
        url = f"https://www.google.com/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            res = requests.get(url, headers=headers, timeout=5)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')
            answer_div = soup.find('div', class_='BNeawe')
            return answer_div.text if answer_div else "I couldn't locate a direct snippet summary on Google search parameters."
        except Exception as e:
            return f"Google scraping routine thrown exception error: {e}"

    def ask_ai(self, prompt: str) -> None:
        """Generates contextual conversational completions using modern rapid LLM configurations."""
        if not self.ai_client:
            self.speak("AI functions remain inactive because an OpenAI validation key was not loaded.")
            return
        if not prompt:
            self.speak("What question should I pass to the AI engine cluster?")
            return

        try:
            response = self.ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            self.speak(response.choices[0].message.content.strip())
        except Exception as e:
            print(f"AI Exception Context: {e}")
            self.speak("I ran into an internal execution fault contacting the OpenAI endpoint.")

    # ==========================================
    # ROUTING & CORE ENGINE LOOP CONTROLS
    # ==========================================

    def handle_query(self, query: str) -> bool:
        """Main routing parser maps detected speech intents to custom modular functions."""
        
        # 1. Lookups
        if 'wikipedia' in query:
            self.speak('Checking Wikipedia records...')
            search_term = query.replace("wikipedia", "").strip()
            try:
                self.speak(wikipedia.summary(search_term, sentences=2))
            except Exception:
                self.speak("I could not pull verified files from Wikipedia targets.")

        elif 'google' in query:
            self.speak('Searching Google engines...')
            search_term = query.replace("google", "").replace("search", "").strip()
            self.speak(self.scrape_google(search_term))

        elif 'time' in query:
            self.speak(f"The time is currently {datetime.datetime.now().strftime('%I:%M %p')}")

        elif 'ask ai' in query:
            ai_prompt = query.replace("ask ai for", "").replace("ask ai", "").strip()
            self.ask_ai(ai_prompt)

        # 2. Automation Injects
        elif 'volume' in query:
            digits = [int(s) for s in query.split() if s.isdigit()]
            if digits:
                self.speak(self.set_system_volume(digits[0]))
            else:
                self.speak("Please specify a target percentage value for volume adjustments.")

        elif 'launch' in query or 'open app' in query:
            target_app = query.replace("launch", "").replace("open app", "").strip()
            self.speak(self.launch_app(target_app))

        # 3. Web Navigation Handlers
        else:
            opened = False
            for site, url in self.POPULAR_WEBSITES.items():
                if f"open {site}" in query:
                    self.speak(f"Opening browser window for {site}")
                    webbrowser.open(url)
                    opened = True
                    break
            if not opened and "open" in query:
                self.speak("I don't recognize that specific custom website macro.")

        return True

    def create_tray_image(self) -> Image.Image:
        """Generates the graphic layout block utilized inside the native System Tray panel icon taskbars."""
        image = Image.new('RGB', (64, 64), color='black')
        dc = ImageDraw.Draw(image)
        dc.rectangle([16, 16, 48, 48], fill='#0078D7')  # Blue active center indicator block
        return image

    def on_exit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Gracefully tears down background workers, thread processes, and exits."""
        print("\nShedding runtime application environments...")
        self.is_running = False
        icon.stop()

    def run(self) -> None:
        """Initializes components and maps application processing into asynchronous running state frames."""
        worker_thread = threading.Thread(target=self.listen_for_wake_word, daemon=True)
        worker_thread.start()

        menu = pystray.Menu(
            pystray.MenuItem("Status: Active Listening", lambda: None, enabled=False),
            pystray.MenuItem("Force Assistant Activation", lambda: self.trigger_assistant_action()),
            pystray.MenuItem("Exit System Service", self.on_exit)
        )

        self.icon = pystray.Icon(
            "VoiceAssistantService",
            self.create_tray_image(),
            title="Desktop Voice Assistant Service Engine",
            menu=menu
        )
        
        self.icon.run()


if __name__ == "__main__":
    print("=== Launching Persistent Background System Service ===")
    
    # Prompt user explicitly for API key at boot. Pressing Enter bypasses AI comfortably.
    user_key = input("Enter your OpenAI API key to activate AI features (or press Enter to skip): ").strip()
    
    if not user_key:
        print("[System Info] Proceeding without AI modules. Wake word tasks remain fully active.")
        user_key = None

    assistant_service = BackgroundVoiceAssistant(openai_api_key=user_key)
    assistant_service.run()
