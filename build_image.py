from pathlib import Path

from installer.image.pipeline import ImagePipeline


PROJECT_ROOT = Path(__file__).resolve().parent
BUILD_ROOT = PROJECT_ROOT / "build"
IMAGE_ROOT = BUILD_ROOT / "rootfs"
STAGING_ROOT = BUILD_ROOT / "iso"
OUTPUT_ISO = BUILD_ROOT / "VELES-OS-test.iso"


pipeline = ImagePipeline(
    image_root=str(IMAGE_ROOT),
    staging_root=str(STAGING_ROOT),
    output_iso=str(OUTPUT_ISO),
)

pipeline.build()

print()
print("VELES OS ISO BUILD COMPLETE")