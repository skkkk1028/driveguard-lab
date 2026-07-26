"""Tests for Windows-safe cleanup of SUMO-owned temporary logs."""

import time

import pytest

import app.adapters.sumo.session as session_module


class _TemporaryDirectoryDouble:
    def __init__(self, failures_before_success: int) -> None:
        self.failures_before_success = failures_before_success
        self.cleanup_calls = 0

    def cleanup(self) -> None:
        self.cleanup_calls += 1
        if self.cleanup_calls <= self.failures_before_success:
            raise PermissionError("SUMO still holds the error log")


def test_temporary_directory_cleanup_retries_windows_file_locks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = _TemporaryDirectoryDouble(failures_before_success=2)
    sleep_calls: list[float] = []
    monkeypatch.setattr(time, "sleep", sleep_calls.append)

    session_module._cleanup_temporary_directory(directory)  # type: ignore[arg-type]

    assert directory.cleanup_calls == 3
    assert sleep_calls == [
        session_module.TEMPORARY_DIRECTORY_CLEANUP_RETRY_DELAY_S,
        session_module.TEMPORARY_DIRECTORY_CLEANUP_RETRY_DELAY_S,
    ]


def test_temporary_directory_cleanup_raises_after_bounded_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = _TemporaryDirectoryDouble(
        failures_before_success=session_module.TEMPORARY_DIRECTORY_CLEANUP_ATTEMPTS
    )
    monkeypatch.setattr(time, "sleep", lambda _: None)

    with pytest.raises(PermissionError, match="SUMO still holds"):
        session_module._cleanup_temporary_directory(directory)  # type: ignore[arg-type]

    assert (
        directory.cleanup_calls
        == session_module.TEMPORARY_DIRECTORY_CLEANUP_ATTEMPTS
    )
