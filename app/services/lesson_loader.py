from app.lessons import ru_en, ru_ko, uz_en, uz_ko

MAP = {
    ("ru", "en"): ru_en.LESSONS,
    ("ru", "ko"): ru_ko.LESSONS,
    ("uz", "en"): uz_en.LESSONS,
    ("uz", "ko"): uz_ko.LESSONS,
}

def get_lessons(native, foreign):
    return MAP[(native, foreign)]
