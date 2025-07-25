from enum import Enum
from typing import TypedDict


class SlotFormat(TypedDict):
    show_min_duration: int
    show_max_duration: int
    slot_duration: int


class CategoryCriteria(str, Enum):
    GENRE = "genre"
    TYPE = "type"
    LANGUAGE = "language"

    DURATION = "duration"


class Criteria(TypedDict):
    category: CategoryCriteria
    values: list[str | int | float]


class Show(TypedDict):
    name: str
    properties: dict[CategoryCriteria, list[str | int | float]]


class ChannelBlock(TypedDict):
    criteria: list[Criteria]
    begin: float
    end: float
    shows: list[Show]
    # slot_duration: int
    slot_count: int
    slow_format: SlotFormat


class Channel(TypedDict):
    name: str
    description: str
    blocks: list[ChannelBlock]

    # permet d'automatiser la generation aleatoire des blocks
    available_properties: dict[CategoryCriteria, list[str | int | float]]
    # available_slot_durations: list[int]
    available_slow_format: list[SlotFormat]
    available_slot_count: list[int]
    begin: int
    end: int