"""External integration package."""

from app.integrations.ocr_client import OCRClient, OCRClientError

__all__ = ["OCRClient", "OCRClientError"]
