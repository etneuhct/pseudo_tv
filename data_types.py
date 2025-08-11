from enum import Enum
from typing import TypedDict, Optional


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
    forbidden: bool

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
    slot_format: SlotFormat


class Channel(TypedDict):
    name: str
    description: str # totalement inutile pour l'instant, mais qui sait...
    blocks: list[ChannelBlock]
    fillers: list[str] # pas utilisé lors de la génération aléatoire pour l'instant
    logo: Optional[str]
    # permet d'automatiser la generation aleatoire des blocks
    available_properties: dict[CategoryCriteria, list[str | int | float]]
    available_slot_format: list[SlotFormat]
    available_slot_count: list[int]
    begin: int
    end: int

class Catalog(TypedDict):
    name: str
    step: int
    channels: list[Channel]


class CatalogGenerationStep:
    init = 0
    generation = 1
    config = 2
    super_category = 1