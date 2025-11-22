import time
import numpy as np
import torch
from v2m.infrastructure.vad_service import VADService
from v2m.infrastructure.audio.recorder import AudioRecorder
import logging

# Setup logging to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("v2m")
logger.setLevel(logging.DEBUG)

def test_vad_loop():
    vad_service = VADService()
    print("Loading VAD...")
    vad_service.load_model()
    iterator = vad_service.create_iterator(min_silence_duration_ms=500)

    if not iterator:
        print("Failed to create iterator")
        return

    recorder = AudioRecorder()

    def callback(chunk):
        try:
            # print(f"Chunk: {chunk.shape}")
            speech_dict = iterator(torch.from_numpy(chunk), return_seconds=True)
            if speech_dict:
                print(f"VAD Event: {speech_dict}")
        except Exception as e:
            print(f"Error: {e}")

    print("Starting recorder (speak now)...")
    recorder.start(chunk_callback=callback)
    time.sleep(5)
    print("Stopping recorder...")
    recorder.stop()
    print("Done.")

if __name__ == "__main__":
    test_vad_loop()
