"""Error tracking and monitoring."""

import traceback
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque, defaultdict
from dataclasses import dataclass, field
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class ErrorRecord:
    """Error record data."""

    error_type: str
    error_message: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    request_id: Optional[str] = None
    client_id: Optional[str] = None
    ip_address: Optional[str] = None
    stack_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)


class ErrorTracker:
    """Service for tracking and monitoring errors."""

    def __init__(self, max_errors: int = 1000):
        """Initialize error tracker.

        Args:
            max_errors: Maximum number of errors to keep in memory
        """
        self.max_errors = max_errors
        self._errors: deque = deque(maxlen=max_errors)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def record_error(
        self,
        error: Exception,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
        client_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Record an error.

        Args:
            error: Exception object
            endpoint: Optional endpoint
            method: Optional HTTP method
            status_code: Optional status code
            request_id: Optional request ID
            client_id: Optional client ID
            ip_address: Optional IP address
            context: Optional additional context
        """
        async with self._lock:
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = traceback.format_exc()

            error_record = ErrorRecord(
                error_type=error_type,
                error_message=error_message,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                request_id=request_id,
                client_id=client_id,
                ip_address=ip_address,
                stack_trace=stack_trace,
                context=context or {},
            )

            self._errors.append(error_record)
            self._error_counts[error_type] += 1

            # Log error
            logger.error(
                f"Error recorded: {error_type} - {error_message}",
                extra={
                    "error_type": error_type,
                    "error_message": error_message,
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code,
                    "request_id": request_id,
                    "client_id": client_id,
                    "ip_address": ip_address,
                },
            )

    def get_recent_errors(self, limit: int = 100) -> List[Dict]:
        """Get recent errors.

        Args:
            limit: Maximum number of errors to return

        Returns:
            List of recent error records
        """
        recent = list(self._errors)[-limit:]
        return [
            {
                "error_type": e.error_type,
                "error_message": e.error_message,
                "endpoint": e.endpoint,
                "method": e.method,
                "status_code": e.status_code,
                "request_id": e.request_id,
                "client_id": e.client_id,
                "ip_address": e.ip_address,
                "timestamp": e.timestamp.isoformat(),
                "context": e.context,
            }
            for e in recent
        ]

    def get_error_counts(self) -> Dict[str, int]:
        """Get error counts by type.

        Returns:
            Dictionary of error type to count
        """
        return dict(self._error_counts)

    def get_error_summary(self) -> Dict:
        """Get error summary statistics.

        Returns:
            Error summary dictionary
        """
        total_errors = len(self._errors)
        error_counts = self.get_error_counts()

        # Errors by endpoint
        endpoint_errors = defaultdict(int)
        for error in self._errors:
            if error.endpoint:
                endpoint_errors[error.endpoint] += 1

        # Errors by status code
        status_errors = defaultdict(int)
        for error in self._errors:
            if error.status_code:
                status_errors[error.status_code] += 1

        return {
            "total_errors": total_errors,
            "error_types": error_counts,
            "errors_by_endpoint": dict(endpoint_errors),
            "errors_by_status_code": dict(status_errors),
        }

    def clear_errors(self):
        """Clear all error records."""
        self._errors.clear()
        self._error_counts.clear()
        logger.info("Error tracker cleared")


# Global error tracker instance
error_tracker = ErrorTracker()

