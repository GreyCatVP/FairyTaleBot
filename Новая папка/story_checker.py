def is_story_complete(text: str) -> bool:
    if len(text) < 1300:
        return False

    endings = [
        "Вот и сказке конец",
        "И жили они долго и счастливо",
        "Так закончилась их история",
        "А на этом сказка заканчивается",
        "И с тех пор жили мирно",
        "И никто их больше не тревожил",
        "И всё было хорошо",
        "С тех пор каждый день был добрым",
        "Так закончилась добрая сказка",
        "Сказка подошла к концу",
        "Так закончилась история про"
    ]

    text_lower = text.lower().strip()
    if any(text_lower.endswith(ending.lower()) for ending in endings):
        return True
    if len(text) > 1500 and text.strip().endswith("."):
        return True
    return False