"""
Tests de resiliencia para los command handlers según el V2M QA Manifesto.
Tests de "No Happy Path" - Por cada test de éxito, al menos 2 de fallo.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from v2m.application.command_handlers import StartRecordingHandler, StopRecordingHandler, ProcessTextHandler
from v2m.application.commands import StartRecordingCommand, StopRecordingCommand, ProcessTextCommand
from v2m.domain.errors import RecordingError, LLMError, MicrophoneNotFoundError


@pytest.fixture
def mock_transcription_service():
    """Mock del servicio de transcripción."""
    return MagicMock()


@pytest.fixture
def mock_llm_service():
    """Mock del servicio LLM."""
    return MagicMock()


@pytest.fixture
def mock_notification_service():
    """Mock del servicio de notificaciones."""
    return MagicMock()


@pytest.fixture
def mock_clipboard_service():
    """Mock del servicio de portapapeles."""
    return MagicMock()


class TestStartRecordingHandler:
    """Tests para StartRecordingHandler."""

    @pytest.mark.asyncio
    async def test_start_recording_success(self, mock_transcription_service, mock_notification_service):
        """Happy Path: grabación inicia correctamente."""
        handler = StartRecordingHandler(mock_transcription_service, mock_notification_service)
        
        await handler.handle(StartRecordingCommand())
        
        mock_transcription_service.start_recording.assert_called_once()
        mock_notification_service.notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_recording_already_in_progress(self, mock_transcription_service, mock_notification_service):
        """Edge Case: intento de iniciar grabación cuando ya hay una en progreso."""
        mock_transcription_service.start_recording.side_effect = RecordingError("grabación ya en progreso")
        handler = StartRecordingHandler(mock_transcription_service, mock_notification_service)
        
        with pytest.raises(RecordingError):
            await handler.handle(StartRecordingCommand())

    @pytest.mark.asyncio
    async def test_start_recording_microphone_not_found(self, mock_transcription_service, mock_notification_service):
        """Edge Case: micrófono no disponible."""
        mock_transcription_service.start_recording.side_effect = MicrophoneNotFoundError("No se detectó micrófono")
        handler = StartRecordingHandler(mock_transcription_service, mock_notification_service)
        
        with pytest.raises(MicrophoneNotFoundError):
            await handler.handle(StartRecordingCommand())


class TestStopRecordingHandler:
    """Tests para StopRecordingHandler."""

    @pytest.mark.asyncio
    async def test_stop_recording_success(self, mock_transcription_service, mock_notification_service, mock_clipboard_service):
        """Happy Path: transcripción exitosa."""
        mock_transcription_service.stop_and_transcribe.return_value = "Texto transcrito correctamente"
        handler = StopRecordingHandler(mock_transcription_service, mock_notification_service, mock_clipboard_service)
        
        await handler.handle(StopRecordingCommand())
        
        mock_clipboard_service.copy.assert_called_once_with("Texto transcrito correctamente")
        assert mock_notification_service.notify.call_count == 2

    @pytest.mark.asyncio
    async def test_stop_recording_empty_transcription(self, mock_transcription_service, mock_notification_service, mock_clipboard_service):
        """Edge Case: audio grabado sin voz (transcripción vacía)."""
        mock_transcription_service.stop_and_transcribe.return_value = ""
        handler = StopRecordingHandler(mock_transcription_service, mock_notification_service, mock_clipboard_service)
        
        await handler.handle(StopRecordingCommand())
        
        mock_clipboard_service.copy.assert_not_called()
        mock_notification_service.notify.assert_called_with("❌ Whisper", "No se detectó voz en el audio")

    @pytest.mark.asyncio
    async def test_stop_recording_zero_duration_audio(self, mock_transcription_service, mock_notification_service, mock_clipboard_service):
        """Edge Case: audio de 0 segundos."""
        mock_transcription_service.stop_and_transcribe.side_effect = RecordingError("no se grabó audio o el buffer está vacío")
        handler = StopRecordingHandler(mock_transcription_service, mock_notification_service, mock_clipboard_service)
        
        with pytest.raises(RecordingError):
            await handler.handle(StopRecordingCommand())

    @pytest.mark.asyncio
    async def test_stop_recording_no_active_recording(self, mock_transcription_service, mock_notification_service, mock_clipboard_service):
        """Edge Case: detener grabación cuando no hay ninguna activa."""
        mock_transcription_service.stop_and_transcribe.side_effect = RecordingError("no hay grabación en curso")
        handler = StopRecordingHandler(mock_transcription_service, mock_notification_service, mock_clipboard_service)
        
        with pytest.raises(RecordingError):
            await handler.handle(StopRecordingCommand())


class TestProcessTextHandler:
    """Tests para ProcessTextHandler."""

    @pytest.mark.asyncio
    async def test_process_text_success_async(self, mock_llm_service, mock_notification_service, mock_clipboard_service):
        """Happy Path: procesamiento exitoso con LLM async."""
        mock_llm_service.process_text = AsyncMock(return_value="Texto refinado por el LLM")
        handler = ProcessTextHandler(mock_llm_service, mock_notification_service, mock_clipboard_service)
        
        await handler.handle(ProcessTextCommand("texto original"))
        
        mock_clipboard_service.copy.assert_called_once_with("Texto refinado por el LLM")

    @pytest.mark.asyncio
    async def test_process_text_llm_failure_fallback(self, mock_llm_service, mock_notification_service, mock_clipboard_service):
        """Edge Case: fallo del LLM debe usar texto original como fallback."""
        mock_llm_service.process_text = AsyncMock(side_effect=LLMError("Error de conexión con Gemini"))
        handler = ProcessTextHandler(mock_llm_service, mock_notification_service, mock_clipboard_service)
        
        await handler.handle(ProcessTextCommand("texto original"))
        
        # Debe copiar el texto original como fallback
        mock_clipboard_service.copy.assert_called_with("texto original")
        # Debe notificar el fallo
        assert any("Gemini Falló" in str(call) for call in mock_notification_service.notify.call_args_list)

    @pytest.mark.asyncio
    async def test_process_text_extremely_long_text(self, mock_llm_service, mock_notification_service, mock_clipboard_service):
        """Edge Case: texto de 10,000 caracteres."""
        long_text = "a" * 10000
        mock_llm_service.process_text = AsyncMock(return_value="Resumen del texto largo")
        handler = ProcessTextHandler(mock_llm_service, mock_notification_service, mock_clipboard_service)
        
        await handler.handle(ProcessTextCommand(long_text))
        
        mock_llm_service.process_text.assert_called_once_with(long_text)

    @pytest.mark.asyncio
    async def test_process_text_empty_string(self, mock_llm_service, mock_notification_service, mock_clipboard_service):
        """Edge Case: string vacío."""
        mock_llm_service.process_text = AsyncMock(return_value="")
        handler = ProcessTextHandler(mock_llm_service, mock_notification_service, mock_clipboard_service)
        
        await handler.handle(ProcessTextCommand(""))
        
        mock_llm_service.process_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_text_special_characters(self, mock_llm_service, mock_notification_service, mock_clipboard_service):
        """Edge Case: texto con caracteres especiales y emojis."""
        special_text = "Texto con émojis 🚀 y símbolos especiales: @#$%^&*()"
        mock_llm_service.process_text = AsyncMock(return_value=special_text)
        handler = ProcessTextHandler(mock_llm_service, mock_notification_service, mock_clipboard_service)
        
        await handler.handle(ProcessTextCommand(special_text))
        
        mock_clipboard_service.copy.assert_called_once()
