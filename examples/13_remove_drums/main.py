import asyncio
import os
import numpy as np
from scipy.io import wavfile
from scipy import signal
from pydub import AudioSegment
from dotenv import load_dotenv
from rice_agents.agents.base import Agent
from rice_agents.containers.base import Container
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.tools.base import tool

load_dotenv()


# --- Tools ---
@tool("remove_drums")
def remove_drums(input_file: str) -> str:
    """Removes drum sounds (low frequency) from audio using a high-pass filter to keep only melody/vocals."""
    print(f"   [Tool] Removing drums from {input_file}...")
    try:
        sample_rate, data = wavfile.read(input_file)

        # High Pass Filter to remove kick/bass (< 250Hz)
        sos = signal.butter(10, 250, "hp", fs=sample_rate, output="sos")

        # Handle stereo
        if len(data.shape) > 1:
            filtered = signal.sosfilt(sos, data, axis=0)
        else:
            filtered = signal.sosfilt(sos, data)

        output_file = "melody_only.wav"
        wavfile.write(output_file, sample_rate, filtered.astype(np.int16))
        return f"Success: Drums removed. Melody saved to {output_file}"
    except Exception as e:
        return f"Error removing drums: {e}"


@tool("analyze_audio_file")
def analyze_audio_file(file_path: str) -> str:
    """Analyzes the audio file content."""
    try:
        sr, data = wavfile.read(file_path)
        duration = len(data) / sr
        max_amp = np.max(np.abs(data))
        return f"Analysis: Duration: {duration:.2f}s, Max Amp: {max_amp}. (File: {file_path})"
    except Exception as e:
        return f"Error analyzing: {e}"


# --- Setup ---
def setup_audio():
    real_file = "03 holiday.mp3"
    target_wav = "mix.wav"

    if os.path.exists(real_file):
        print(f"Found real audio file: '{real_file}'. Converting to WAV...")
        try:
            sound = AudioSegment.from_mp3(real_file)
            sound.export(target_wav, format="wav")
            print(f"Converted to '{target_wav}'")
            return target_wav
        except Exception as e:
            print(f"Failed to convert MP3: {e}")
            return None

    # Fallback synthetic
    print("Generating synthetic mix...")
    sample_rate = 44100
    duration = 5
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Drums
    kick = np.sin(2 * np.pi * 60 * t) * (0.5 * (1 + np.sin(2 * np.pi * 2 * t)))
    # Melody
    melody = 0.3 * np.sin(2 * np.pi * 440 * t) + 0.3 * np.sin(2 * np.pi * 550 * t)
    mix = (kick + melody) / np.max(np.abs(kick + melody))
    wavfile.write(target_wav, sample_rate, (mix * 32767).astype(np.int16))
    return target_wav


async def main():
    print("=== Melody Extraction Agent (No Drums) ===")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return

    target_file = setup_audio()
    if not target_file:
        return

    llm = GeminiProvider(model="gemini-3-flash-preview", api_key=api_key)
    container = Container("AudioStudio")

    agent = Agent(
        name="MelodyExtractor",
        llm=llm,
        tools=[remove_drums, analyze_audio_file],
        system_prompt="You are a sound engineer specialized in isolating melodies. Remove drums from the input file.",
        container=container,
    )

    task = f"Remove the drums from '{target_file}' so I can hear the melody clearly. Analyze the result."
    print(f"\nUser: {task}")
    response = await agent.run(task)
    print(f"Agent: {response}")


if __name__ == "__main__":
    asyncio.run(main())
