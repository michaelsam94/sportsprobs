"""Observability endpoints for metrics and monitoring."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.auth import verify_admin_token
from app.infrastructure.observability.metrics import metrics_collector
from app.infrastructure.observability.error_tracker import error_tracker

router = APIRouter()


@router.get("/metrics", tags=["observability"])
async def get_metrics(
    endpoint: Optional[str] = Query(None, description="Filter by endpoint"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
):
    """Get performance metrics (public endpoint for monitoring)."""
    try:
        summary = metrics_collector.get_summary_stats()
        endpoint_stats = metrics_collector.get_endpoint_stats(endpoint=endpoint, method=method)
        
        return {
            "summary": summary,
            "endpoints": endpoint_stats,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}",
        )


@router.get("/metrics/recent", tags=["observability", "admin"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_recent_metrics(
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Number of recent metrics"),
    authorization: Optional[str] = None,
):
    """Get recent request metrics (Admin only)."""
    verify_admin_token(authorization)
    
    try:
        metrics = metrics_collector.get_recent_metrics(limit=limit)
        return {
            "count": len(metrics),
            "metrics": metrics,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent metrics: {str(e)}",
        )


@router.get("/errors", tags=["observability", "admin"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_errors(
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Number of recent errors"),
    authorization: Optional[str] = None,
):
    """Get recent errors (Admin only)."""
    verify_admin_token(authorization)
    
    try:
        errors = error_tracker.get_recent_errors(limit=limit)
        error_summary = error_tracker.get_error_summary()
        
        return {
            "recent_errors": errors,
            "summary": error_summary,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get errors: {str(e)}",
        )


@router.get("/errors/summary", tags=["observability", "admin"])
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_error_summary(
    request: Request,
    authorization: Optional[str] = None,
):
    """Get error summary statistics (Admin only)."""
    verify_admin_token(authorization)
    
    try:
        summary = error_tracker.get_error_summary()
        error_counts = error_tracker.get_error_counts()
        
        return {
            "summary": summary,
            "error_counts": error_counts,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get error summary: {str(e)}",
        )


@router.delete("/metrics", status_code=204, tags=["observability", "admin"])
@limiter.limit("10/minute")
async def clear_metrics(
    request: Request,
    authorization: Optional[str] = None,
):
    """Clear all metrics (Admin only)."""
    verify_admin_token(authorization)
    
    try:
        metrics_collector.clear_metrics()
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear metrics: {str(e)}",
        )


@router.delete("/errors", status_code=204, tags=["observability", "admin"])
@limiter.limit("10/minute")
async def clear_errors(
    request: Request,
    authorization: Optional[str] = None,
):
    """Clear all error records (Admin only)."""
    verify_admin_token(authorization)
    
    try:
        error_tracker.clear_errors()
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear errors: {str(e)}",
        )


@router.get("/health/detailed", tags=["observability"])
async def detailed_health_check():
    """Detailed health check with observability status."""
    from app.infrastructure.cache.redis_client import redis_client
    
    redis_healthy = await redis_client.health_check()
    metrics_summary = metrics_collector.get_summary_stats()
    error_summary = error_tracker.get_error_summary()
    
    return {
        "status": "healthy",
        "redis": "connected" if redis_healthy else "disconnected",
        "metrics": {
            "total_requests": metrics_summary.get("total_requests", 0),
            "endpoints_tracked": metrics_summary.get("endpoints_tracked", 0),
        },
        "errors": {
            "total_errors": error_summary.get("total_errors", 0),
            "error_types": len(error_summary.get("error_types", {})),
        },
    }

