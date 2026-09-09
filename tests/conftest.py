import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def _write_shim(directory: Path, script: Path) -> Path:
    if os.name == "nt":
        shim = directory / "allure.cmd"
        shim.write_text(
            f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n',
            encoding="utf-8",
        )
        return shim
    shim = directory / "allure"
    shim.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    return shim


@pytest.fixture
def fake_allure(tmp_path: Path) -> Path:
    script = Path(__file__).parent / "support" / "fake_allure.py"
    return _write_shim(tmp_path, script)


@pytest.fixture
def failing_allure(tmp_path: Path) -> Path:
    script = Path(__file__).parent / "support" / "failing_allure.py"
    directory = tmp_path / "failing"
    directory.mkdir()
    return _write_shim(directory, script)


@pytest.fixture
def settings(tmp_path: Path, fake_allure: Path) -> Settings:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return Settings(
        data_dir=data_dir,
        max_upload_mb=1,
        max_zip_files=20,
        max_uncompressed_mb=2,
        allure_bin=str(fake_allure),
        public_base_url="http://testserver",
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
