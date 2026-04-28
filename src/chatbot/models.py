from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DataChunk:
    file_name: str
    title: str
    text: str
