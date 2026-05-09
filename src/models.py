from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Any


class ShapeType(Enum):
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"
    OTHER = "other"


class ColorGroup(Enum):
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    CYAN = "cyan"
    BLUE = "blue"
    PURPLE = "purple"
    WHITE = "white"
    GRAY = "gray"
    BLACK = "black"


COLOR_GROUP_TO_CHANNEL = {
    ColorGroup.RED: 0,
    ColorGroup.ORANGE: 1,
    ColorGroup.YELLOW: 2,
    ColorGroup.GREEN: 3,
    ColorGroup.CYAN: 4,
    ColorGroup.BLUE: 5,
    ColorGroup.PURPLE: 6,
    ColorGroup.WHITE: 7,
    ColorGroup.GRAY: 8,
    ColorGroup.BLACK: 9,
}

# RGB tuples used for drawing annotation overlays
CHANNEL_COLORS_RGB = {
    0: (220, 60, 60),
    1: (220, 140, 50),
    2: (200, 200, 50),
    3: (60, 180, 60),
    4: (50, 200, 200),
    5: (70, 100, 220),
    6: (160, 60, 220),
    7: (220, 220, 220),
    8: (140, 140, 140),
    9: (180, 100, 60),
}

CHANNEL_NAMES = {
    0: "Lead Melody",
    1: "Counter Melody",
    2: "High Harmony",
    3: "Chord Pad",
    4: "Arpeggio",
    5: "Bass",
    6: "Ethereal",
    7: "Bell",
    8: "Textured",
    9: "Sub-Bass",
}

# Octave shift relative to base octave 4 (C4 = MIDI 60)
CHANNEL_OCTAVE_OFFSET = {
    0: 0,
    1: 0,
    2: 1,
    3: 0,
    4: 0,
    5: -2,
    6: 0,
    7: 2,
    8: 0,
    9: -3,
}

# General MIDI program numbers
CHANNEL_PROGRAMS = {
    0: 40,
    1: 56,
    2: 9,
    3: 48,
    4: 11,
    5: 32,
    6: 91,
    7: 98,
    8: 52,
    9: 43,
}

# Duration in MIDI ticks (at 480 ticks-per-beat)
SHAPE_DURATIONS = {
    ShapeType.CIRCLE: 480,
    ShapeType.RECTANGLE: 240,
    ShapeType.TRIANGLE: 120,
    ShapeType.OTHER: 960,
}

SHAPE_BASE_VELOCITY = {
    ShapeType.CIRCLE: 72,
    ShapeType.RECTANGLE: 88,
    ShapeType.TRIANGLE: 104,
    ShapeType.OTHER: 58,
}

SCALES = {
    "Major":           [0, 2, 4, 5, 7, 9, 11],
    "Natural Minor":   [0, 2, 3, 5, 7, 8, 10],
    "Harmonic Minor":  [0, 2, 3, 5, 7, 8, 11],
    "Pentatonic Major":[0, 2, 4, 7, 9],
    "Pentatonic Minor":[0, 3, 5, 7, 10],
    "Blues":           [0, 3, 5, 6, 7, 10],
    "Dorian":          [0, 2, 3, 5, 7, 9, 10],
    "Mixolydian":      [0, 2, 4, 5, 7, 9, 10],
    "Whole Tone":      [0, 2, 4, 6, 8, 10],
    "Chromatic":       [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
}

ROOT_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass
class DetectedElement:
    shape: ShapeType
    color_group: ColorGroup
    color_rgb: Tuple[int, int, int]
    color_hsv: Tuple[float, float, float]
    position: Tuple[float, float]   # normalized (x, y), 0–1
    size: float                     # normalized contour area, 0–1
    texture_variance: float         # grayscale std-dev inside contour
    bbox: Tuple[int, int, int, int] # x, y, w, h in pixels
    contour: Any = field(repr=False)

    # Assigned by midi_generator
    midi_channel: int = 0
    midi_note: int = 60
    midi_velocity: int = 80
    note_duration: int = 480
    note_start_tick: int = 0
    note_name: str = "C4"


@dataclass
class MIDISettings:
    scale_name: str = "Major"
    root_note_name: str = "C"
    bpm: int = 120
    num_clusters: int = 6
    bars: int = 4
    ticks_per_beat: int = 480
