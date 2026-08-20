"""
VELES Monitoring Service

Central monitoring engine for remote infrastructure.

The Resource Registry defines what exists.
Monitoring determines whether those resources are healthy.

Every monitoring result is persisted in PostgreSQL
so health information survives VELES restarts.
"""

from datetime import datetime
from threading import RLock

from core.database.connection import get_session
from core.database.models import MonitoringHistory

from services.monitoring.models import (
    HealthCheckResult,
    ResourceHealth
)

from services.monitoring.checks import (
    run_check
)


class MonitoringService:
    """
    Main VELES monitoring service.

    Responsibilities:

    - execute health checks
    - calculate resource health
    - keep current health in memory
    - persist every check result
    - retrieve monitoring history
    """

    def __init__(self):

        self.health = {}

        self._lock = RLock()


    # =========================================================
    # RESOURCE CHECK
    # =========================================================

    def check_resource(
        self,
        resource: dict
    ):
        """
        Execute all configured checks for one resource.
        """

        if not isinstance(
            resource,
            dict
        ):

            return None


        resource_id = resource.get(
            "id"
        )


        if resource_id is None:

            return None


        resource_id = str(
            resource_id
        )


        checks = self._get_checks(
            resource
        )


        results = []


        for check in checks:

            try:

                result = run_check(
                    check,
                    resource
                )

            except Exception as exc:

                result = {
                    "status": "unknown",
                    "message": str(exc),
                    "response_time_ms": None,
                    "metadata": {}
                }


            health_result = HealthCheckResult(

                resource_id=resource_id,

                check_type=str(
                    check
                ),

                status=result.get(
                    "status",
                    "unknown"
                ),

                message=result.get(
                    "message",
                    ""
                ),

                response_time_ms=result.get(
                    "response_time_ms"
                ),

                metadata=result.get(
                    "metadata",
                    {}
                )
            )


            results.append(
                health_result
            )


            self._store_history(
                health_result
            )


        status = self._calculate_status(
            results
        )


        health = ResourceHealth(

            resource_id=resource_id,

            status=status,

            checks=results,

            last_check=datetime.now().isoformat()
        )


        with self._lock:

            self.health[
                resource_id
            ] = health


        return health


    # =========================================================
    # MULTIPLE RESOURCES
    # =========================================================

    def check_resources(
        self,
        resources: list
    ):
        """
        Check multiple resources.
        """

        results = []


        if not resources:

            return results


        for resource in resources:

            try:

                result = self.check_resource(
                    resource
                )

                if result is not None:

                    results.append(
                        result
                    )

            except Exception as exc:

                print(
                    "[MONITORING RESOURCE ERROR]",
                    exc
                )


        return results


    # =========================================================
    # CURRENT HEALTH
    # =========================================================

    def get_health(
        self,
        resource_id
    ):

        if resource_id is None:

            return None


        key = str(
            resource_id
        )


        with self._lock:

            return self.health.get(
                key
            )


    def get_all_health(self):

        with self._lock:

            return dict(
                self.health
            )


    # =========================================================
    # HEALTH HISTORY
    # =========================================================

    def get_history(
        self,
        resource_id,
        limit=100
    ):
        """
        Return historical monitoring results
        for a resource.

        Newest results are returned first.
        """

        if resource_id is None:

            return []


        try:

            limit = int(
                limit
            )

        except (
            TypeError,
            ValueError
        ):

            limit = 100


        limit = max(
            1,
            min(
                limit,
                1000
            )
        )


        session = get_session()


        try:

            rows = session.query(
                MonitoringHistory
            ).filter(
                MonitoringHistory.resource_id
                == int(resource_id)
            ).order_by(
                MonitoringHistory.timestamp.desc()
            ).limit(
                limit
            ).all()


            return [

                self._history_to_dict(
                    row
                )

                for row in rows

            ]


        except Exception as exc:

            print(
                "[MONITORING HISTORY ERROR]",
                exc
            )

            return []


        finally:

            session.close()


    def get_check_history(
        self,
        resource_id,
        check_type,
        limit=100
    ):
        """
        Return history for one specific check.
        """

        if resource_id is None:

            return []


        try:

            limit = int(
                limit
            )

        except (
            TypeError,
            ValueError
        ):

            limit = 100


        limit = max(
            1,
            min(
                limit,
                1000
            )
        )


        session = get_session()


        try:

            rows = session.query(
                MonitoringHistory
            ).filter(
                MonitoringHistory.resource_id
                == int(resource_id),

                MonitoringHistory.check_type
                == str(check_type).lower()
            ).order_by(
                MonitoringHistory.timestamp.desc()
            ).limit(
                limit
            ).all()


            return [

                self._history_to_dict(
                    row
                )

                for row in rows

            ]


        except Exception as exc:

            print(
                "[MONITORING CHECK HISTORY ERROR]",
                exc
            )

            return []


        finally:

            session.close()


    # =========================================================
    # STORE HISTORY
    # =========================================================

    def _store_history(
        self,
        result: HealthCheckResult
    ):
        """
        Persist one monitoring result.

        Monitoring history is intentionally separate
        from the Resource Registry.
        """

        session = get_session()


        try:

            history = MonitoringHistory(

                resource_id=int(
                    result.resource_id
                ),

                check_type=str(
                    result.check_type
                ),

                status=str(
                    result.status
                ),

                message=result.message,

                response_time_ms=(
                    result.response_time_ms
                ),

                timestamp=self._parse_timestamp(
                    result.timestamp
                ),

                metadata_json=result.metadata or {}
            )


            session.add(
                history
            )

            session.commit()


        except Exception as exc:

            session.rollback()

            print(
                "[MONITORING HISTORY STORE ERROR]",
                exc
            )


        finally:

            session.close()


    # =========================================================
    # MODULE STATUS
    # =========================================================

    def get_status(self):
        """
        VELES module status interface.
        Used by WEB dashboard.
        """

        with self._lock:

            resources = list(
                self.health.values()
            )


        return {

            "name": "Monitoring",

            "status": "active",

            "resources": resources,

            "count": len(
                resources
            )

        }


    # =========================================================
    # CHECK RESOLUTION
    # =========================================================

    def _get_checks(
        self,
        resource: dict
    ):
        """
        Resolve monitoring checks from a resource.

        Supported configuration:

            resource["checks"]

        or:

            resource["monitoring"]["checks"]

        Default:

            ping
        """

        checks = resource.get(
            "checks"
        )


        if checks is None:

            monitoring_config = resource.get(
                "monitoring"
            )

            if isinstance(
                monitoring_config,
                dict
            ):

                checks = monitoring_config.get(
                    "checks"
                )


        if isinstance(
            checks,
            str
        ):

            checks = [
                checks
            ]


        if not isinstance(
            checks,
            (list, tuple)
        ):

            checks = [
                "ping"
            ]


        normalized = []


        for check in checks:

            value = str(
                check
            ).strip().lower()


            if value and value not in normalized:

                normalized.append(
                    value
                )


        if not normalized:

            normalized = [
                "ping"
            ]


        return normalized


    # =========================================================
    # HEALTH CALCULATION
    # =========================================================

    def _calculate_status(
        self,
        results
    ):
        """
        Calculate global resource state.

        Priority:

            CRITICAL
            WARNING
            UNKNOWN
            HEALTHY
        """

        if not results:

            return "unknown"


        statuses = [

            str(
                item.status
            ).strip().lower()

            for item in results

        ]


        if "offline" in statuses:

            return "critical"


        if "warning" in statuses:

            return "warning"


        if "unknown" in statuses:

            return "unknown"


        return "healthy"


    # =========================================================
    # HELPERS
    # =========================================================

    def _history_to_dict(
        self,
        item
    ):
        """
        Convert SQLAlchemy monitoring history
        object to a normal dictionary.
        """

        return {

            "id":
                item.id,

            "resource_id":
                item.resource_id,

            "check_type":
                item.check_type,

            "status":
                item.status,

            "message":
                item.message or "",

            "response_time_ms":
                item.response_time_ms,

            "timestamp":
                (
                    item.timestamp.isoformat()
                    if item.timestamp
                    else None
                ),

            "metadata":
                item.metadata_json or {}

        }


    def _parse_timestamp(
        self,
        value
    ):
        """
        Convert ISO timestamp into datetime.
        """

        if isinstance(
            value,
            datetime
        ):

            return value


        if not value:

            return datetime.utcnow()


        try:

            return datetime.fromisoformat(
                str(value
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return datetime.utcnow()


# Global VELES monitoring instance

monitoring = MonitoringService()