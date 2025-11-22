import pytest
from v2m.config import Settings

def test_config_loading():
    """Test that configuration loads correctly."""
    config = Settings()
    # The config.toml overrides the defaults in Settings class
    assert config.whisper.model == "large-v3-turbo"
    # language is set to "auto" in config.toml, but "es" in Settings default
    assert config.whisper.language == "auto"
    assert config.gemini.retry_attempts == 3
