from pathlib import Path
import os


from installer.image.pipeline import ImagePipeline


def load_environment(path):
    """Load VELES build-time environment configuration."""

    environment_path = Path(path)

    if not environment_path.is_file():
        raise FileNotFoundError(
            f"VELES environment file not found: {environment_path}"
        )

    for line in environment_path.read_text(
        encoding="utf-8"
    ).splitlines():

        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[7:].strip()

        if "=" not in line:
            continue

        name, value = line.split("=", 1)

        name = name.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in ("'", '"')
        ):
            value = value[1:-1]

        if name:
            os.environ[name] = value


load_environment("/etc/veles/veles.env")


pipeline = ImagePipeline(
    image_root="build/rootfs",
    staging_root="build/iso",
    output_iso="build/VELES-OS-test.iso",
)

pipeline.build()

print()
print("VELES ISO BUILD COMPLETE")