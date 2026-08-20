"""
VELES OS

Primary VELES OS entrypoint.
"""

from kernel.runtime import VelesRuntime


def main():
    runtime = VelesRuntime()

    try:
        runtime.start()
        runtime.wait()

    except KeyboardInterrupt:
        print()
        print("[VELES] Shutdown requested.")

    finally:
        runtime.stop()


if __name__ == "__main__":
    main()
