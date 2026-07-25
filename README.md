# Fedora Voice Agent

A bi-directional AI voice assistant for Fedora Linux (Wayland), powered by Groq Llama 3, Whisper, and Orpheus.

## Features
- **Wake Word Detection**: Energy-based (Triggers on loud voice/phrases).
- **Natural Conversation**: Fast responses using Llama 3 70B and Orpheus TTS.
- **System Control**: Execute shell commands, control apps, and manage files.
- **Wayland Native**: Designed for Fedora Workstation (GNOME).
- **Privacy Focused**: Local wake word, configurable permissions.

## Installation

1. **Run the setup script**:
   ```bash
   ./setup.sh
   # Follow prompts to authorize permissions
   ```

2. **Configure API Keys**:
   Copy the example environment file and add your keys:
   ```bash
   cp .env.example .env
   nano .env
   ```
   *Required Keys:*
   - `GROQ_API_KEY`: For STT, LLM, and TTS.
   - *(No other keys required. Wake word is now energy-based)*

3. **Run the Agent**:
   ```bash
   python3 main.py
   ```

## Usage
- Say "Hey Assistant" (or your configured wake word).
- Wait for the orb to turn blue (Listening).
- Speak your command (e.g., "Open Firefox", "What time is it?", "Play some music").
- The agent will process and respond.

## Structure
- `src/core`: Configuration and state.
- `src/voice`: Audio pipeline (STT, TTS, VAD).
- `src/brain`: Intelligence (LLM, Prompts).
- `src/execution`: Command execution and safety.
- `src/gui`: PyQt6 interface.

## Troubleshooting
- **Audio Issues**: Ensure PipeWire is running and `pavucontrol` shows valid input/output.
- **Wayland Issues**: If the overlay doesn't appear, check `gtk-layer-shell` support.
- **Permission Errors**: Ensure your user is in the `input` group for `ydotool`.

## License
MIT License
