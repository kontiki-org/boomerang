import os
from importlib.metadata import version

image_version = os.environ.get("BOOMERANG_VERSION", "")
__version__ = image_version or version("kontiki-boomerang")
