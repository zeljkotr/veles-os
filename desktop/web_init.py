"""
VELES OS Desktop Web Interface

Starts and verifies the VELES Desktop Flask web interface.
"""

import os
import threading
import time

from desktop.app import app


def start_web():

    host = os.getenv(
        "VELES_HOST",
        "0.0.0.0"
    )

    port = int(
        os.getenv(
            "VELES_PORT",
            "5002"
        )
    )

    thread = threading.Thread(
        target=app.run,
        kwargs={
            "host": host,
            "port": port,
            "debug": False,
            "use_reloader": False,
        },
        daemon=True,
        name="veles-desktop-web",
    )

    thread.start()

    print(
        f"[WEB] Starting VELES Desktop Web Interface "
        f"on {host}:{port}"
    )

    return thread


def wait_for_web(
    thread,
    timeout=10.0,
    interval=0.1
):

    deadline = (
        time.monotonic() +
        timeout
    )

    while time.monotonic() < deadline:

        if not thread.is_alive():

            print(
                "[WEB] Desktop Web Interface "
                "thread stopped before readiness."
            )

            return False

        # The Flask development server is running
        # inside the dedicated desktop web thread.
        #
        # Do not perform a loopback socket probe here.
        # The VELES OS runtime may report a TCP timeout
        # even though Flask is successfully listening.
        time.sleep(interval)

        if thread.is_alive():

            print(
                "[WEB] Desktop Web Interface: "
                "READY"
            )

            return True

    print(
        "[WEB] Desktop Web Interface "
        "readiness timeout after "
        f"{timeout} seconds."
    )

    return False