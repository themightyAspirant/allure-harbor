from typing import Any


class HarborError(Exception):
    status_code: int = 400
    code: str = "HARBOR_ERROR"

    def __init__(
        self,
        message: str,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or []


class InvalidZipError(HarborError):
    status_code = 400
    code = "INVALID_ZIP"


class ZipSlipError(HarborError):
    status_code = 400
    code = "ZIP_SLIP"


class ZipBombError(HarborError):
    status_code = 400
    code = "ZIP_BOMB"


class MissingResultsError(HarborError):
    status_code = 422
    code = "MISSING_RESULTS"


class PayloadTooLargeError(HarborError):
    status_code = 413
    code = "PAYLOAD_TOO_LARGE"


class ReportNotFoundError(HarborError):
    status_code = 404
    code = "REPORT_NOT_FOUND"


class GenerationError(HarborError):
    status_code = 502
    code = "GENERATION_FAILED"
