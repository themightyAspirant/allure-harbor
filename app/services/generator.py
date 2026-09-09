import logging
import shutil
import subprocess
from pathlib import Path

from app.core.config import Settings
from app.core.errors import GenerationError

logger = logging.getLogger(__name__)


def resolve_allure_bin(allure_bin: str) -> str:
    configured = Path(allure_bin)
    if configured.is_file():
        return str(configured)
    found = shutil.which(allure_bin)
    if found is None:
        raise FileNotFoundError(allure_bin)
    return found


def generate_report(settings: Settings, results_dir: Path, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    args = ["generate", str(results_dir), "-o", str(report_dir), "--clean"]
    try:
        completed = _run_allure(settings, args, settings.allure_timeout_seconds)
    except FileNotFoundError as exc:
        raise GenerationError("Allure CLI is not installed") from exc
    except subprocess.TimeoutExpired as exc:
        raise GenerationError("Allure report generation timed out") from exc
    if completed.returncode != 0:
        stderr = (completed.stderr or completed.stdout or "").strip()
        logger.error("allure_generate_failed returncode=%s", completed.returncode)
        raise GenerationError(
            "Allure report generation failed",
            details=[{"stderr": stderr[:500]}],
        )
    index = report_dir / "index.html"
    if not index.is_file():
        raise GenerationError("Allure did not produce index.html")


def read_allure_version(settings: Settings) -> str | None:
    try:
        completed = _run_allure(settings, ["--version"], 10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    output = (completed.stdout or completed.stderr).strip()
    return output or None


def _run_allure(
    settings: Settings,
    args: list[str],
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    command = [resolve_allure_bin(settings.allure_bin), *args]
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        shell=False,
    )
