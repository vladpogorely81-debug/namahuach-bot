import sqlite3
from scoring import calculate_result, STAGE_STAKES
from matches_data import WC2026_MATCHES

class Database:
    def __init__(self, path: str):
        self.path = path

    def conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def init(self):
        with self.conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    username TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team1 TEXT NOT NULL,
                    team2 TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    stage_name TEXT NOT NULL,
                    stake INTEGER NOT NULL,
                    match_date TEXT,
                    score1 INTEGER DEFAULT NULL,
                    score2 INTEGER DEFAULT NULL,
                    is_open INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS bets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    match_id INTEGER NOT NULL,
                    bet1 INTEGER NOT NULL,
                    bet2 INTEGER NOT NULL,
                    result_delta INTEGER DEFAULT NULL,
                    result_label TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, match_id),
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    FOREIGN KEY(match_id) REFERENCES matches(id)
                );
            """)

    def seed_wc2026_matches(self):
        with self.conn() as c:
            count = c.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
            if count > 0:
                return
            for m in WC2026_MATCHES:
                c.execute(
                    "INSERT INTO matches (team1, team2, stage, stage_name, stake, match_date) VALUES (?,?,?,?,?,?)",
                    (m['team1'], m['team2'], m['stage'], m['stage_name'], m['stake'], m['date'])
                )

    def register_user(self, user_id, name, username):
        with self.conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO users (user_id, name, username) VALUES (?,?,?)",
                (user_id, name, username)
            )
            c.execute(
                "UPDATE users SET name=?, username=? WHERE user_id=?",
                (name, username, user_id)
            )

    def get_all_users(self):
        with self.conn() as c:
            return c.execute("SELECT user_id FROM users").fetchall()

    def get_match(self, match_id):
        with self.conn() as c:
            return c.execute("SELECT * FROM matches WHERE id=?", (match_id,)).fetchone()

    def get_all_matches(self):
        with self.conn() as c:
            return c.execute("SELECT * FROM matches ORDER BY id").fetchall()

    def get_upcoming_matches_with_bets(self, user_id):
        with self.conn() as c:
            rows = c.execute("""
                SELECT m.*, b.bet1, b.bet2
                FROM matches m
                LEFT JOIN bets b ON b.match_id = m.id AND b.user_id = ?
                WHERE m.is_open = 1
                ORDER BY m.id
                LIMIT 20
            """, (user_id,)).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                if d.get('bet1') is not None:
                    d['user_bet'] = f"{d['bet1']}:{d['bet2']}"
                else:
                    d['user_bet'] = None
                result.append(d)
            return result

    def get_open_matches_for_betting(self, user_id):
        with self.conn() as c:
            return c.execute("""
                SELECT m.*
                FROM matches m
                WHERE m.is_open = 1
                  AND m.score1 IS NULL
                  AND m.id NOT IN (
                    SELECT match_id FROM bets WHERE user_id = ?
                  )
                ORDER BY m.id
                LIMIT 15
            """, (user_id,)).fetchall()

    def get_user_bet(self, user_id, match_id):
        with self.conn() as c:
            return c.execute(
                "SELECT * FROM bets WHERE user_id=? AND match_id=?",
                (user_id, match_id)
            ).fetchone()

    def place_bet(self, user_id, match_id, bet1, bet2):
        with self.conn() as c:
            c.execute(
                "INSERT INTO bets (user_id, match_id, bet1, bet2) VALUES (?,?,?,?)",
                (user_id, match_id, bet1, bet2)
            )

    def update_bet(self, user_id, match_id, bet1, bet2):
        with self.conn() as c:
            c.execute(
                "UPDATE bets SET bet1=?, bet2=?, result_delta=NULL WHERE user_id=? AND match_id=?",
                (bet1, bet2, user_id, match_id)
            )

    def add_match(self, team1, team2, stage, stage_name, stake, date):
        with self.conn() as c:
            cur = c.execute(
                "INSERT INTO matches (team1,team2,stage,stage_name,stake,match_date) VALUES (?,?,?,?,?,?)",
                (team1, team2, stage, stage_name, stake, date)
            )
            return cur.lastrowid

    def set_match_result(self, match_id, s1, s2):
        with self.conn() as c:
            c.execute(
                "UPDATE matches SET score1=?, score2=?, is_open=0 WHERE id=?",
                (s1, s2, match_id)
            )

    def calculate_and_save_results(self, match_id, s1, s2):
        with self.conn() as c:
            bets = c.execute("""
                SELECT b.*, u.name FROM bets b
                JOIN users u ON u.user_id = b.user_id
                WHERE b.match_id = ?
            """, (match_id,)).fetchall()

            match = c.execute("SELECT * FROM matches WHERE id=?", (match_id,)).fetchone()
            stake = match['stake']
            results = []

            for b in bets:
                res = calculate_result(b['bet1'], b['bet2'], s1, s2, stake)
                c.execute(
                    "UPDATE bets SET result_delta=?, result_label=? WHERE id=?",
                    (res['delta'], res['label'], b['id'])
                )
                results.append({
                    'name': b['name'],
                    'bet1': b['bet1'],
                    'bet2': b['bet2'],
                    'delta': res['delta'],
                    'label': res['label']
                })

            return results

    def get_user_stats(self, user_id):
        with self.conn() as c:
            row = c.execute("""
                SELECT
                    u.name,
                    COALESCE(SUM(b.result_delta), 0) as balance,
                    COUNT(b.id) as total_bets,
                    SUM(CASE WHEN b.result_delta > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN b.result_delta < 0 THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN b.result_delta = 0 AND b.result_delta IS NOT NULL THEN 1 ELSE 0 END) as returns
                FROM users u
                LEFT JOIN bets b ON b.user_id = u.user_id
                WHERE u.user_id = ?
            """, (user_id,)).fetchone()
            return dict(row) if row else None

    def get_standings(self):
        with self.conn() as c:
            return c.execute("""
                SELECT
                    u.name,
                    COALESCE(SUM(b.result_delta), 0) as balance,
                    COUNT(b.id) as total_bets
                FROM users u
                LEFT JOIN bets b ON b.user_id = u.user_id
                GROUP BY u.user_id
                ORDER BY balance DESC
            """).fetchall()

    def get_bank_total(self):
        with self.conn() as c:
            row = c.execute("""
                SELECT COALESCE(-SUM(result_delta), 0) as bank
                FROM bets
                WHERE result_delta IS NOT NULL
            """).fetchone()
            return max(0, row['bank'] if row else 0)

    def get_user_history(self, user_id):
        with self.conn() as c:
            return c.execute("""
                SELECT b.bet1, b.bet2, b.result_delta, b.result_label,
                       m.team1, m.team2, m.score1, m.score2, m.stage_name
                FROM bets b
                JOIN matches m ON m.id = b.match_id
                WHERE b.user_id = ?
                ORDER BY b.created_at DESC
            """, (user_id,)).fetchall()
