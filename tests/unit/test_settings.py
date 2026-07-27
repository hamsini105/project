"""Unit tests for core.settings.Settings."""

from __future__ import annotations

import pytest

from core.settings import Settings, get_settings


class TestSettingsDefaults:
    def test_default_environment(self):
        s = Settings()
        assert s.environment == "development"

    def test_default_log_level(self):
        s = Settings()
        assert s.log_level == "INFO"

    def test_default_log_format(self):
        s = Settings()
        assert s.log_format == "text"

    def test_debug_defaults_to_false(self):
        s = Settings()
        assert s.debug is False

    def test_max_upload_size_default(self):
        s = Settings()
        assert s.max_upload_size_mb == 10

    def test_embedding_model_default(self):
        s = Settings()
        assert s.embedding_model_name == "all-MiniLM-L6-v2"


class TestSettingsFromEnv:
    def test_log_level_from_env(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "debug")
        s = Settings()
        # Validator should uppercase it
        assert s.log_level == "DEBUG"

    def test_environment_from_env(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        s = Settings()
        assert s.environment == "production"

    def test_debug_from_env(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "true")
        s = Settings()
        assert s.debug is True

    def test_invalid_environment_raises(self):
        with pytest.raises(Exception):
            Settings(environment="unknown")  # type: ignore[arg-type]


class TestComputedProperties:
    def test_is_production_true(self):
        s = Settings(environment="production")
        assert s.is_production is True

    def test_is_production_false(self):
        s = Settings(environment="development")
        assert s.is_production is False

    def test_is_development(self):
        s = Settings(environment="development")
        assert s.is_development is True

    def test_max_upload_bytes(self):
        s = Settings(max_upload_size_mb=5)
        assert s.max_upload_bytes == 5 * 1_048_576


class TestGetSettingsSingleton:
    def test_returns_settings_instance(self):
        get_settings.cache_clear()
        s = get_settings()
        assert isinstance(s, Settings)

    def test_cached(self):
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_cache_clear_allows_reload(self, monkeypatch):
        get_settings.cache_clear()
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        get_settings.cache_clear()
        s = get_settings()
        assert s.log_level == "WARNING"
        get_settings.cache_clear()  # tidy up
