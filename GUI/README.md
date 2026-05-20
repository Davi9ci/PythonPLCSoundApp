# TwinCAT ADS Sound Player

A lightweight Windows desktop application that listens to a **TwinCAT 3 PLC** via ADS and plays WAV audio files in response to PLC variable changes. Designed for industrial HMI setups where audio alerts must remain active even when the HMI web client is closed.

---

## The Problem

TwinCAT HMI's built-in audio feature plays sound through the browser — meaning if the HMI client is closed, no audio plays. This application solves that by running as a standalone process on the Windows host, independent of any HMI session.

---

## How It Works

```
TwinCAT 3 PLC
    │
    │  bSound = TRUE / FALSE     → triggers looping playback or stops it
    │  nSoundSelect = 1 / 2 / 3  → selects which WAV file to play
    │
    └──── ADS ────► ADS Sound Player (this app) ────► Windows Audio
```

The app subscribes to PLC variable changes via ADS notifications — TwinCAT pushes updates instantly, no polling required. Audio plays through the standard Windows audio session, so it works regardless of HMI state.

---

## Features

- GUI configuration — no editing config files manually
- ADS connection test with live status indicator
- Select up to 3 WAV files with browse + preview per sound
- Looping playback while `bSound = TRUE`, stops immediately on `FALSE`
- Switch sounds at runtime via `nSoundSelect`
- Settings auto-saved to `config.ini` next to the executable
- Timestamped log panel for diagnostics
- Can be packaged as a standalone `.exe` (no Python required on target PC)

---

## Requirements

### On the development machine (to build)
- Python 3.8+
- [pyads](https://github.com/stlehmann/pyads) — `pip install pyads`
- [PyInstaller](https://pyinstaller.org) — `pip install pyinstaller` (for building the exe)

### On the target / customer machine
- Windows 10 or 11
- TwinCAT 3 runtime (ADS router must be running)
- A logged-in Windows user session (required for audio access)
- No Python needed if using the compiled `.exe`

---

## PLC Setup

Declare these two variables in your PLC program (e.g. in `MAIN`):

```iecst
VAR
    bSound       : BOOL;    (* TRUE = play sound, FALSE = stop *)
    nSoundSelect : INT := 1; (* 1, 2, or 3 — selects the WAV file *)
END_VAR
```

Variable names are configurable in the app — the defaults above match the app's defaults.

---

## Installation & Usage

### Running from source

```powershell
pip install pyads
python ads_listener_gui.py
```

### First-time configuration

1. Enter the **AMS Net ID** of the TwinCAT machine
   - Find it in TwinCAT: system tray icon → Properties, or XAE → System → Settings
   - For the local machine, `127.0.0.1.1.1` usually works
2. Click **Test Connection** — confirm it shows green
3. Enter the PLC variable names (default: `MAIN.bSound` / `MAIN.nSoundSelect`)
4. Browse to your WAV files for sounds 1, 2, and 3
5. Click **▶ Test** on each sound to verify playback
6. Click **Save Config** then **▶ Start Listener**

---

## Building a Standalone Exe

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --name SoundPlayer ads_listener_gui.py
```

The compiled executable appears in the `dist\` folder. Copy it alongside `config.ini` and your WAV files.

---

## Deployment Package (for customers)

```
SoundPlayer\
├── SoundPlayer.exe     ← compiled application
├── config.ini          ← created automatically on first Save
└── sounds\
    ├── 1.wav
    ├── 2.wav
    └── 3.wav
```

To auto-start on Windows boot, add `SoundPlayer.exe` to **Windows Task Scheduler**:
- Trigger: At log on
- Action: Run `SoundPlayer.exe`
- Run as: the logged-in user account (required for audio)

---

## Config File Reference

`config.ini` is created automatically on first save. It can also be edited manually:

```ini
[ADS]
ams_net_id = 127.0.0.1.1.1
port = 851

[PLC]
var_sound  = MAIN.bSound
var_select = MAIN.nSoundSelect

[Sounds]
sound_1 = C:\path\to\1.wav
sound_2 = C:\path\to\2.wav
sound_3 = C:\path\to\3.wav
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Connection test fails (error 6) | TwinCAT not in Run mode | Set TwinCAT to Run, ensure PLC is started |
| Connection test fails (error 1808) | Wrong variable name | Check exact name and case in PLC |
| Sound plays a system beep | WAV file not found or MP3 used | Verify path; only PCM WAV is supported |
| No sound at all | App running as SYSTEM | Ensure Task Scheduler runs as logged-in user |
| App crashes on startup | TwinCAT not ready | Add a delay or start the app after TwinCAT |

---

## Notes

- Only **PCM WAV** files are supported. MP3 files will not play correctly — convert them first using Audacity or any online converter.
- `nSoundSelect` changes take effect on the next trigger of `bSound`. If a sound is already playing and you change the selection, it will continue until stopped.
- The ADS port `851` is the default for TwinCAT 3 PLC runtime 1. Use `852` for runtime 2, and so on.

---

## License

Internal / customer use. Not for redistribution.
