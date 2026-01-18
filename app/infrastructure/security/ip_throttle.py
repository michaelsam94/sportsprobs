"""IP throttling and abuse prevention service."""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class IPThrottleService:
    """Service for IP-based throttling and abuse prevention."""

    def __init__(self):
        """Initialize IP throttle service."""
        # Track request times per IP
        self._request_times: Dict[str, List[datetime]] = defaultdict(list)
        
        # Track suspicious activity
        self._suspicious_ips: Dict[str, Dict] = defaultdict(dict)
        
        # Blocked IPs
        self._blocked_ips: Dict[str, datetime] = {}
        
        # Configuration
        self.max_requests_per_minute = 100
        self.max_requests_per_hour = 1000
        self.suspicious_threshold = 5  # Suspicious requests before blocking
        self.block_duration_minutes = 60  # Block duration in minutes
        self._lock = asyncio.Lock()

    async def check_ip(self, ip_address: str) -> tuple[bool, Optional[str]]:
        """Check if IP is allowed to make requests.

        Args:
            ip_address: IP address to check

        Returns:
            Tuple of (is_allowed, reason_if_blocked)
        """
        async with self._lock:
            now = datetime.utcnow()

            # Check if IP is blocked
            if ip_address in self._blocked_ips:
                block_until = self._blocked_ips[ip_address]
                if now < block_until:
                    remaining = (block_until - now).total_seconds() / 60
                    return False, f"IP blocked. Try again in {remaining:.0f} minutes"
                else:
                    # Block expired, remove it
                    del self._blocked_ips[ip_address]
                    if ip_address in self._suspicious_ips:
                        del self._suspicious_ips[ip_address]

            # Clean old request times
            self._clean_old_requests(ip_address, now)

            # Get request times for this IP
            request_times = self._request_times[ip_address]

            # Check per-minute limit
            recent_requests = [
                t for t in request_times
                if now - t < timedelta(minutes=1)
            ]
            if len(recent_requests) >= self.max_requests_per_minute:
                await self._mark_suspicious(ip_address, "rate_limit_exceeded")
                return False, "Rate limit exceeded. Too many requests per minute"

            # Check per-hour limit
            hourly_requests = [
                t for t in request_times
                if now - t < timedelta(hours=1)
            ]
            if len(hourly_requests) >= self.max_requests_per_hour:
                await self._mark_suspicious(ip_address, "hourly_limit_exceeded")
                return False, "Rate limit exceeded. Too many requests per hour"

            # Record this request
            request_times.append(now)

            return True, None

    async def _mark_suspicious(self, ip_address: str, reason: str):
        """Mark IP as suspicious.

        Args:
            ip_address: IP address
            reason: Reason for marking as suspicious
        """
        if ip_address not in self._suspicious_ips:
            self._suspicious_ips[ip_address] = {
                "count": 0,
                "first_seen": datetime.utcnow(),
                "reasons": [],
            }

        self._suspicious_ips[ip_address]["count"] += 1
        self._suspicious_ips[ip_address]["reasons"].append({
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Block if threshold exceeded
        if self._suspicious_ips[ip_address]["count"] >= self.suspicious_threshold:
            await self._block_ip(ip_address, reason)

    async def _block_ip(self, ip_address: str, reason: str):
        """Block an IP address.

        Args:
            ip_address: IP address to block
            reason: Reason for blocking
        """
        block_until = datetime.utcnow() + timedelta(minutes=self.block_duration_minutes)
        self._blocked_ips[ip_address] = block_until
        logger.warning(
            f"Blocked IP {ip_address} until {block_until.isoformat()}. Reason: {reason}"
        )

    def _clean_old_requests(self, ip_address: str, now: datetime):
        """Clean old request times for an IP.

        Args:
            ip_address: IP address
            now: Current datetime
        """
        if ip_address in self._request_times:
            # Keep only requests from last hour
            self._request_times[ip_address] = [
                t for t in self._request_times[ip_address]
                if now - t < timedelta(hours=1)
            ]

    async def unblock_ip(self, ip_address: str) -> bool:
        """Manually unblock an IP address.

        Args:
            ip_address: IP address to unblock

        Returns:
            True if unblocked, False if not blocked
        """
        async with self._lock:
            if ip_address in self._blocked_ips:
                del self._blocked_ips[ip_address]
                if ip_address in self._suspicious_ips:
                    del self._suspicious_ips[ip_address]
                logger.info(f"Unblocked IP: {ip_address}")
                return True
            return False

    def get_ip_status(self, ip_address: str) -> Dict:
        """Get status information for an IP.

        Args:
            ip_address: IP address

        Returns:
            Status dictionary
        """
        now = datetime.utcnow()
        request_times = self._request_times.get(ip_address, [])

        # Clean old requests
        recent_requests = [
            t for t in request_times
            if now - t < timedelta(hours=1)
        ]

        status = {
            "ip_address": ip_address,
            "is_blocked": ip_address in self._blocked_ips,
            "requests_last_hour": len(recent_requests),
            "requests_last_minute": len([
                t for t in recent_requests
                if now - t < timedelta(minutes=1)
            ]),
            "suspicious_count": self._suspicious_ips.get(ip_address, {}).get("count", 0),
        }

        if ip_address in self._blocked_ips:
            block_until = self._blocked_ips[ip_address]
            status["blocked_until"] = block_until.isoformat()
            status["block_remaining_minutes"] = max(0, (block_until - now).total_seconds() / 60)

        return status

    def get_blocked_ips(self) -> List[str]:
        """Get list of currently blocked IPs."""
        now = datetime.utcnow()
        # Remove expired blocks
        active_blocks = {
            ip: until for ip, until in self._blocked_ips.items()
            if now < until
        }
        self._blocked_ips = active_blocks
        return list(self._blocked_ips.keys())


# Global IP throttle service instance
ip_throttle_service = IPThrottleService()

