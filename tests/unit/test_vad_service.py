import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from v2m.infrastructure.vad_service import VADService

@pytest.fixture
def vad_service():
    service = VADService()
    # Properly mock the model as loaded
    service.model = MagicMock()
    service.disabled = False
    return service

def test_vad_process_empty_audio(vad_service):
    """Test processing empty audio returns empty array."""
    empty_audio = np.array([], dtype=np.float32)
    result = vad_service.process(empty_audio)

    assert result.size == 0

def test_vad_process_no_speech(vad_service):
    """Test processing audio with no speech returns empty array."""
    # Mock get_speech_timestamps to return no speech segments
    vad_service.get_speech_timestamps = MagicMock(return_value=[])

    # 1 second of silence
    audio = np.zeros(16000, dtype=np.float32)
    result = vad_service.process(audio)

    assert result.size == 0

def test_vad_process_with_speech(vad_service):
    """Test processing audio with speech returns concatenated segments."""
    # Mock timestamps: speech from 1000-2000 and 3000-4000
    vad_service.get_speech_timestamps = MagicMock(return_value=[
        {'start': 1000, 'end': 2000},
        {'start': 3000, 'end': 4000}
    ])

    # Create dummy audio
    audio = np.arange(5000, dtype=np.float32)

    result = vad_service.process(audio)

    # Expected size: (2000-1000) + (4000-3000) = 1000 + 1000 = 2000
    assert result.size == 2000
    # Verify content
    expected = np.concatenate([audio[1000:2000], audio[3000:4000]])
    np.testing.assert_array_equal(result, expected)

def test_vad_disabled_returns_original_audio():
    """Test that disabled VAD returns original audio unchanged."""
    service = VADService()
    service.disabled = True
    
    audio = np.arange(1000, dtype=np.float32)
    result = service.process(audio)
    
    np.testing.assert_array_equal(result, audio)

def test_vad_model_not_loaded_returns_original_audio():
    """Test that VAD without loaded model returns original audio."""
    service = VADService()
    service.model = None
    service.disabled = False
    
    # Mock load_model to fail
    with patch.object(service, 'load_model', side_effect=Exception("Model load failed")):
        audio = np.arange(1000, dtype=np.float32)
        result = service.process(audio)
        
        # Should return original audio as fallback
        np.testing.assert_array_equal(result, audio)
