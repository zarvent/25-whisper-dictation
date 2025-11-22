import asyncio
import threading
from PySide6.QtCore import QObject, Signal, Slot, Property
from v2m.sdk import V2MClient
from v2m.core.logging import logger

class Bridge(QObject):
    # Signals to notify QML of state changes
    isRecordingChanged = Signal()
    isProcessingChanged = Signal()
    audioLevelChanged = Signal()
    transcriptionReceived = Signal(str)
    errorOccurred = Signal(str)

    def __init__(self):
        super().__init__()
        self._client = V2MClient()
        self._is_recording = False
        self._is_processing = False
        self._audio_level = 0.0

        # Background loop for async client operations
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        # Connect to daemon on startup
        self._run_async(self._connect_client())

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _run_async(self, coro):
        asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def _connect_client(self):
        try:
            connected = await self._client.connect()
            if connected:
                logger.info("Bridge connected to Daemon")
            else:
                logger.error("Bridge failed to connect to Daemon")
                self.errorOccurred.emit("Could not connect to Daemon")
        except Exception as e:
            logger.error(f"Bridge connection error: {e}")
            self.errorOccurred.emit(str(e))

    # --- Properties ---

    @Property(bool, notify=isRecordingChanged)
    def isRecording(self):
        return self._is_recording

    @Property(bool, notify=isProcessingChanged)
    def isProcessing(self):
        return self._is_processing

    @Property(float, notify=audioLevelChanged)
    def audioLevel(self):
        return self._audio_level

    # --- Slots (Methods callable from QML) ---

    @Slot()
    def startCapture(self):
        """Start smart capture (VAD-based recording)"""
        if self._is_recording or self._is_processing:
            return

        self._is_recording = True
        self.isRecordingChanged.emit()
        self._run_async(self._do_smart_capture())

    @Slot()
    def stopCapture(self):
        """Stop is not needed in smart capture mode, but kept for compatibility"""
        pass

    async def _do_smart_capture(self):
        """Execute smart capture: records until silence, then transcribes"""
        try:
            # The transcribe method now uses SmartCaptureCommand via daemon
            # It will record until VAD detects silence
            result = await self._client.transcribe(use_llm=True)
            text = result.get("text", "")
            self.transcriptionReceived.emit(text)
        except Exception as e:
            logger.error(f"Smart capture failed: {e}")
            self.errorOccurred.emit(str(e))
        finally:
            self._is_recording = False
            self.isRecordingChanged.emit()

    @Slot()
    def toggleSettings(self):
        # TODO: Implement settings toggle logic or emit signal to open window
        pass
