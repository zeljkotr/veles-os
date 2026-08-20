"""
VELES OS Desktop Web Interface

Starts and verifies the VELES Desktop Flask web interface.
"""

import os
import threading
import time
import urllib.error
import urllib.request

from desktop.app import app


def start_web():

    host = os.getenv("VELES_HOST", "0.0.0.0")
    port = int(os.getenv("VELES_PORT", "5002"))

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


def wait_for_web(thread, timeout=5.0, interval=0.1):

    host = os.getenv("VELES_HOST", "0.0.0.0")
    port = int(os.getenv("VELES_PORT", "5002"))

    check_host = (
        "127.0.0.1"
        if host in ("0.0.0.0", "")
        else host
    )

    url = f"http://{check_host}:{port}/"

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:

        if not thread.is_alive():
            return False

        try:
            with urllib.request.urlopen(
                url,
                timeout=0.5,
            ) as response:

                if 200 <= response.status < 500:
                    return True

        except (
            urllib.error.URLError,
            ConnectionError,
            TimeoutError,
            OSError,
        ):
            pass

        time.sleep(interval)

    return False