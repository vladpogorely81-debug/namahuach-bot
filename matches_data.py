from scoring import STAGE_STAKES

# World Cup 2026 Group Stage — all 48 teams, 12 groups
# Source: FIFA official draw December 2025

WC2026_MATCHES = [
    # ── GROUP A ──────────────────────────────────────────────────
    {"team1": "Мексика",        "team2": "ПАР",          "stage": "group", "stage_name": "Група A", "stake": 10, "date": "11 черв."},
    {"team1": "Пд. Корея",      "team2": "Чехія",        "stage": "group", "stage_name": "Група A", "stake": 10, "date": "11 черв."},
    {"team1": "Мексика",        "team2": "Пд. Корея",    "stage": "group", "stage_name": "Група A", "stake": 10, "date": "15 черв."},
    {"team1": "Чехія",          "team2": "ПАР",          "stage": "group", "stage_name": "Група A", "stake": 10, "date": "15 черв."},
    {"team1": "Мексика",        "team2": "Чехія",        "stage": "group", "stage_name": "Група A", "stake": 10, "date": "19 черв."},
    {"team1": "ПАР",            "team2": "Пд. Корея",    "stage": "group", "stage_name": "Група A", "stake": 10, "date": "19 черв."},

    # ── GROUP B ──────────────────────────────────────────────────
    {"team1": "Канада",         "team2": "Боснія",       "stage": "group", "stage_name": "Група B", "stake": 10, "date": "12 черв."},
    {"team1": "Катар",          "team2": "Швейцарія",    "stage": "group", "stage_name": "Група B", "stake": 10, "date": "13 черв."},
    {"team1": "Канада",         "team2": "Катар",        "stage": "group", "stage_name": "Група B", "stake": 10, "date": "17 черв."},
    {"team1": "Швейцарія",      "team2": "Боснія",       "stage": "group", "stage_name": "Група B", "stake": 10, "date": "17 черв."},
    {"team1": "Канада",         "team2": "Швейцарія",    "stage": "group", "stage_name": "Група B", "stake": 10, "date": "21 черв."},
    {"team1": "Боснія",         "team2": "Катар",        "stage": "group", "stage_name": "Група B", "stake": 10, "date": "21 черв."},

    # ── GROUP C ──────────────────────────────────────────────────
    {"team1": "Бразилія",       "team2": "Марокко",      "stage": "group", "stage_name": "Група C", "stake": 10, "date": "13 черв."},
    {"team1": "Гаїті",          "team2": "Шотландія",    "stage": "group", "stage_name": "Група C", "stake": 10, "date": "13 черв."},
    {"team1": "Бразилія",       "team2": "Гаїті",        "stage": "group", "stage_name": "Група C", "stake": 10, "date": "17 черв."},
    {"team1": "Шотландія",      "team2": "Марокко",      "stage": "group", "stage_name": "Група C", "stake": 10, "date": "17 черв."},
    {"team1": "Бразилія",       "team2": "Шотландія",    "stage": "group", "stage_name": "Група C", "stake": 10, "date": "22 черв."},
    {"team1": "Марокко",        "team2": "Гаїті",        "stage": "group", "stage_name": "Група C", "stake": 10, "date": "22 черв."},

    # ── GROUP D ──────────────────────────────────────────────────
    {"team1": "США",            "team2": "Парагвай",     "stage": "group", "stage_name": "Група D", "stake": 10, "date": "12 черв."},
    {"team1": "Австралія",      "team2": "Індія",        "stage": "group", "stage_name": "Група D", "stake": 10, "date": "13 черв."},
    {"team1": "США",            "team2": "Австралія",    "stage": "group", "stage_name": "Група D", "stake": 10, "date": "17 черв."},
    {"team1": "Індія",          "team2": "Парагвай",     "stage": "group", "stage_name": "Група D", "stake": 10, "date": "18 черв."},
    {"team1": "США",            "team2": "Індія",        "stage": "group", "stage_name": "Група D", "stake": 10, "date": "22 черв."},
    {"team1": "Парагвай",       "team2": "Австралія",    "stage": "group", "stage_name": "Група D", "stake": 10, "date": "22 черв."},

    # ── GROUP E ──────────────────────────────────────────────────
    {"team1": "Іспанія",        "team2": "Кабо-Верде",   "stage": "group", "stage_name": "Група E", "stake": 10, "date": "15 черв."},
    {"team1": "Саудівська Ар.", "team2": "Уругвай",      "stage": "group", "stage_name": "Група E", "stake": 10, "date": "15 черв."},
    {"team1": "Іспанія",        "team2": "Саудівська Ар.","stage":"group", "stage_name": "Група E", "stake": 10, "date": "19 черв."},
    {"team1": "Уругвай",        "team2": "Кабо-Верде",   "stage": "group", "stage_name": "Група E", "stake": 10, "date": "20 черв."},
    {"team1": "Іспанія",        "team2": "Уругвай",      "stage": "group", "stage_name": "Група E", "stake": 10, "date": "24 черв."},
    {"team1": "Кабо-Верде",     "team2": "Саудівська Ар.","stage":"group", "stage_name": "Група E", "stake": 10, "date": "24 черв."},

    # ── GROUP F ──────────────────────────────────────────────────
    {"team1": "Португалія",     "team2": "Ірак",         "stage": "group", "stage_name": "Група F", "stake": 10, "date": "14 черв."},
    {"team1": "Хорватія",       "team2": "Танзанія",     "stage": "group", "stage_name": "Група F", "stake": 10, "date": "15 черв."},
    {"team1": "Португалія",     "team2": "Хорватія",     "stage": "group", "stage_name": "Група F", "stake": 10, "date": "19 черв."},
    {"team1": "Танзанія",       "team2": "Ірак",         "stage": "group", "stage_name": "Група F", "stake": 10, "date": "19 черв."},
    {"team1": "Португалія",     "team2": "Танзанія",     "stage": "group", "stage_name": "Група F", "stake": 10, "date": "24 черв."},
    {"team1": "Ірак",           "team2": "Хорватія",     "stage": "group", "stage_name": "Група F", "stake": 10, "date": "24 черв."},

    # ── GROUP G ──────────────────────────────────────────────────
    {"team1": "Бельгія",        "team2": "Єгипет",       "stage": "group", "stage_name": "Група G", "stake": 10, "date": "15 черв."},
    {"team1": "Іран",           "team2": "Нова Зеландія","stage": "group", "stage_name": "Група G", "stake": 10, "date": "15 черв."},
    {"team1": "Бельгія",        "team2": "Іран",         "stage": "group", "stage_name": "Група G", "stake": 10, "date": "19 черв."},
    {"team1": "Нова Зеландія",  "team2": "Єгипет",       "stage": "group", "stage_name": "Група G", "stake": 10, "date": "20 черв."},
    {"team1": "Бельгія",        "team2": "Нова Зеландія","stage": "group", "stage_name": "Група G", "stake": 10, "date": "24 черв."},
    {"team1": "Єгипет",         "team2": "Іран",         "stage": "group", "stage_name": "Група G", "stake": 10, "date": "24 черв."},

    # ── GROUP H ──────────────────────────────────────────────────
    {"team1": "Нідерланди",     "team2": "Перу",         "stage": "group", "stage_name": "Група H", "stake": 10, "date": "14 черв."},
    {"team1": "Туреччина",      "team2": "Чилі",         "stage": "group", "stage_name": "Група H", "stake": 10, "date": "14 черв."},
    {"team1": "Нідерланди",     "team2": "Туреччина",    "stage": "group", "stage_name": "Група H", "stake": 10, "date": "18 черв."},
    {"team1": "Чилі",           "team2": "Перу",         "stage": "group", "stage_name": "Група H", "stake": 10, "date": "19 черв."},
    {"team1": "Нідерланди",     "team2": "Чилі",         "stage": "group", "stage_name": "Група H", "stake": 10, "date": "23 черв."},
    {"team1": "Перу",           "team2": "Туреччина",    "stage": "group", "stage_name": "Група H", "stake": 10, "date": "23 черв."},

    # ── GROUP I ──────────────────────────────────────────────────
    {"team1": "Франція",        "team2": "Сенегал",      "stage": "group", "stage_name": "Група I", "stake": 10, "date": "16 черв."},
    {"team1": "Ірак",           "team2": "Норвегія",     "stage": "group", "stage_name": "Група I", "stake": 10, "date": "16 черв."},
    {"team1": "Франція",        "team2": "Ірак",         "stage": "group", "stage_name": "Група I", "stake": 10, "date": "20 черв."},
    {"team1": "Норвегія",       "team2": "Сенегал",      "stage": "group", "stage_name": "Група I", "stake": 10, "date": "21 черв."},
    {"team1": "Франція",        "team2": "Норвегія",     "stage": "group", "stage_name": "Група I", "stake": 10, "date": "25 черв."},
    {"team1": "Сенегал",        "team2": "Ірак",         "stage": "group", "stage_name": "Група I", "stake": 10, "date": "25 черв."},

    # ── GROUP J ──────────────────────────────────────────────────
    {"team1": "Аргентина",      "team2": "Албанія",      "stage": "group", "stage_name": "Група J", "stake": 10, "date": "16 черв."},
    {"team1": "Нігерія",        "team2": "Венесуела",    "stage": "group", "stage_name": "Група J", "stake": 10, "date": "16 черв."},
    {"team1": "Аргентина",      "team2": "Нігерія",      "stage": "group", "stage_name": "Група J", "stake": 10, "date": "20 черв."},
    {"team1": "Венесуела",      "team2": "Албанія",      "stage": "group", "stage_name": "Група J", "stake": 10, "date": "21 черв."},
    {"team1": "Аргентина",      "team2": "Венесуела",    "stage": "group", "stage_name": "Група J", "stake": 10, "date": "25 черв."},
    {"team1": "Албанія",        "team2": "Нігерія",      "stage": "group", "stage_name": "Група J", "stake": 10, "date": "25 черв."},

    # ── GROUP K ──────────────────────────────────────────────────
    {"team1": "Германія",       "team2": "Саудівська Ар.","stage":"group", "stage_name": "Група K", "stake": 10, "date": "14 черв."},
    {"team1": "Японія",         "team2": "Камерун",      "stage": "group", "stage_name": "Група K", "stake": 10, "date": "14 черв."},
    {"team1": "Германія",       "team2": "Японія",       "stage": "group", "stage_name": "Група K", "stake": 10, "date": "18 черв."},
    {"team1": "Камерун",        "team2": "Саудівська Ар.","stage":"group", "stage_name": "Група K", "stake": 10, "date": "19 черв."},
    {"team1": "Германія",       "team2": "Камерун",      "stage": "group", "stage_name": "Група K", "stake": 10, "date": "23 черв."},
    {"team1": "Саудівська Ар.", "team2": "Японія",       "stage": "group", "stage_name": "Група K", "stake": 10, "date": "23 черв."},

    # ── GROUP L ──────────────────────────────────────────────────
    {"team1": "Англія",         "team2": "Сербія",       "stage": "group", "stage_name": "Група L", "stake": 10, "date": "16 черв."},
    {"team1": "Колумбія",       "team2": "Кот-д'Івуар",  "stage": "group", "stage_name": "Група L", "stake": 10, "date": "17 черв."},
    {"team1": "Англія",         "team2": "Колумбія",     "stage": "group", "stage_name": "Група L", "stake": 10, "date": "21 черв."},
    {"team1": "Кот-д'Івуар",    "team2": "Сербія",       "stage": "group", "stage_name": "Група L", "stake": 10, "date": "21 черв."},
    {"team1": "Англія",         "team2": "Кот-д'Івуар",  "stage": "group", "stage_name": "Група L", "stake": 10, "date": "25 черв."},
    {"team1": "Сербія",         "team2": "Колумбія",     "stage": "group", "stage_name": "Група L", "stake": 10, "date": "26 черв."},
]

def get_upcoming_matches():
    return WC2026_MATCHES

def get_match_by_id(match_id):
    if 1 <= match_id <= len(WC2026_MATCHES):
        return WC2026_MATCHES[match_id - 1]
    return None
