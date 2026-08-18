"""
VELES Monitoring Models

Data models for resource monitoring.

Monitoring is resource-oriented and designed
for remote infrastructure, services and cloud resources.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class HealthCheckResult:
    """
    Result of a single health check.
    """

    resource_id: str

    check_type: str

    status: str = "unknown"

    message: str = ""

    response_time_ms: Optional[float] = None

    timestamp: str = field(
        default_factory=lambda:
        datetime.now().isoformat()
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ResourceHealth:
    """
    Current health state of a resource.
    """

    resource_id: str

    status: str = "unknown"

    checks: list[HealthCheckResult] = field(
        default_factory=list
    )

    last_check: str = field(
        default_factory=lambda:
        datetime.now().isoformat()
    )

    uptime: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class MonitoringTarget:
    """
    Resource observed by the monitoring engine.

    The target is intentionally generic so it can
    represent remote servers, cloud resources,
    network devices or service endpoints.
    """

    resource_id: str

    name: str

    host: str

    port: int = 0

    enabled: bool = True

    interval: int = 60

    checks: list[str] = field(
        default_factory=lambda: [
            "ping"
        ]
    )

    target_type: str = "resource"

    provider: Optional[str] = None

    endpoint: Optional[str] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )