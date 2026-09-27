"""
Weather-Sculpt — sculpt real ERA5 weather fields into video, GIF and sound.

Real reanalysis data (ECMWF ERA5, CC-BY 4.0), tuned "sculpt" presets,
video/GIF export and a sonification channel.
"""

__version__ = "0.1.0"

from .fields import open_weather, vorticity, divergence, normalize, to_celsius
from .presets import PRESETS, list_presets, draw_frame
from .render import render_video
from .sonify import sonify

__all__ = [
    "__version__",
    "open_weather",
    "vorticity",
    "divergence",
    "normalize",
    "to_celsius",
    "PRESETS",
    "list_presets",
    "draw_frame",
    "render_video",
    "sonify",
]
