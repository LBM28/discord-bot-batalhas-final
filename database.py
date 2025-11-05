import aiosqlite
from pathlib import Path

class DB:
    def __init__(self, path: Path):
        self.path = path

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            # Cria a tabela com campo 'tipo'
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    player TEXT NOT NULL,
                    tipo TEXT NOT NULL DEFAULT 'Geral',
                    wins INTEGER NOT NULL DEFAULT 0,
                    losses INTEGER NOT NULL DEFAULT 0,
                    score INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (player, tipo)
                )
            """)
            await db.commit()

    async def add_player(self, player: str):
        async with aiosqlite.connect(self.path) as db:
            # adiciona o player com tipo "Geral" por padrão
            await db.execute("""
                INSERT OR IGNORE INTO stats (player, tipo)
                VALUES (?, 'Geral')
            """, (player,))
            await db.commit()

    async def record_result(self, winner: str, loser: str, tipo: str, pontos: int):
        async with aiosqlite.connect(self.path) as db:
            # Cria o tipo se ainda não existir
            await db.execute("""
                INSERT OR IGNORE INTO stats (player, tipo)
                VALUES (?, ?)
            """, (winner, tipo))
            await db.execute("""
                INSERT OR IGNORE INTO stats (player, tipo)
                VALUES (?, ?)
            """, (loser, tipo))

            # Atualiza o vencedor e o perdedor
            await db.execute("""
                UPDATE stats
                SET wins = wins + 1,
                    score = score + ?
                WHERE player = ? AND tipo = ?
            """, (pontos, winner, tipo))

            await db.execute("""
                UPDATE stats
                SET losses = losses + 1
                WHERE player = ? AND tipo = ?
            """, (loser, tipo))

            await db.commit()

    async def get_page(self, limit: int, offset: int):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("""
                SELECT player,
                       tipo,
                       wins,
                       losses,
                       CASE WHEN (wins + losses) = 0 THEN 0.0
                            ELSE ROUND(100.0 * wins * 1.0 / (wins + losses), 2)
                       END AS winrate,
                       score
                FROM stats
                ORDER BY score DESC, winrate DESC, wins DESC, player ASC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            return await cur.fetchall()

async def record_result(self, winner: str, loser: str, tipo: str, pontos: int):
    async with aiosqlite.connect(self.path) as db:
        await db.execute("""
            UPDATE stats
            SET wins = wins + 1, score = score + ?
            WHERE player = ?
        """, (pontos, winner))
        await db.execute("""
            UPDATE stats
            SET losses = losses + 1
            WHERE player = ?
        """, (loser,))
        await db.commit()
       async def get_page_tipo(self, tipo: str, limit: int, offset: int):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("""
                SELECT player,
                       tipo,
                       wins,
                       losses,
                       CASE WHEN (wins + losses) = 0 THEN 0.0
                            ELSE ROUND(100.0 * wins * 1.0 / (wins + losses), 2)
                       END AS winrate,
                       score
                FROM stats
                WHERE tipo = ?
                ORDER BY score DESC, winrate DESC, wins DESC, player ASC
                LIMIT ? OFFSET ?
            """, (tipo, limit, offset))
            return await cur.fetchall()

