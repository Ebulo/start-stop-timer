# AIIMS Auto Timer

Tkinter-based exam timer with pre-recorded audio prompts.

## Run from source

1. Create/activate a virtual environment
2. Install deps: `pip install -r requirements.txt`
3. Run: `python exam_timer_app.py`

Audio files must be present in `audios/` (next to `exam_timer_app.py`):
- `audios/instructions.mp3`
- `audios/start.mp3`
- `audios/stop.mp3`
- `audios/move-to-next-station.mp3`

## Build Windows EXE (with audio)

On a Windows machine, from the repo root:

- Double-click `build_windows.bat`, or run it from `cmd`.

Output:
- `dist\ExamTimer.exe`
- `dist\audios\` (copied automatically)

Distribute the contents of `dist\` together.
