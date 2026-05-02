"""Делает копию данных wiki, заменяя в тексте все термины и переименовывая файлы,
чтобы LLM могла опираться только на контекст для получения информации."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from chatbot.tools.consts import DATA_DIR

ORIGINAL_DIR = DATA_DIR / "amber_wiki"
OBFUSCATED_DIR = DATA_DIR / "amber_wiki_obfuscated"


MAP_OF_TERMS = {
    "Chaos": "Tumba",
    "Order": "Umba",
    "Avalon": "Azaron",
    "Amber": "Yander",
    "Arden": "Losiniy",
    "Benedict": "Peter",
    "Black Circle": "Yellow Square",
    "Black Road": "Dark Highway",
    "Borel": "Rogov",
    "Brand": "Jon",
    "Caine": "Avel",
    "Clarrisa": "Krisa",
    "Coral": "Klara",
    "Corwin": "Pavel",
    "Cymnea": "Lyudmila",
    "Dalt": "Balt",
    "Dara": "O'Briain",
    "Deidre": "Irina",
    "Dworkin": "Qweryin",
    "Eric": "Kripke",
    "Faiella": "Lera",
    "Finndo": "Tomre",
    "Fiona": "Shriona",
    "Frakir": "Glukometerir",
    "Ganelon": "Alfred",
    "Lorraine": "Aravia",
    "Gerard": "Gattler",
    "Ghostwheel": "Spiritcircle",
    "Grayswandir": "White Lance",
    "Jasra": "Yaga",
    "Joplin": "Scott",
    "Julia": "Roberta",
    "Julian": "Robert",
    "Llewella": "Ciwilla",
    "Logrus": "Tumbatorium",
    "Luke": "Mark",
    "Mandor": "Secundus",
    "Martin": "Freeman",
    "Merlin": "Moorlin",
    "Moire": "Muira",
    "Morgenstern": "Inagentiy",
    "Oberon": "Chronoron",
    "Osric": "Oslic",
    "Remba": "Bara",
    "Rilga": "Regelia",
    "Spikard": "Pikard",
    "Strygalldwir": "Megaolen",
    "Sukuy": "Mukoyan",
    "Swayvill": "Swaili",
    "Tir-na Nog'th": "Notr Na'th",
    "Ty'iga": "Tigana",
    "Vinta Bayle": "Daiana Blake",
    "Werewindle": "Wasswindle",
    "Roger": "Charli",
    "Zelazny": "Derevanny",
    # для замены в ссылках на амбер wiki
    "amber": "yander",
    "princeofamber": "princeofyander",
}


def _compile_term_pattern(term: str) -> re.Pattern[str]:
    """Целое вхождение: слева/справа не латинские буквы и не цифры
    (подчёркивание — не часть имени: в путях wiki разделяет слова)."""
    return re.compile(rf"(?<![A-Za-z0-9]){re.escape(term)}(?=('s|s(?![A-Za-z0-9])|(?![A-Za-z0-9])))")


def replace_terms_in_text(text: str, mapping: dict[str, str] | None = None) -> str:
    mapping = mapping or MAP_OF_TERMS
    pairs = sorted(mapping.items(), key=lambda item: (-len(item[0]), item[0]))
    result = text
    for term, replacement in pairs:
        result = _compile_term_pattern(term).sub(replacement, result)
    return result


def rename_files(source_dir: Path) -> None:
    paths = sorted(
        (p for p in source_dir.rglob("*") if p.is_file()),
        key=lambda p: (-len(p.parts), len(str(p))),
    )
    for path in paths:
        new_name = replace_terms_in_text(path.name)
        if new_name != path.name:
            path.rename(path.parent / new_name)


def obfuscate_text(source_dir: Path) -> None:
    for file in source_dir.rglob("*"):
        if file.is_dir():
            continue
        text = file.read_text(encoding="utf-8")
        file.write_text(replace_terms_in_text(text), encoding="utf-8")


if __name__ == "__main__":
    shutil.rmtree(OBFUSCATED_DIR, ignore_errors=True)
    shutil.copytree(ORIGINAL_DIR, OBFUSCATED_DIR)
    rename_files(Path(OBFUSCATED_DIR))
    obfuscate_text(Path(OBFUSCATED_DIR))
