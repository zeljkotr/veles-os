"""
VELES Monitoring Scheduler

Central background scheduler for automatic remote monitoring.

The scheduler uses one worker thread and maintains an
independent monitoring schedule for every resource.

Resource monitoring configuration:

    resource["monitoring"] = {
        "enabled": True,
        "interval": 60,
        "checks": [
            "ping",
            "port",
            "http"
        ]
    }

If no monitoring configuration exists, the scheduler
uses the default configuration:

    enabled  = True
    interval = 60
    checks   = ["ping"]

The scheduler never creates one thread per resource.
"""

import threading

from datetime import datetime, timedelta


DEFAULT_INTERVAL = 60

MIN_INTERVAL = 1

WORKER_TICK = 1


class MonitoringScheduler:
    """
    Central VELES monitoring scheduler.

    One worker thread manages all resources.

    Each resource has its own:

        enabled
        interval
        last_run
        next_run
        running
        error

    The scheduler delegates actual monitoring to
    MonitoringService.
    """

    def __init__(
        self,
        service,
        interval=DEFAULT_INTERVAL
    ):

        self.service = service

        self.interval = max(
            MIN_INTERVAL,
            int(interval)
        )

        self.running = False

        self.thread = None

        self._stop_event = threading.Event()

        self._lock = threading.RLock()

        self.last_check_at = None

        self.next_check_at = None

        self.check_count = 0

        self.last_resource_count = 0

        self.last_healthy = 0

        self.last_warning = 0

        self.last_critical = 0

        self.last_unknown = 0

        self.resource_schedules = {}


    # =========================================================
    # START
    # =========================================================

    def start(
        self,
        resources_provider
    ):
        """
        Start the central monitoring loop.
        """

        if self.running:

            return False


        if not callable(
            resources_provider
        ):

            raise TypeError(
                "resources_provider must be callable"
            )


        self.running = True

        self._stop_event.clear()


        with self._lock:

            self.last_check_at = None

            self.next_check_at = None

            self.check_count = 0

            self.last_resource_count = 0

            self.last_healthy = 0

            self.last_warning = 0

            self.last_critical = 0

            self.last_unknown = 0

            self.resource_schedules = {}


        self.thread = threading.Thread(

            target=self._worker,

            args=(
                resources_provider,
            ),

            daemon=True,

            name="veles-monitoring"

        )


        self.thread.start()


        return True


    # =========================================================
    # STOP
    # =========================================================

    def stop(self):
        """
        Stop monitoring loop.
        """

        self.running = False

        self._stop_event.set()


        with self._lock:

            self.next_check_at = None


        thread = self.thread


        if (
            thread
            and thread.is_alive()
            and thread is not threading.current_thread()
        ):

            thread.join(
                timeout=2
            )


        self.thread = None


    # =========================================================
    # STATE
    # =========================================================

    def is_running(self):

        return (
            self.running
            and self.thread is not None
            and self.thread.is_alive()
        )


    def get_status(self):
        """
        Return scheduler state for the web UI.
        """

        with self._lock:

            return {

                "running":
                    self.is_running(),

                "interval":
                    self.interval,

                "last_check_at":
                    self.last_check_at,

                "next_check_at":
                    self.next_check_at,

                "check_count":
                    self.check_count,

                "resource_count":
                    self.last_resource_count,

                "healthy":
                    self.last_healthy,

                "warning":
                    self.last_warning,

                "critical":
                    self.last_critical,

                "unknown":
                    self.last_unknown,

                "resources":
                    self._get_resource_schedule_status()

            }


    # =========================================================
    # RESOURCE CONFIGURATION
    # =========================================================

    def _get_monitoring_config(
        self,
        resource
    ):
        """
        Resolve monitoring configuration for one resource.

        Supported:

            resource["monitoring"]

        Defaults:

            enabled  = True
            interval = global scheduler interval
            checks   = ["ping"]
        """

        monitoring = resource.get(
            "monitoring"
        )


        if not isinstance(
            monitoring,
            dict
        ):

            monitoring = {}


        enabled = monitoring.get(
            "enabled",
            True
        )


        if isinstance(
            enabled,
            str
        ):

            enabled = (
                enabled.strip().lower()
                in (
                    "1",
                    "true",
                    "yes",
                    "on"
                )
            )

        else:

            enabled = bool(
                enabled
            )


        interval = monitoring.get(
            "interval",
            self.interval
        )


        try:

            interval = int(
                interval
            )

        except (
            TypeError,
            ValueError
        ):

            interval = self.interval


        interval = max(
            MIN_INTERVAL,
            interval
        )


        checks = monitoring.get(
            "checks"
        )


        if checks is None:

            checks = resource.get(
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


        normalized_checks = []


        for check in checks:

            value = str(
                check
            ).strip().lower()


            if (
                value
                and value not in normalized_checks
            ):

                normalized_checks.append(
                    value
                )


        if not normalized_checks:

            normalized_checks = [
                "ping"
            ]


        return {

            "enabled":
                enabled,

            "interval":
                interval,

            "checks":
                normalized_checks

        }


    # =========================================================
    # RESOURCE SCHEDULE
    # =========================================================

    def _sync_resources(
        self,
        resources
    ):
        """
        Synchronize scheduler state with the current
        Resource Registry.

        Existing schedule state is preserved.

        New resources are scheduled immediately.

        Removed resources are removed from the scheduler.
        """

        now = datetime.now()

        current_ids = set()


        for resource in resources:

            if not isinstance(
                resource,
                dict
            ):

                continue


            resource_id = resource.get(
                "id"
            )


            if resource_id is None:

                continue


            resource_id = str(
                resource_id
            )

            current_ids.add(
                resource_id
            )


            config = self._get_monitoring_config(
                resource
            )


            existing = self.resource_schedules.get(
                resource_id
            )


            if existing is None:

                self.resource_schedules[
                    resource_id
                ] = {

                    "resource_id":
                        resource_id,

                    "name":
                        resource.get(
                            "name",
                            resource_id
                        ),

                    "enabled":
                        config["enabled"],

                    "interval":
                        config["interval"],

                    "checks":
                        config["checks"],

                    "last_run":
                        None,

                    "next_run":
                        now
                        if config["enabled"]
                        else None,

                    "running":
                        False,

                    "error":
                        None

                }

                continue


            existing[
                "name"
            ] = resource.get(
                "name",
                resource_id
            )


            previous_enabled = existing.get(
                "enabled",
                True
            )


            previous_interval = existing.get(
                "interval",
                self.interval
            )


            existing[
                "enabled"
            ] = config["enabled"]


            existing[
                "interval"
            ] = config["interval"]


            existing[
                "checks"
            ] = config["checks"]


            if not config["enabled"]:

                existing[
                    "next_run"
                ] = None


            elif (
                not previous_enabled
                or previous_interval
                != config["interval"]
            ):

                existing[
                    "next_run"
                ] = now


        removed_ids = (

            set(
                self.resource_schedules.keys()
            )
            - current_ids

        )


        for resource_id in removed_ids:

            self.resource_schedules.pop(
                resource_id,
                None
            )


    # =========================================================
    # DUE RESOURCES
    # =========================================================

    def _get_due_resources(
        self,
        resources
    ):
        """
        Return resources whose next_run has arrived.
        """

        now = datetime.now()

        due = []


        for resource in resources:

            if not isinstance(
                resource,
                dict
            ):

                continue


            resource_id = resource.get(
                "id"
            )


            if resource_id is None:

                continue


            resource_id = str(
                resource_id
            )


            schedule = self.resource_schedules.get(
                resource_id
            )


            if schedule is None:

                continue


            if not schedule.get(
                "enabled",
                True
            ):

                continue


            next_run = schedule.get(
                "next_run"
            )


            if next_run is None:

                continue


            if next_run <= now:

                due.append(
                    resource
                )


        return due


    # =========================================================
    # RESOURCE CHECK
    # =========================================================

    def _check_resource(
        self,
        resource
    ):
        """
        Execute monitoring for one scheduled resource.
        """

        resource_id = resource.get(
            "id"
        )


        if resource_id is None:

            return None


        resource_id = str(
            resource_id
        )


        schedule = self.resource_schedules.get(
            resource_id
        )


        if schedule is None:

            return None


        schedule[
            "running"
        ] = True

        schedule[
            "error"
        ] = None


        try:

            result = self.service.check_resource(
                resource
            )


            return result


        except Exception as exc:

            schedule[
                "error"
            ] = str(
                exc
            )

            print(
                "[MONITORING RESOURCE ERROR]",
                resource_id,
                repr(exc),
                flush=True
            )

            return None


        finally:

            now = datetime.now()

            schedule[
                "running"
            ] = False

            schedule[
                "last_run"
            ] = now.isoformat()


            interval = max(
                MIN_INTERVAL,
                int(
                    schedule.get(
                        "interval",
                        self.interval
                    )
                )
            )


            if schedule.get(
                "enabled",
                True
            ):

                schedule[
                    "next_run"
                ] = (
                    now
                    + timedelta(
                        seconds=interval
                    )
                )

            else:

                schedule[
                    "next_run"
                ] = None


    # =========================================================
    # STATUS
    # =========================================================

    def _calculate_summary(
        self,
        results
    ):
        """
        Calculate current scheduler summary.
        """

        healthy = 0

        warning = 0

        critical = 0

        unknown = 0


        for result in results:

            if result is None:

                continue


            status = getattr(
                result,
                "status",
                "unknown"
            )


            status = str(
                status
            ).strip().lower()


            if status == "healthy":

                healthy += 1

            elif status == "warning":

                warning += 1

            elif status == "critical":

                critical += 1

            else:

                unknown += 1


        return (
            healthy,
            warning,
            critical,
            unknown
        )


    # =========================================================
    # RESOURCE SCHEDULE STATUS
    # =========================================================

    def _get_resource_schedule_status(
        self
    ):
        """
        Return scheduler state for every resource.
        """

        resources = []


        for resource_id, schedule in (
            self.resource_schedules.items()
        ):

            resources.append({

                "resource_id":
                    resource_id,

                "name":
                    schedule.get(
                        "name"
                    ),

                "enabled":
                    schedule.get(
                        "enabled",
                        True
                    ),

                "interval":
                    schedule.get(
                        "interval",
                        self.interval
                    ),

                "checks":
                    list(
                        schedule.get(
                            "checks",
                            []
                        )
                    ),

                "last_run":
                    schedule.get(
                        "last_run"
                    ),

                "next_run":
                    schedule.get(
                        "next_run"
                    ),

                "running":
                    schedule.get(
                        "running",
                        False
                    ),

                "error":
                    schedule.get(
                        "error"
                    )

            })


        return resources


    # =========================================================
    # WORKER
    # =========================================================

    def _worker(
        self,
        resources_provider
    ):

        print(
            "[MONITORING] Worker started",
            flush=True
        )


        while self.running:

            try:

                resources = (
                    resources_provider()
                    or []
                )


                resource_count = len(
                    resources
                )


                print(
                    "[MONITORING] Resources provider returned",
                    flush=True
                )


                print(
                    "[MONITORING] Resources:",
                    resource_count,
                    flush=True
                )


                with self._lock:

                    self._sync_resources(
                        resources
                    )


                    due_resources = (
                        self._get_due_resources(
                            resources
                        )
                    )


                    self.last_resource_count = (
                        resource_count
                    )


                if due_resources:

                    print(
                        "[MONITORING] Due resources:",
                        len(
                            due_resources
                        ),
                        flush=True
                    )


                cycle_results = []


                for resource in due_resources:

                    if not self.running:

                        break


                    result = self._check_resource(
                        resource
                    )


                    if result is not None:

                        cycle_results.append(
                            result
                        )


                if due_resources:

                    (
                        healthy,
                        warning,
                        critical,
                        unknown
                    ) = self._calculate_summary(
                        cycle_results
                    )


                    with self._lock:

                        self.last_check_at = (
                            datetime.now().isoformat()
                        )

                        self.check_count += 1

                        self.last_healthy = healthy

                        self.last_warning = warning

                        self.last_critical = critical

                        self.last_unknown = unknown


                    print(
                        "[MONITORING] Check cycle complete:",
                        "checked=",
                        len(
                            cycle_results
                        ),
                        "healthy=",
                        healthy,
                        "warning=",
                        warning,
                        "critical=",
                        critical,
                        "unknown=",
                        unknown,
                        flush=True
                    )


                with self._lock:

                    next_runs = [

                        schedule.get(
                            "next_run"
                        )

                        for schedule
                        in self.resource_schedules.values()

                        if (
                            schedule.get(
                                "enabled",
                                True
                            )
                            and schedule.get(
                                "next_run"
                            ) is not None
                        )

                    ]


                    if next_runs:

                        self.next_check_at = min(
                            next_runs
                        )

                    else:

                        self.next_check_at = None


            except Exception as exc:

                print(
                    "[MONITORING ERROR]",
                    repr(exc),
                    flush=True
                )


                with self._lock:

                    self.last_check_at = (
                        datetime.now().isoformat()
                    )

                    self.check_count += 1


            if self._stop_event.wait(
                WORKER_TICK
            ):

                break


        self.running = False


        with self._lock:

            self.next_check_at = None


        print(
            "[MONITORING] Worker stopped",
            flush=True
        )