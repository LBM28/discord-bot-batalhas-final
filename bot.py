import os
import aiosqlite
import discord
from discord.ext import commands
from discord import app_commands
from pathlib import Path
from database import DB

# ------------------- CONFIG -------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "batalhas.db"

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("⚠️ Token não encontrado. Defina DISCORD_TOKEN no ambiente.")

OWNER_ID = 496404030038212618  # <-- seu ID aqui

intents = discord.Intents.default()
intents.message_content = True  # você já habilitou nas intents do portal

bot = commands.Bot(command_prefix="!", intents=intents)
db = DB(DB_PATH)

# ------------------- EVENTOS -------------------
@bot.event
async def on_ready():
    await db.init()
    await bot.tree.sync()
    print(f"🤖 Logado como {bot.user} | Comandos sincronizados.")

# ------------------- COMANDOS -------------------
@bot.tree.command(name="battle", description="Cria uma batalha entre dois jogadores.")
@app_commands.describe(tipo="Tipo da batalha (Comp, Ginasio ou Convencional)")
@app_commands.choices(
    tipo=[
        app_commands.Choice(name="Competitiva", value="comp"),
        app_commands.Choice(name="Ginásio", value="ginasio"),
        app_commands.Choice(name="Convencional", value="convencional"),
    ]
)
async def battle(
    interaction: discord.Interaction,
    player1: str,
    player2: str,
    tipo: app_commands.Choice[str],
):
    # garante que os jogadores existem no banco
    await db.add_player(player1)
    await db.add_player(player2)

    tipo_valor = tipo.value.lower()
    # pontuação por tipo (ajuste se quiser)
    pontos = 3 if tipo_valor == "comp" else 5 if tipo_valor == "ginasio" else 1

    view = BattleView(player1.strip(), player2.strip(), pontos)
    await interaction.response.send_message(
        f"⚔️ **Batalha criada!**\n**{player1}** vs **{player2}**\n"
        f"🏆 Tipo: **{tipo.name}**\nEscolha o vencedor abaixo:",
        view=view
    )

@bot.tree.command(name="tabela", description="Mostra a tabela geral de vitórias, derrotas e pontuação.")
async def tabela(interaction: discord.Interaction):
    stats = await db.get_page(50, 0)

    if not stats:
        await interaction.response.send_message("⚠️ Nenhum jogador ainda tem registros.")
        return

    # Aceita 5 ou 6 colunas:
    # 5: (player, wins, losses, winrate, score)
    # 6: (player, tipo,  wins, losses, winrate, score)
    has_tipo = len(stats[0]) == 6

    if has_tipo:
        header = f"{'Jogador':<14}{'Tipo':<12}{'W':>3}{'L':>3}{'Win%':>8}{'Pts':>6}\n"
        sep    = "-" * (14+12+3+3+8+6) + "\n"
    else:
        header = f"{'Jogador':<20}{'W':>3}{'L':>3}{'Win%':>8}{'Pts':>6}\n"
        sep    = "-" * (20+3+3+8+6) + "\n"

    linhas = []
    for row in stats:
        if len(row) == 6:
            player, tipo, wins, losses, winrate, score = row
            linhas.append(f"{player:<14}{str(tipo):<12}{wins:>3}{losses:>3}{float(winrate):>8.1f}{int(score):>6}")
        elif len(row) == 5:
            player, wins, losses, winrate, score = row
            linhas.append(f"{player:<20}{wins:>3}{losses:>3}{float(winrate):>8.1f}{int(score):>6}")
        else:
            # Linha inesperada: imprime crua pra não quebrar
            linhas.append(str(row))

    msg = "🏅 **Tabela de Jogadores** 🏅\n```\n" + header + sep + "\n".join(linhas) + "\n```"
    await interaction.response.send_message(msg)

@bot.tree.command(name="reset", description="Reseta a tabela de batalhas (somente o dono).")
async def reset(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Apenas o dono pode usar este comando.", ephemeral=True)
        return

    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM stats;")
        await conn.commit()

    await interaction.response.send_message("🧹 Tabela resetada com sucesso!")

# ------------------- VIEW -------------------
class BattleView(discord.ui.View):
    def __init__(self, p1: str, p2: str, pontos: int):
        super().__init__(timeout=60)
        self.p1 = p1
        self.p2 = p2
        self.pontos = int(pontos)

    @discord.ui.button(label="🏆 Jogador 1 venceu", style=discord.ButtonStyle.green)
    async def player1_win(self, interaction: discord.Interaction, button: discord.ui.Button):
        await db.record_result(self.p1, self.p2, self.pontos)
        await interaction.response.edit_message(
            content=f"✅ **{self.p1} venceu!** (+{self.pontos} pts)",
            view=None
        )

    @discord.ui.button(label="🏆 Jogador 2 venceu", style=discord.ButtonStyle.blurple)
    async def player2_win(self, interaction: discord.Interaction, button: discord.ui.Button):
        await db.record_result(self.p2, self.p1, self.pontos)
        await interaction.response.edit_message(
            content=f"✅ **{self.p2} venceu!** (+{self.pontos} pts)",
            view=None
        )

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Batalha cancelada.", view=None)

# ------------------- RUN -------------------
bot.run(TOKEN)
