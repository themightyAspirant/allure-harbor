from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.errors import MissingResultsError, ZipBombError, ZipSlipError
from app.services.upload import extract_zip, find_results_root, is_safe_member
from tests.support.zips import build_results_zip, build_zip_with_member


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        data_dir=tmp_path,
        max_upload_mb=1,
        max_zip_files=2,
        max_uncompressed_mb=1,
        allure_bin="allure",
    )


def test_zip_slip_is_rejected(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    zip_path = tmp_path / "slip.zip"
    zip_path.write_bytes(build_zip_with_member("../evil.txt", b"hacked"))
    with pytest.raises(ZipSlipError):
        extract_zip(zip_path, dest, _settings(tmp_path))
    assert not (tmp_path / "evil.txt").exists()


def test_absolute_zip_member_is_unsafe(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    assert not is_safe_member("/tmp/evil.txt", dest)
    assert not is_safe_member("C:\\Windows\\evil.txt", dest)
    assert not is_safe_member("..\\evil.txt", dest)


def test_valid_zip_extracts_results(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    zip_path = tmp_path / "ok.zip"
    zip_path.write_bytes(build_results_zip(nested=True))
    extract_zip(zip_path, dest, _settings(tmp_path))
    root = find_results_root(dest)
    assert (root / "aaaaaaaa-result.json").is_file()


def test_missing_results_raises(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    zip_path = tmp_path / "empty.zip"
    zip_path.write_bytes(build_zip_with_member("readme.txt", b"hello"))
    extract_zip(zip_path, dest, _settings(tmp_path))
    with pytest.raises(MissingResultsError):
        find_results_root(dest)


def test_too_many_zip_entries_is_bomb(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    zip_path = tmp_path / "bomb.zip"
    zip_path.write_bytes(
        build_results_zip(
            extra={
                "one.bin": b"1",
                "two.bin": b"2",
            }
        )
    )
    with pytest.raises(ZipBombError):
        extract_zip(zip_path, dest, _settings(tmp_path))
