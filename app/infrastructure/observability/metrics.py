"""Performance metrics collection."""

import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class RequestMetric:
    """Request metric data."""

    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    client_id: Optional[str] = None
    ip_address: Optional[str] = None


@dataclass
class EndpointStats:
    """Statistics for an endpoint."""

    endpoint: str
    method: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time_ms: float = 0.0
    min_response_time_ms: float = float('inf')
    max_response_time_ms: float = 0.0
    avg_response_time_ms: float = 0.0
    p50_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    last_request_at: Optional[datetime] = None


class MetricsCollector:
    """Collector for performance metrics."""

    def __init__(self, max_metrics: int = 10000):
        """Initialize metrics collector.

        Args:
            max_metrics: Maximum number of metrics to keep in memory
        """
        self.max_metrics = max_metrics
        self._metrics: deque = deque(maxlen=max_metrics)
        self._endpoint_stats: Dict[str, EndpointStats] = {}
        self._response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._lock = asyncio.Lock()

    async def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        client_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """Record a request metric.

        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time in milliseconds
            client_id: Optional client ID
            ip_address: Optional IP address
        """
        async with self._lock:
            metric = RequestMetric(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                client_id=client_id,
                ip_address=ip_address,
            )

            self._metrics.append(metric)

            # Update endpoint statistics
            endpoint_key = f"{method}:{endpoint}"
            if endpoint_key not in self._endpoint_stats:
                self._endpoint_stats[endpoint_key] = EndpointStats(
                    endpoint=endpoint,
                    method=method,
                )

            stats = self._endpoint_stats[endpoint_key]
            stats.total_requests += 1
            stats.last_request_at = datetime.utcnow()

            if 200 <= status_code < 400:
                stats.successful_requests += 1
            else:
                stats.failed_requests += 1

            # Update response time statistics
            stats.total_response_time_ms += response_time_ms
            stats.min_response_time_ms = min(stats.min_response_time_ms, response_time_ms)
            stats.max_response_time_ms = max(stats.max_response_time_ms, response_time_ms)
            stats.avg_response_time_ms = stats.total_response_time_ms / stats.total_requests

            # Store response time for percentile calculation
            self._response_times[endpoint_key].append(response_time_ms)

            # Calculate percentiles
            if len(self._response_times[endpoint_key]) > 0:
                sorted_times = sorted(self._response_times[endpoint_key])
                stats.p50_response_time_ms = self._percentile(sorted_times, 50)
                stats.p95_response_time_ms = self._percentile(sorted_times, 95)
                stats.p99_response_time_ms = self._percentile(sorted_times, 99)

    @staticmethod
    def _percentile(sorted_list: List[float], percentile: int) -> float:
        """Calculate percentile.

        Args:
            sorted_list: Sorted list of values
            percentile: Percentile (0-100)

        Returns:
            Percentile value
        """
        if not sorted_list:
            return 0.0

        index = int(len(sorted_list) * percentile / 100)
        index = min(index, len(sorted_list) - 1)
        return sorted_list[index]

    def get_endpoint_stats(self, endpoint: Optional[str] = None, method: Optional[str] = None) -> Dict:
        """Get endpoint statistics.

        Args:
            endpoint: Optional endpoint filter
            method: Optional method filter

        Returns:
            Dictionary of endpoint statistics
        """
        stats_dict = {}

        for key, stats in self._endpoint_stats.items():
            if endpoint and stats.endpoint != endpoint:
                continue
            if method and stats.method != method:
                continue

            stats_dict[key] = {
                "endpoint": stats.endpoint,
                "method": stats.method,
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "failed_requests": stats.failed_requests,
                "response_time_ms": {
                    "min": stats.min_response_time_ms if stats.min_response_time_ms != float('inf') else 0.0,
                    "max": stats.max_response_time_ms,
                    "avg": stats.avg_response_time_ms,
                    "p50": stats.p50_response_time_ms,
                    "p95": stats.p95_response_time_ms,
                    "p99": stats.p99_response_time_ms,
                },
                "last_request_at": stats.last_request_at.isoformat() if stats.last_request_at else None,
            }

        return stats_dict

    def get_recent_metrics(self, limit: int = 100) -> List[Dict]:
        """Get recent metrics.

        Args:
            limit: Maximum number of metrics to return

        Returns:
            List of recent metrics
        """
        recent = list(self._metrics)[-limit:]
        return [
            {
                "endpoint": m.endpoint,
                "method": m.method,
                "status_code": m.status_code,
                "response_time_ms": m.response_time_ms,
                "timestamp": m.timestamp.isoformat(),
                "client_id": m.client_id,
                "ip_address": m.ip_address,
            }
            for m in recent
        ]

    def get_summary_stats(self) -> Dict:
        """Get summary statistics.

        Returns:
            Summary statistics dictionary
        """
        if not self._metrics:
            return {
                "total_requests": 0,
                "total_endpoints": 0,
                "avg_response_time_ms": 0.0,
            }

        total_requests = len(self._metrics)
        total_response_time = sum(m.response_time_ms for m in self._metrics)
        avg_response_time = total_response_time / total_requests if total_requests > 0 else 0.0

        # Count by status code
        status_counts = defaultdict(int)
        for metric in self._metrics:
            status_range = f"{metric.status_code // 100}xx"
            status_counts[status_range] += 1

        return {
            "total_requests": total_requests,
            "total_endpoints": len(self._endpoint_stats),
            "avg_response_time_ms": round(avg_response_time, 2),
            "status_code_distribution": dict(status_counts),
            "endpoints_tracked": len(self._endpoint_stats),
        }

    def clear_metrics(self):
        """Clear all metrics."""
        self._metrics.clear()
        self._endpoint_stats.clear()
        self._response_times.clear()
        logger.info("Metrics cleared")


# Global metrics collector instance
metrics_collector = MetricsCollector()

