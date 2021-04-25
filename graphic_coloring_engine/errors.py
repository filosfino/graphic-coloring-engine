from dataclasses import dataclass


@dataclass
class ColoringEngineError(Exception):
    msg: str
