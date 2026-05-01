from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DataChunk:
    page_title: str
    sections: str
    text: str
