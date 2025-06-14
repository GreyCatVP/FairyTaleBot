def is_story_complete(text: str) -> bool:
    if len(text) < 1300:
        return False
    endings = [
        "Вот и сказке конец",
        "И жили они долго и счастливо",
        "Так закончилась их история",
        "А на этом сказка заканчивается"
    ]
    return any(ending in text for ending in endings)