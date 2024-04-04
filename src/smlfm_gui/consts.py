from enum import unique, Enum

COMMAND = 'command'
READONLY = 'readonly'
TEXT = 'text'
TEXTVARIABLE = 'textvariable'
VARIABLE = 'variable'
IMAGE = 'image'


@unique
class GraphType(Enum):
    MLA = 1  # All generated MLA lenses
    CSV_RAW = 2  # All points as loaded from CSV file
    MAPPED = 3  # Colored CSV points as mapped to MLA lenses
    FILTERED = 4  # Same as MAPPED but with some points filtered out
    CORRECTED = 5  # Similar to FILTERED but with aberration corrections
    LOCS_3D = 6  # 3D view
    HISTOGRAM = 7  # 2D histogram
    OCCURRENCES = 8


@unique
class StageType(Enum):
    CONFIG = 1
    CSV = 2
    OPTICS = 3
    FILTER = 4
    CORRECT = 5
    FIT = 6
