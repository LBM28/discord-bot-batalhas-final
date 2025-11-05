import aiosqlite
from pathlib import Path

class DB:
    def __init__(self, path: Path):
        self.path = path

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    player TEXT PRIMARY KEY,
                    wins   INTEGER NOT NULL DEFAULT 0,
                    losses INTEGER NOT NULL DEFAULT 0,
                    score  INTEGER NOT NULL DEFAULT 0
                )
            """)
            await db.commit()

    async def add_player(self, player: str):
        player = (player or "").strip()
        if not player:
            return
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT OR IGNORE INTO stats (player) VALUES (?)", (player,))
            await db.commit()

    async def record_result(self, winner: str, loser: str, pontos: int):
        winner = (winner or "").strip()
        loser  = (loser  or "").strip()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE stats SET wins = wins + 1, score = score + ? WHERE player = ?",
                (int(pontos), winner)
            )
            await db.execute(
                "UPDATE stats SET losses = losses + 1 WHERE player = ?",
                (loser,)
            )
            await db.commit()

    async def get_page(self, limit: int, offset: int):
        """
        Retorna SEMPRE 5 colunas, nesta ordem:
        (player, wins, losses, winrate, score)
        """
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("""
                SELECT
                    player,
                    wins,
                    losses,
                    CASE
                        WHEN (wins + losses) = 0 THEN 0.0
                        ELSE ROUND(100.0 * wins * 1.0 / (wins + losses), 2)
                    END AS winrate,
                    score
                FROM stats
                ORDER BY score DESC, winrate DESC, wins DESC, player ASC
                LIMIT ? OFFSET ?
            """, (int(limit), int(offset)))
            rows = await cur.fetchall()
        return rows
