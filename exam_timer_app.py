import subprocess
import sys
import threading
import time
from pathlib import Path

import pyttsx3
import tkinter as tk
from tkinter import ttk

IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

if IS_WINDOWS:
    import winsound

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audios"
AUDIO_BACKUP_DIR = AUDIO_DIR / "english-bckup"
AUDIO_INSTRUCTIONS = "instructions.mp3"
AUDIO_START = "start.mp3"
AUDIO_STOP = "stop.mp3"
AUDIO_MOVE = "move-to-next-station.mp3"

# ---------------- CONFIG ----------------
STATION_TIME = 4 * 60      # 4 minutes
BREAK_TIME = 15            # 15 seconds
START_DELAY = 5            # gap between instructions and Start
COUNTDOWN_NUMBERS = (3, 2, 1)

INSTRUCTION_LINES = (
    "Hello. This is your AI exam guide.",
    "You will rotate through multiple stations. Each station lasts four minutes.",
    "When you hear Start, begin immediately.",
    "When you hear Stop, end the station and wait.",
    "You will then have fifteen seconds to move to the next station.",
    "I will count you down and keep you on time.",
)


class ExamTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Exam Timer")
        self.root.geometry("520x360")
        self.root.resizable(False, False)

        self.running = False
        self.engine = pyttsx3.init()
        self.choose_female_voice()
        self.engine.setProperty("rate", 175)
        self.engine.setProperty("volume", 1.0)

        self.setup_ui()

    # ---------- UI ----------
    def setup_ui(self):
        ttk.Style().configure("TButton", font=("Segoe UI", 12))

        self.title_label = ttk.Label(
            self.root, text="Examination Timer",
            font=("Segoe UI", 20, "bold")
        )
        self.title_label.pack(pady=15)

        self.status_label = ttk.Label(
            self.root, text="Status: Ready",
            font=("Segoe UI", 14)
        )
        self.status_label.pack(pady=10)

        self.timer_label = ttk.Label(
            self.root, text="00:00",
            font=("Segoe UI", 36, "bold")
        )
        self.timer_label.pack(pady=20)

        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=20)

        self.start_btn = ttk.Button(
            button_frame, text="▶ Start Exam",
            command=self.start_exam
        )
        self.start_btn.grid(row=0, column=0, padx=15)

        self.stop_btn = ttk.Button(
            button_frame, text="■ Stop Exam",
            command=self.stop_exam
        )
        self.stop_btn.grid(row=0, column=1, padx=15)
        self.stop_btn.state(["disabled"])

    def choose_female_voice(self):
        voices = self.engine.getProperty("voices") or []

        if IS_WINDOWS:
            preferred = ["zira", "aria", "jenny", "eva"]
        elif IS_MAC:
            preferred = ["samantha", "victoria", "serena", "karen"]
        else:
            preferred = ["female", "woman", "feminine"]

        for voice in voices:
            name = (voice.name or "").lower()
            vid = str(getattr(voice, "id", "")).lower()
            if any(tag in name or tag in vid for tag in preferred):
                self.engine.setProperty("voice", voice.id)
                return voice.id

        if voices:
            self.engine.setProperty("voice", voices[0].id)
            return voices[0].id

        return None

    # ---------- AUDIO ----------
    def resolve_audio_path(self, filename):
        primary = AUDIO_DIR / filename
        if primary.exists():
            return primary

        backup = AUDIO_BACKUP_DIR / filename
        if backup.exists():
            return backup

        return None

    def play_audio(self, filename, label):
        if not self.running:
            return False

        clip = self.resolve_audio_path(filename)
        if not clip:
            self.set_status(f"Status: Missing {label} audio")
            return False

        try:
            if IS_WINDOWS:
                winsound.PlaySound(str(clip), winsound.SND_FILENAME)
            elif IS_MAC:
                subprocess.run(["afplay", str(clip)], check=True)
            else:
                # Prefer a simple, blocking playback so sequencing stays intact.
                subprocess.run(["ffplay", "-nodisp", "-autoexit", str(clip)],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as exc:
            self.set_status(f"Status: {label} audio error")
            print(f"Failed to play {label} audio: {exc}", file=sys.stderr)
            return False

        return self.running

    # ---------- SPEECH ----------
    def speak(self, text):
        if not self.running:
            return
        self.engine.say(text)
        self.engine.runAndWait()

    # ---------- TIMER DISPLAY ----------
    def update_timer(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")

    def set_status(self, text):
        self.status_label.config(text=text)

    # ---------- MAIN LOGIC ----------
    def start_exam(self):
        if self.running:
            return
        self.running = True
        self.start_btn.state(["disabled"])
        self.stop_btn.state(["!disabled"])
        threading.Thread(target=self.exam_flow, daemon=True).start()

    def stop_exam(self):
        self.running = False
        self.engine.stop()
        self.set_status("Status: Stopped")
        self.timer_label.config(text="00:00")
        self.start_btn.state(["!disabled"])
        self.stop_btn.state(["disabled"])

    def play_instructions(self):
        self.engine.stop()
        self.set_status("Status: Instructions")

        played = self.play_audio(AUDIO_INSTRUCTIONS, "instructions")
        if played:
            return self.running

        if not self.running:
            return False

        # Fallback to spoken instructions if the audio file is missing.
        for line in INSTRUCTION_LINES:
            if not self.running:
                return False
            self.speak(line)
            time.sleep(0.25)
        time.sleep(0.3)
        return self.running

    def run_countdown(self, seconds, status_prefix):
        for remaining in range(seconds, 0, -1):
            if not self.running:
                return False
            self.set_status(f"{status_prefix} {remaining}s")
            self.update_timer(remaining)
            time.sleep(1)
        return self.running

    def countdown_to_start(self):
        if not self.running:
            return False

        for remaining in range(START_DELAY, 0, -1):
            if not self.running:
                return False
            self.set_status(f"Status: Starting in {remaining}s")
            self.update_timer(remaining)

            if remaining in COUNTDOWN_NUMBERS:
                self.speak(str(remaining))

            time.sleep(1)

        played = self.play_audio(AUDIO_START, "start")
        if not played and self.running:
            self.speak("Start")
        return self.running

    def run_station_timer(self, station_number):
        for t in range(STATION_TIME, 0, -1):
            if not self.running:
                return False
            self.set_status(f"Status: Station {station_number} - In progress")
            self.update_timer(t)
            time.sleep(1)
        return self.running

    def run_break(self):
        if not self.running:
            return False
        self.set_status("Status: Break - Move to next station")

        played = self.play_audio(AUDIO_MOVE, "move-to-next-station")
        if not played and not self.running:
            return False

        return self.run_countdown(BREAK_TIME, "Status: Next station in")

    def exam_flow(self):
        if not self.play_instructions():
            return

        station_count = 1

        while self.running:
            self.set_status(f"Status: Station {station_count} - Ready")

            if not self.countdown_to_start():
                break

            if not self.run_station_timer(station_count):
                break

            if not self.running:
                break

            self.set_status(f"Status: Station {station_count} - STOP")
            played_stop = self.play_audio(AUDIO_STOP, "stop")
            if not played_stop and self.running:
                self.speak("Stop")

            if not self.run_break():
                break

            station_count += 1


# ---------- RUN APP ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = ExamTimerApp(root)
    root.mainloop()
