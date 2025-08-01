
import discord
from discord.ext import commands
import random
import json
import os
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents)

# Pomocnicze funkcje do danych
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# LOWIENIE
@bot.command()
@commands.cooldown(1, 20, commands.BucketType.user)
async def lowienie(ctx):
    user_id = str(ctx.author.id)
    data = load_data()

    ryby = {
        "Płotka": (10, 30),
        "Leszcz": (30, 60),
        "Szczupak": (60, 100),
        "Sum": (100, 200),
        "Megalodon": (200, 400)
    }

    ryba, (min_rbx, max_rbx) = random.choice(list(ryby.items()))
    zarobek = random.randint(min_rbx, max_rbx)

    if user_id not in data:
        data[user_id] = {"robux": 0, "exp": 0, "level": 1, "bank": 0}

    data[user_id]["robux"] += zarobek
    data[user_id]["exp"] += 10

    await ctx.send(f"🎣 {ctx.author.mention} złowił {ryba} i zarobił {zarobek} robuxów!")

    save_data(data)

# SKLEP
@bot.command()
async def shop(ctx):
    sklep = {
        "PEDAŁ": 5000,
        "ZŁODZIEJ": 15000,
        "ZBIERACZ": 50000,
        "GIT": 70000,
        "VIP": 100000
    }

    opis = "🛒 Sklep z rangami:

"
    for rola, cena in sklep.items():
        opis += f"🎫 {rola} – {cena} robuxów
"
    opis += "
Aby kupić, wpisz: `.kup <nazwa roli>`"

    await ctx.send(opis)

# OBSŁUGA COOLDOWN
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"{ctx.author.mention}, odczekaj {int(error.retry_after)} sekund przed ponownym użyciem.")
    else:
        raise error

# START
if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
