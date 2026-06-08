from scoring import STAGE_STAKES

# World Cup 2026 — офіційний розклад (джерело: terrikon.com, ESPN)
# Дати у форматі DD.MM, час київський (UTC+3)

WC2026_MATCHES = [
    # ── ГРУПА A ──────────────────────────────────────────────
    {"team1": "Мексика",      "team2": "ПАР",          "stage": "group", "stage_name": "Група A", "stake": 10, "date": "12.06 01:00"},
    {"team1": "Пд.Корея",     "team2": "Чехія",        "stage": "group", "stage_name": "Група A", "stake": 10, "date": "12.06 08:00"},
    {"team1": "Чехія",        "team2": "ПАР",          "stage": "group", "stage_name": "Група A", "stake": 10, "date": "18.06 22:00"},
    {"team1": "Мексика",      "team2": "Пд.Корея",     "stage": "group", "stage_name": "Група A", "stake": 10, "date": "19.06 07:00"},
    {"team1": "Чехія",        "team2": "Мексика",      "stage": "group", "stage_name": "Група A", "stake": 10, "date": "25.06 07:00"},
    {"team1": "ПАР",          "team2": "Пд.Корея",     "stage": "group", "stage_name": "Група A", "stake": 10, "date": "25.06 07:00"},

    # ── ГРУПА B ──────────────────────────────────────────────
    {"team1": "Канада",       "team2": "Боснія",       "stage": "group", "stage_name": "Група B", "stake": 10, "date": "13.06 01:00"},
    {"team1": "Катар",        "team2": "Швейцарія",    "stage": "group", "stage_name": "Група B", "stake": 10, "date": "14.06 01:00"},
    {"team1": "Швейцарія",    "team2": "Боснія",       "stage": "group", "stage_name": "Група B", "stake": 10, "date": "19.06 01:00"},
    {"team1": "Канада",       "team2": "Катар",        "stage": "group", "stage_name": "Група B", "stake": 10, "date": "19.06 04:00"},
    {"team1": "Швейцарія",    "team2": "Канада",       "stage": "group", "stage_name": "Група B", "stake": 10, "date": "25.06 01:00"},
    {"team1": "Боснія",       "team2": "Катар",        "stage": "group", "stage_name": "Група B", "stake": 10, "date": "25.06 01:00"},

    # ── ГРУПА C ──────────────────────────────────────────────
    {"team1": "Бразилія",     "team2": "Марокко",      "stage": "group", "stage_name": "Група C", "stake": 10, "date": "14.06 04:00"},
    {"team1": "Гаїті",        "team2": "Шотландія",    "stage": "group", "stage_name": "Група C", "stake": 10, "date": "14.06 07:00"},
    {"team1": "Шотландія",    "team2": "Марокко",      "stage": "group", "stage_name": "Група C", "stake": 10, "date": "20.06 04:00"},
    {"team1": "Бразилія",     "team2": "Гаїті",        "stage": "group", "stage_name": "Група C", "stake": 10, "date": "20.06 06:30"},
    {"team1": "Шотландія",    "team2": "Бразилія",     "stage": "group", "stage_name": "Група C", "stake": 10, "date": "26.06 04:00"},
    {"team1": "Марокко",      "team2": "Гаїті",        "stage": "group", "stage_name": "Група C", "stake": 10, "date": "26.06 04:00"},

    # ── ГРУПА D ──────────────────────────────────────────────
    {"team1": "США",          "team2": "Парагвай",     "stage": "group", "stage_name": "Група D", "stake": 10, "date": "13.06 07:00"},
    {"team1": "Австралія",    "team2": "Туреччина",    "stage": "group", "stage_name": "Група D", "stake": 10, "date": "14.06 10:00"},
    {"team1": "США",          "team2": "Австралія",    "stage": "group", "stage_name": "Група D", "stake": 10, "date": "20.06 01:00"},
    {"team1": "Туреччина",    "team2": "Парагвай",     "stage": "group", "stage_name": "Група D", "stake": 10, "date": "20.06 09:00"},
    {"team1": "Туреччина",    "team2": "США",          "stage": "group", "stage_name": "Група D", "stake": 10, "date": "26.06 08:00"},
    {"team1": "Парагвай",     "team2": "Австралія",    "stage": "group", "stage_name": "Група D", "stake": 10, "date": "26.06 08:00"},

    # ── ГРУПА E ──────────────────────────────────────────────
    {"team1": "Германія",     "team2": "Кюрасао",      "stage": "group", "stage_name": "Група E", "stake": 10, "date": "14.06 23:00"},
    {"team1": "Кот-д'Івуар", "team2": "Еквадор",      "stage": "group", "stage_name": "Група E", "stake": 10, "date": "15.06 05:00"},
    {"team1": "Германія",     "team2": "Кот-д'Івуар", "stage": "group", "stage_name": "Група E", "stake": 10, "date": "21.06 02:00"},
    {"team1": "Еквадор",      "team2": "Кюрасао",      "stage": "group", "stage_name": "Група E", "stake": 10, "date": "21.06 06:00"},
    {"team1": "Кюрасао",      "team2": "Кот-д'Івуар", "stage": "group", "stage_name": "Група E", "stake": 10, "date": "26.06 02:00"},
    {"team1": "Еквадор",      "team2": "Германія",     "stage": "group", "stage_name": "Група E", "stake": 10, "date": "26.06 02:00"},

    # ── ГРУПА F ──────────────────────────────────────────────
    {"team1": "Нідерланди",   "team2": "Японія",       "stage": "group", "stage_name": "Група F", "stake": 10, "date": "15.06 02:00"},
    {"team1": "Швеція",       "team2": "Туніс",        "stage": "group", "stage_name": "Група F", "stake": 10, "date": "15.06 08:00"},
    {"team1": "Нідерланди",   "team2": "Швеція",       "stage": "group", "stage_name": "Група F", "stake": 10, "date": "20.06 23:00"},
    {"team1": "Туніс",        "team2": "Японія",       "stage": "group", "stage_name": "Група F", "stake": 10, "date": "21.06 10:00"},
    {"team1": "Туніс",        "team2": "Нідерланди",   "stage": "group", "stage_name": "Група F", "stake": 10, "date": "26.06 05:00"},
    {"team1": "Японія",       "team2": "Швеція",       "stage": "group", "stage_name": "Група F", "stake": 10, "date": "26.06 05:00"},

    # ── ГРУПА G ──────────────────────────────────────────────
    {"team1": "Бельгія",      "team2": "Єгипет",       "stage": "group", "stage_name": "Група G", "stake": 10, "date": "16.06 01:00"},
    {"team1": "Іран",         "team2": "Нова Зеландія","stage": "group", "stage_name": "Група G", "stake": 10, "date": "16.06 07:00"},
    {"team1": "Бельгія",      "team2": "Іран",         "stage": "group", "stage_name": "Група G", "stake": 10, "date": "22.06 01:00"},
    {"team1": "Нова Зеландія","team2": "Єгипет",       "stage": "group", "stage_name": "Група G", "stake": 10, "date": "22.06 07:00"},
    {"team1": "Єгипет",       "team2": "Іран",         "stage": "group", "stage_name": "Група G", "stake": 10, "date": "27.06 09:00"},
    {"team1": "Нова Зеландія","team2": "Бельгія",      "stage": "group", "stage_name": "Група G", "stake": 10, "date": "27.06 09:00"},

    # ── ГРУПА H ──────────────────────────────────────────────
    {"team1": "Іспанія",      "team2": "Кабо-Верде",   "stage": "group", "stage_name": "Група H", "stake": 10, "date": "15.06 22:00"},
    {"team1": "Саудівська Ар.","team2": "Уругвай",     "stage": "group", "stage_name": "Група H", "stake": 10, "date": "16.06 04:00"},
    {"team1": "Іспанія",      "team2": "Саудівська Ар.","stage":"group", "stage_name": "Група H", "stake": 10, "date": "21.06 22:00"},
    {"team1": "Уругвай",      "team2": "Кабо-Верде",   "stage": "group", "stage_name": "Група H", "stake": 10, "date": "22.06 04:00"},
    {"team1": "Кабо-Верде",   "team2": "Саудівська Ар.","stage":"group", "stage_name": "Група H", "stake": 10, "date": "27.06 06:00"},
    {"team1": "Уругвай",      "team2": "Іспанія",      "stage": "group", "stage_name": "Група H", "stake": 10, "date": "27.06 06:00"},

    # ── ГРУПА I ──────────────────────────────────────────────
    {"team1": "Франція",      "team2": "Сенегал",      "stage": "group", "stage_name": "Група I", "stake": 10, "date": "17.06 01:00"},
    {"team1": "Ірак",         "team2": "Норвегія",     "stage": "group", "stage_name": "Група I", "stake": 10, "date": "17.06 04:00"},
    {"team1": "Франція",      "team2": "Ірак",         "stage": "group", "stage_name": "Група I", "stake": 10, "date": "23.06 02:59"},
    {"team1": "Норвегія",     "team2": "Сенегал",      "stage": "group", "stage_name": "Група I", "stake": 10, "date": "23.06 06:00"},
    {"team1": "Норвегія",     "team2": "Франція",      "stage": "group", "stage_name": "Група I", "stake": 10, "date": "27.06 01:00"},
    {"team1": "Сенегал",      "team2": "Ірак",         "stage": "group", "stage_name": "Група I", "stake": 10, "date": "27.06 01:00"},

    # ── ГРУПА J ──────────────────────────────────────────────
    {"team1": "Аргентина",    "team2": "Алжир",        "stage": "group", "stage_name": "Група J", "stake": 10, "date": "17.06 07:00"},
    {"team1": "Австрія",      "team2": "Йорданія",     "stage": "group", "stage_name": "Група J", "stake": 10, "date": "17.06 10:00"},
    {"team1": "Аргентина",    "team2": "Австрія",      "stage": "group", "stage_name": "Група J", "stake": 10, "date": "22.06 23:00"},
    {"team1": "Йорданія",     "team2": "Алжир",        "stage": "group", "stage_name": "Група J", "stake": 10, "date": "23.06 09:00"},
    {"team1": "Алжир",        "team2": "Австрія",      "stage": "group", "stage_name": "Група J", "stake": 10, "date": "28.06 08:00"},
    {"team1": "Йорданія",     "team2": "Аргентина",    "stage": "group", "stage_name": "Група J", "stake": 10, "date": "28.06 08:00"},

    # ── ГРУПА K ──────────────────────────────────────────────
    {"team1": "Португалія",   "team2": "ДР Конго",     "stage": "group", "stage_name": "Група K", "stake": 10, "date": "17.06 23:00"},
    {"team1": "Узбекистан",   "team2": "Колумбія",     "stage": "group", "stage_name": "Група K", "stake": 10, "date": "18.06 08:00"},
    {"team1": "Португалія",   "team2": "Узбекистан",   "stage": "group", "stage_name": "Група K", "stake": 10, "date": "23.06 23:00"},
    {"team1": "Колумбія",     "team2": "ДР Конго",     "stage": "group", "stage_name": "Група K", "stake": 10, "date": "24.06 08:00"},
    {"team1": "Колумбія",     "team2": "Португалія",   "stage": "group", "stage_name": "Група K", "stake": 10, "date": "28.06 05:30"},
    {"team1": "ДР Конго",     "team2": "Узбекистан",   "stage": "group", "stage_name": "Група K", "stake": 10, "date": "28.06 05:30"},

    # ── ГРУПА L ──────────────────────────────────────────────
    {"team1": "Англія",       "team2": "Хорватія",     "stage": "group", "stage_name": "Група L", "stake": 10, "date": "18.06 02:00"},
    {"team1": "Гана",         "team2": "Панама",       "stage": "group", "stage_name": "Група L", "stake": 10, "date": "18.06 05:00"},
    {"team1": "Англія",       "team2": "Гана",         "stage": "group", "stage_name": "Група L", "stake": 10, "date": "24.06 02:00"},
    {"team1": "Панама",       "team2": "Хорватія",     "stage": "group", "stage_name": "Група L", "stake": 10, "date": "24.06 05:00"},
    {"team1": "Панама",       "team2": "Англія",       "stage": "group", "stage_name": "Група L", "stake": 10, "date": "28.06 02:59"},
    {"team1": "Хорватія",     "team2": "Гана",         "stage": "group", "stage_name": "Група L", "stake": 10, "date": "28.06 02:59"},
]

def get_upcoming_matches():
    return WC2026_MATCHES

def get_match_by_id(match_id):
    if 1 <= match_id <= len(WC2026_MATCHES):
        return WC2026_MATCHES[match_id - 1]
    return None
