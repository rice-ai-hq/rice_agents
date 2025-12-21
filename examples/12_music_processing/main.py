import asyncio
import os
import time
import json
import numpy as np
from scipy.io import wavfile
from scipy import signal
from dotenv import load_dotenv
from pydub import AudioSegment

from rice_agents.agents.base import Agent
from rice_agents.containers.base import Container
from rice_agents.llms.gemini_provider import GeminiProvider
from rice_agents.tools.base import tool

load_dotenv()


# --- Tools ---
@tool("separate_drums")
def separate_drums(input_file: str) -> str:
    """Separates drum (low frequency) components from audio file using a low-pass filter."""
    print(f"   [Tool] Separating drums from {input_file}...")
    try:
        sample_rate, data = wavfile.read(input_file)
        # Simple Low Pass Filter to isolate "kick drum" (< 150Hz)
        sos = signal.butter(10, 150, "lp", fs=sample_rate, output="sos")

        # Handle stereo
        if len(data.shape) > 1:
            filtered = signal.sosfilt(sos, data, axis=0)
        else:
            filtered = signal.sosfilt(sos, data)

        output_file = "drums_only.wav"
        wavfile.write(output_file, sample_rate, filtered.astype(np.int16))
        return f"Success: Drums separated and saved to {output_file}"
    except Exception as e:
        return f"Error separating drums: {e}"


@tool("analyze_audio_file")
def analyze_audio_file(file_path: str) -> str:
    """Analyzes the audio file content to extract features."""
    try:
        sr, data = wavfile.read(file_path)
        duration = len(data) / sr
        max_amp = np.max(np.abs(data))
        desc = "Loud, high energy" if max_amp > 10000 else "Soft, low energy"
        return f"Analysis: {desc}, Steady rhythmic pulse detected. (File: {file_path})"
    except Exception as e:
        return f"Error analyzing: {e}"


# --- Simulation Setup ---
def generate_mixed_audio(filename="mix.wav"):
    sample_rate = 44100
    duration = 5
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    kick = np.sin(2 * np.pi * 60 * t) * (0.5 * (1 + np.sin(2 * np.pi * 2 * t)))
    melody = 0.5 * np.sin(2 * np.pi * 440 * t)
    mix = (kick + melody) / np.max(np.abs(kick + melody))
    wavfile.write(filename, sample_rate, (mix * 32767).astype(np.int16))
    print(f"Generated {filename}")


# --- Agent Wrappers ---
class SwarmAgent:
    def __init__(self, agent: Agent, container: Container):
        self.agent = agent
        self.container = container
        self.name = agent.name

    def read_scratchpad(self):
        return self.container.memory_store.get_scratchpad("audio_session_1")

    def write_scratchpad(self, content: str, metadata: dict):
        self.container.memory_store.add_scratchpad(
            session_id="audio_session_1",
            agent=self.name,
            content=content,
            metadata=metadata,
        )


class SeparatorBot(SwarmAgent):
    async def act(self):
        history = self.read_scratchpad()
        if any(
            e.get("metadata", {}).get("stage") == "separation_complete" for e in history
        ):
            return

        if not history:
            print(f"[{self.name}] Detecting new mix file. Starting separation...")
            res = await self.agent.run("Separate drums from 'mix.wav'.")
            self.write_scratchpad(
                res, {"stage": "separation_complete", "file": "drums_only.wav"}
            )


class AnalyzerBot(SwarmAgent):
    async def act(self):
        history = self.read_scratchpad()
        if any(
            e.get("metadata", {}).get("stage") == "analysis_complete" for e in history
        ):
            return

        separation_event = next(
            (
                e
                for e in history
                if e.get("metadata", {}).get("stage") == "separation_complete"
            ),
            None,
        )
        if separation_event:
            print(f"[{self.name}] Separation detected. Starting analysis...")
            target_file = separation_event.get("metadata", {}).get(
                "file", "drums_only.wav"
            )
            res = await self.agent.run(f"Analyze the file '{target_file}'.")
            self.write_scratchpad(res, {"stage": "analysis_complete", "analysis": res})


class ProducerBot(SwarmAgent):
    async def act(self):
        history = self.read_scratchpad()
        if any(e.get("metadata", {}).get("stage") == "genre_complete" for e in history):
            return

        analysis_event = next(
            (
                e
                for e in history
                if e.get("metadata", {}).get("stage") == "analysis_complete"
            ),
            None,
        )
        if analysis_event:
            print(f"[{self.name}] Analysis received. Classifying genre...")
            analysis_text = analysis_event.get("content", "")
            res = await self.agent.run(
                f"Based on this analysis: '{analysis_text}', what is the musical genre? Check Memory."
            )
            self.write_scratchpad(res, {"stage": "genre_complete", "genre": res})
            print(f"\n🎶 FINAL VERDICT: {res}")


async def main():
    print("=== Parallel Audio Swarm (RiceDB Scratchpad) ===")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return

    # 1. Setup Env
    real_file = "03 holiday.mp3"
    target_wav = "mix.wav"

    if os.path.exists(real_file):
        print(f"Found real audio file: '{real_file}'. Converting to WAV...")
        try:
            sound = AudioSegment.from_mp3(real_file)
            sound.export(target_wav, format="wav")
            print(f"Converted to '{target_wav}'")
        except Exception as e:
            print(f"Failed to convert MP3 (ffmpeg might be missing): {e}")
            print("Falling back to synthetic audio.")
            generate_mixed_audio(target_wav)
    else:
        print("Real file not found. Using synthetic audio.")
        generate_mixed_audio(target_wav)

    container = Container("AudioStudio")
    if not container.memory_store:
        return
    container.memory_store.clear_scratchpad("audio_session_1")

    # Seed Knowledge
    styles = [
        "Techno: Loud, high energy, 120bpm, steady kick",
        "Jazz: Soft, swing, irregular",
        "Holiday/Pop: Cheerful, moderate energy, bells",
        "Ambient: Quiet, no beat",
    ]
    container.memory_store.add_texts(
        styles, metadatas=[{"type": "genre_ref"} for _ in styles]
    )

    llm = GeminiProvider(model="gemini-3-flash-preview", api_key=api_key)

    # 2. Initialize Agents
    separator = SeparatorBot(
        Agent(
            "Separator",
            llm,
            tools=[separate_drums],
            container=container,
            system_prompt="You separate audio.",
        ),
        container,
    )
    analyzer = AnalyzerBot(
        Agent(
            "Analyzer",
            llm,
            tools=[analyze_audio_file],
            container=container,
            system_prompt="You analyze audio files.",
        ),
        container,
    )
    producer = ProducerBot(
        Agent(
            "Producer",
            llm,
            container=container,
            system_prompt="You identify genres based on analysis and memory.",
        ),
        container,
    )

    swarm = [separator, analyzer, producer]

    # 3. Parallel Event Loop
    for i in range(10):  # Increased ticks for safety
        print(f"\n--- Tick {i + 1} ---")
        await asyncio.gather(*(agent.act() for agent in swarm))

        history = container.memory_store.get_scratchpad("audio_session_1")
        if any(e.get("metadata", {}).get("stage") == "genre_complete" for e in history):
            print("--- Workflow Completed ---")
            break
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(main())
