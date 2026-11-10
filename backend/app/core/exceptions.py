from fastapi import Request, status
from fastapi.responses import JSONResponse
from backend.app.core.logging import logger

class KrishiRAGException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)

class DocumentNotFoundException(KrishiRAGException):
    def __init__(self, message: str = "The requested agricultural document was not found."):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, code="DOCUMENT_NOT_FOUND")

class DocumentProcessingError(KrishiRAGException):
    def __init__(self, message: str = "Failed to parse or extract document content."):
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="DOCUMENT_PROCESSING_ERROR")

class RetrievalException(KrishiRAGException):
    def __init__(self, message: str = "Failed during vector or lexical retrieval."):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, code="RETRIEVAL_ERROR")

async def app_exception_handler(request: Request, exc: KrishiRAGException):
    logger.error(f"Handled application exception on {request.url.path}: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "An unexpected error occurred while processing the agricultural advisory request."
            }
        }
    )
