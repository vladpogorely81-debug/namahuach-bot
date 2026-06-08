STAGE_STAKES = {
    "group": 10,
    "r32":   20,
    "r16":   30,
    "qf":    40,
    "sf":    50,
    "final": 100,
}

# "Bonus" exact scores that pay x2
BONUS_EXACT = {(1,0),(0,1),(1,1),(2,1),(1,2),(2,2)}

def calculate_result(bet1: int, bet2: int, score1: int, score2: int, stake: int) -> dict:
    total_goals = score1 + score2

    # Exact score
    if bet1 == score1 and bet2 == score2:
        if total_goals > 4:
            return {"delta": stake * 2, "label": "х3 (голів >4) 🔥"}
        elif (bet1, bet2) in BONUS_EXACT:
            return {"delta": stake, "label": "х2 (точний рахунок) ✨"}
        else:
            return {"delta": stake, "label": "х2 ✅"}

    # Goal difference match (but not exact score)
    diff_bet = bet1 - bet2
    diff_real = score1 - score2
    if diff_bet == diff_real and diff_bet != 0:
        return {"delta": 0, "label": "повернення (різниця голів) ↩️"}

    # Correct winner or draw
    winner_bet = 1 if bet1 > bet2 else (2 if bet2 > bet1 else 0)
    winner_real = 1 if score1 > score2 else (2 if score2 > score1 else 0)
    if winner_bet == winner_real:
        return {"delta": -(stake // 2), "label": "−50% (вгадав переможця) ✅"}

    # Wrong
    return {"delta": -stake, "label": "в банк ❌"}
