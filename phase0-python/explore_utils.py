def extract_author(data: dict) -> str:
    return data["slideshow"]["author"]


def summarize_slideshow(data: dict) -> dict:
    return data["slideshow"]
