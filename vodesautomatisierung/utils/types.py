from enum import IntEnum, Enum
from pathlib import Path
from typing import TypeVar, Union, Optional
from datetime import timedelta
from dataclasses import dataclass

__all__ = ["PathLike", "Paths", "Trim", "TrackType", "AudioFormat", "AudioFrame", "AudioStats", "AudioInfo"]

PathLike = TypeVar("PathLike", str, Path, None)
Trim = tuple[int | None, int | None]

Paths = Union[PathLike, list[PathLike]]

# Timedelta (or frame, which will be converted internally), Optional Name
Chapter = tuple[timedelta | int, Optional[str]]


class TrackType(IntEnum):
    VIDEO = 1
    AUDIO = 2
    SUB = 3
    ATTACHMENT = 4
    CHAPTERS = 5
    MKV = 6


@dataclass
class AudioFormat:
    format: str
    ext: str
    codecid: str
    lossy: bool = True


class DitherType(IntEnum):
    """
    FFMPEG Dither Methods, see https://ffmpeg.org/ffmpeg-resampler.html#Resampler-Options
    """

    RECTANGULAR = 1
    TRIANGULAR = 2  # Allegedly SoX's default
    TRIANGULAR_HP = 3
    LIPSHITZ = 4
    SHIBATA = 5  # Foobar uses this for example
    LOW_SHIBATA = 6
    HIGH_SHIBATA = 7
    F_WEIGHTED = 8
    MODIFIED_E_WEIGHTED = 9
    IMPROVED_E_WEIGHTED = 10


class qAAC_MODE(IntEnum):
    TVBR = 1
    CVBR = 2
    ABR = 3
    CBR = 4


@dataclass
class AudioFrame:
    """
    A dataclass representing ffmpeg's `ashowdata` filter output.

    :param n:           The (sequential) number of the input frame, starting from 0
    :param pts:         The presentation timestamp of the input frame, in time base units
                        the time base depends on the filter input pad, and is usually 1/sample_rate

    :param pts_time:    The presentation timestamp of the input frame in seconds
    :param num_samples: Number of samples in a frame (can also be refered to as frame length or size)
    """

    n: int
    pts: int
    pts_time: float
    num_samples: int


@dataclass
class AudioStats:
    """
    A dataclass representing ffmpeg's `astats` filter output.

    Too many attributes to document to be honest.

    See https://ffmpeg.org/ffmpeg-filters.html#astats-1
    """

    dc_offset: float = 0.0
    min_level: float = 0.0
    max_level: float = 0.0
    min_difference: float = 0.0
    max_difference: float = 0.0
    mean_difference: float = 0.0
    rms_difference: float = 0.0
    peak_level_db: float = 0.0
    rms_level_db: float = 0.0
    rms_peak_db: float = 0.0
    rms_trough_db: float = 0.0
    flat_factor: float = 0.0
    peak_count: float = 0.0
    noise_floor_db: float = 0.0
    noise_floor_count: float = 0.0
    entropy: float = 0.0
    bit_depth: str = ""
    number_of_samples: int = 0


@dataclass
class AudioInfo:
    stats: AudioStats = None
    frames: list[AudioFrame] | None = None

    def num_samples(self) -> int:
        for frame in self.frames:
            if frame.num_samples:
                return frame.num_samples
