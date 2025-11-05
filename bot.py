import os
import time
import aiosqlite
import discord
from discord.ext import commands
from discord import app_commands
from pathlib import Path
from database import DB

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "batalhas.db"

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("⚠️ Token não encontrado. Defina DISCORD_TOKEN no ambiente.")

intents = discord.Intents.default()
intents.message_content = True

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
@app_commands.describe(
    player1="Nome do primeiro jogador",
    player2="Nome do segundo jogador",
    tipo="Tipo de batalha (Comp, Ginasio ou Convencional)"
)
@app_commands.choices(tipo=[
    app_commands.Choice(name="Competitiva", value="Comp"),
    app_commands.Choice(name="Ginasio", value="Ginasio"),
    app_commands.Choice(name="Convencional", value="Convencional")
])
async def battle(interaction: discord.Interaction, player1: str, player2: str, tipo: str):
    await db.add_player(player1)
    await db.add_player(player2)

    tipo = tipo.capitalize()
    pontos = {
        "Comp": 3,
        "Ginasio": 5
    }.get(tipo, 1)

    view = BattleView(player1, player2, tipo, pontos)
    await interaction.response.send_message(
        f"⚔️ **Batalha criada!**\n**{player1}** vs **{player2}**\n"
        f"🏆 Tipo: **{tipo}**\nEscolha o vencedor abaixo:",
        view=view
    )

@bot.tree.command(name="tabela", description="Mostra a tabela de jogadores (geral ou por tipo).")
@app_commands.describe(tipo="Escolha o tipo de batalha para filtrar (opcional)")
@app_commands.choices(tipo=[
    app_commands.Choice(name="🏆 Competitiva", value="Comp"),
    app_commands.Choice(name="🏛️ Ginasio", value="Ginasio"),
    app_commands.Choice(name="⚔️ Convencional", value="Convencional"),
    app_commands.Choice(name="📋 Geral", value="Geral")
])
async def tabela(interaction: discord.Interaction, tipo: str = "Geral"):
    tipo = tipo.capitalize()

    # Consulta dinâmica com filtro opcional
    if tipo == "Geral":
        stats = await db.get_page(50, 0)
    else:
        stats = await db.get_page_tipo(tipo, 50, 0)

    if not stats:
        return await interaction.response.send_message(
            f"⚠️ Nenhum registro encontrado para o tipo **{tipo}**."
        )

    msg = f"🏅 **Tabela de Jogadores - {tipo}** 🏅\n\n"
    for player, wins, losses, winrate, score in stats:
        msg += f"**{player}** - 🏆 {wins}W / ❌ {losses}L | 💯 {winrate}% | ⭐ {score} pts\n"

    await interaction.response.send_message(msg)


@bot.tree.command(name="reset", description="Reseta a tabela de batalhas (somente o dono).")
async def reset(interaction: discord.Interaction):
    owner_id = 496404030038212618  # coloque seu ID do Discord aqui

    if interaction.user.id != owner_id:
        return await interaction.response.send_message("❌ Apenas o dono pode usar este comando.", ephemeral=True)

    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM stats;")
        await conn.commit()

    await interaction.response.send_message("🧹 Tabela resetada com sucesso!")

# ------------------- VIEW -------------------

class BattleView(discord.ui.View):
    def __init__(self, p1, p2, tipo, pontos):
        super().__init__(timeout=60)
        self.p1 = p1
        self.p2 = p2
        self.tipo = tipo
        self.pontos = pontos

    @discord.ui.button(label="🏆 Jogador 1 venceu", style=discord.ButtonStyle.green)
    async def player1_win(self, interaction: discord.Interaction, button: discord.ui.Button):
        await db.record_result(self.p1, self.p2, self.tipo, self.pontos)
        await interaction.response.edit_message(content=f"✅ **{self.p1} venceu!** (+{self.pontos} pts) | Tipo: {self.tipo}", view=None)

    @discord.ui.button(label="🏆 Jogador 2 venceu", style=discord.ButtonStyle.blurple)
    async def player2_win(self, interaction: discord.Interaction, button: discord.ui.Button):
        await db.record_result(self.p2, self.p1, self.tipo, self.pontos)
        await interaction.response.edit_message(content=f"✅ **{self.p2} venceu!** (+{self.pontos} pts) | Tipo: {self.tipo}", view=None)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="❌ Batalha cancelada.", view=None)

bot.run(TOKEN)
