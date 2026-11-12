# audio-visualizer

A system sound visualizer for Windows. It draws a 20-band, LED-style spectrum grid on a dedicated display and only appears when Spotify is playing and you're not using that monitor.

## Features

- **Real-time spectrum**: captures audio from an input device, runs an FFT, and renders 20 logarithmically spaced frequency bands (40 Hz to 16 kHz) as a 20x14 grid of cells.
- **Smooth motion**: bars rise instantly and fall gradually.
- **Now playing**: shows the current Spotify track at the bottom of the screen, read from the Spotify window title.
- **Auto show/hide**: fades in when music is playing and you've been away from the visualizer's monitor for a few seconds. Hides when Spotify is idle or you return to that monitor.
- **Stays out of the way**: hidden from Alt+Tab and the taskbar, shown topmost without stealing focus.
- **Runs at login**: optional startup shortcut and a script to stop it.

## Requirements

- Windows (uses the Win32 API through `ctypes`)
- Python 3.x
- Spotify desktop app (for now-playing detection)
- An audio input device that carries system audio (for example a loopback or virtual cable device)

Python dependencies are listed in `requirements.txt`:

```
numpy
psutil
pygame
sounddevice
```

## Setup

1. Create a virtual environment and install dependencies. The startup script expects it at `C:\venvs\audio-visualizer`:

   ```powershell
   python -m venv C:\venvs\audio-visualizer
   C:\venvs\audio-visualizer\Scripts\pip install -r requirements.txt
   ```

2. Find your audio device index:

   ```powershell
   C:\venvs\audio-visualizer\Scripts\python -c "import sounddevice as sd; print(sd.query_devices())"
   ```

3. Open `main.py` and set the constants at the top:

   | Constant | Meaning |
   | --- | --- |
   | `DEVICE` | Index of the audio input device to capture |
   | `DISPLAY` | Index of the monitor to show the visualizer on |
   | `IDLE_DELAY` | Seconds you must be away from the monitor before it appears |
   | `FADE_SECONDS` | Fade-in duration |
   | `WIDTH`, `HEIGHT` | Render resolution (default 800x480) |
   | `COLS`, `ROWS` | Grid size (default 20x14) |

## Usage

Run it:

```powershell
C:\venvs\audio-visualizer\Scripts\python main.py
```

Use `pythonw.exe` instead of `python.exe` to run without a console window.

### Controls

| Input | Action |
| --- | --- |
| `Ctrl` + `Alt` + `V` | Enable / disable the visualizer globally |

## Run at startup

```powershell
.\install_startup.ps1
```

This creates an `Audio Visualizer.lnk` shortcut in your Startup folder that launches `main.py` with the venv's `pythonw.exe`.

To stop a running instance:

```powershell
.\stop.ps1
```

## How it works

- `main.py`: audio capture, FFT and band calculation, grid rendering, and the main loop with visibility logic.
- `spotify.py`: finds Spotify windows by process name and reads the title. A title containing ` - ` that isn't one of the idle titles counts as "now playing". Run it directly to debug detection.
- `monitor.py`: Win32 helpers for per-monitor presence detection (foreground window and cursor), showing and hiding the window, opacity, Alt+Tab hiding, and the global hotkey.
- `install_startup.ps1` / `stop.ps1`: startup shortcut creation and process shutdown.

## Tuning

Adjust these in `main.py` to change the look and response:

- `DB_FLOOR` / `DB_CEIL`: the decibel range mapped to the grid height
- `TILT_DB`: boosts higher frequencies, which are naturally quieter
- `FALL_SPEED`: how quickly bars drop
- `FFT_SIZE`: frequency resolution versus responsiveness
- `LIGHT_GRAY` / `DARK_GRAY` / `OFF_COLOR`: cell colors