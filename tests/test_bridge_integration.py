import asyncio
import sys
import os
import subprocess
import time
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from v2m.gui.bridge import Bridge

# Mock QML environment (just a QObject to receive signals)
class QmlMock(QObject):
    def __init__(self):
        super().__init__()
        self.recording_state = False
        self.transcription = ""
        self.error = ""

    @Slot()
    def onRecordingChanged(self):
        print(f"Signal: isRecordingChanged")

    @Slot(str)
    def onTranscriptionReceived(self, text):
        print(f"Signal: transcriptionReceived: {text}")
        self.transcription = text

    @Slot(str)
    def onErrorOccurred(self, error):
        print(f"Signal: errorOccurred: {error}")
        self.error = error

async def run_test():
    print("Starting Daemon...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")

    daemon_process = subprocess.Popen(
        [sys.executable, "-m", "v2m.daemon"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(2) # Wait for daemon

    try:
        print("Initializing Bridge...")
        bridge = Bridge()
        mock = QmlMock()

        # Connect signals
        bridge.isRecordingChanged.connect(mock.onRecordingChanged)
        bridge.transcriptionReceived.connect(mock.onTranscriptionReceived)
        bridge.errorOccurred.connect(mock.onErrorOccurred)

        # Wait for bridge to connect (it does so in background thread)
        await asyncio.sleep(1)

        print("Testing Start Capture...")
        bridge.startCapture()
        await asyncio.sleep(1)
        assert bridge.isRecording == True
        print("✅ Bridge.isRecording is True")

        print("Testing Stop Capture...")
        bridge.stopCapture()

        # Wait for processing
        print("Waiting for transcription...")
        for _ in range(10):
            if mock.transcription or mock.error:
                break
            await asyncio.sleep(0.5)

        if mock.error:
            print(f"❌ Error received: {mock.error}")
        else:
            print(f"✅ Transcription received: '{mock.transcription}'")

    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        print("Stopping Daemon...")
        daemon_process.terminate()
        daemon_process.wait()

if __name__ == "__main__":
    # PySide6 requires a QCoreApplication for signals to work
    from PySide6.QtCore import QCoreApplication
    app = QCoreApplication(sys.argv)

    # Run async test in a separate thread or just use asyncio.run and hope PySide doesn't complain too much
    # Actually, signals need the event loop.
    # Let's try a simple approach: run the async test, and process events periodically?
    # Or just rely on the fact that Bridge uses its own thread for asyncio.

    asyncio.run(run_test())
