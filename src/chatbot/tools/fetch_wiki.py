import requests
import json
from urllib.parse import quote
from chatbot.tools.consts import DATA_DIR

API_URL = "https://princeofamber.fandom.com/api.php"
DESTINATION_DIR = DATA_DIR / "amber_wiki" / "pages"


def fetch_all_pages() -> list[dict]:
    pages = []
    params = {
        "action": "query",
        "list": "allpages",
        "apnamespace": 0,
        "aplimit": "max",
        "format": "json",
    }

    while True:
        response = requests.get(API_URL, params=params, timeout=20)  # type: ignore[arg-type]
        response.raise_for_status()
        data = response.json()

        pages.extend(data["query"]["allpages"])

        if "continue" not in data:
            break

        params.update(data["continue"])

    return pages


def fetch_page_html(title: str) -> dict:
    params = {
        "action": "parse",
        "page": title,
        "prop": "text|sections|links",
        "format": "json",
        "formatversion": "2",
        "redirects": "1",
    }

    response = requests.get(API_URL, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    return {
        "title": data["parse"]["title"],
        "pageid": data["parse"]["pageid"],
        "html": data["parse"]["text"],
        "sections": data["parse"].get("sections", []),
        "links": data["parse"].get("links", []),
        "url": f"https://amber.fandom.com/ru/wiki/{quote(title.replace(' ', '_'))}",
    }


pages = fetch_all_pages()
page_titles = [
    page["title"]
    for page in pages
    if page["title"] not in {"Amberpedia Manual of Style", "Amberpedia Wiki", "Main Page"}
]
DESTINATION_DIR.mkdir(parents=True, exist_ok=True)
for page_title in page_titles:
    result = fetch_page_html(page_title)
    with open(DESTINATION_DIR / f"{page_title}.json", "w") as f:
        json.dump(result, f, ensure_ascii=False)
