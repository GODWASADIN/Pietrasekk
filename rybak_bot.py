
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

# Pomocnicze funkcje
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

def get_lvl_exp(level):
    return 100 + (level - 1) * 25

async def check_level_up(ctx, data):
    user_id = str(ctx.author.id)
    user = data[user_id]
    next_level = user["level"] + 1
    required_exp = get_lvl_exp(next_level)
    if user["exp"] >= required_exp:
        user["level"] += 1
        await ctx.send(f"🔼 {ctx.author.mention} awansował na **Rybak lvl {user['level']}**!")
        guild = ctx.guild
        role_name = f"Rybak lvl {user['level']}"
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            role = await guild.create_role(name=role_name)
        await ctx.author.add_roles(role)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} jest online.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"{ctx.author.mention}, odczekaj {int(error.retry_after)} sekund przed użyciem tej komendy.")
    else:
        raise error

# Komendy
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
        data[user_id] = {"robux": 0, "bank": 0, "exp": 0, "level": 1}

    data[user_id]["robux"] += zarobek
    data[user_id]["exp"] += 10

    await check_level_up(ctx, data)
    await ctx.send(f"🎣 {ctx.author.mention} złowił {ryba} i zarobił {zarobek} robuxów!")
    save_data(data)

@bot.command()
@commands.cooldown(1, 60, commands.BucketType.user)
async def work(ctx):
    zarobek = random.randint(100, 300)
    user_id = str(ctx.author.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {"robux": 0, "bank": 0, "exp": 0, "level": 1}
    data[user_id]["robux"] += zarobek
    data[user_id]["exp"] += 5
    await check_level_up(ctx, data)
    await ctx.send(f"💼 {ctx.author.mention} zarobił {zarobek} robuxów w pracy!")
    save_data(data)

@bot.command()
@commands.cooldown(1, 90, commands.BucketType.user)
async def slut(ctx):
    wynik = random.choice([True, False])
    kasa = random.randint(100, 300)
    user_id = str(ctx.author.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {"robux": 0, "bank": 0, "exp": 0, "level": 1}
    if wynik:
        data[user_id]["robux"] += kasa
        await ctx.send(f"🎲 {ctx.author.mention} WYGRAŁ {kasa} robuxów w hazardzie!")
    else:
        data[user_id]["robux"] = max(0, data[user_id]["robux"] - kasa)
        await ctx.send(f"🎲 {ctx.author.mention} PRZEGRAŁ {kasa} robuxów w hazardzie!")
    save_data(data)

@bot.command()
@commands.cooldown(1, 120, commands.BucketType.user)
async def rob(ctx, target: discord.Member):
    if target.bot:
        await ctx.send("❌ Nie można okradać botów.")
        return
    data = load_data()
    user_id = str(ctx.author.id)
    target_id = str(target.id)
    if user_id not in data or target_id not in data:
        await ctx.send("❌ Brak danych.")
        return
    if data[target_id]["robux"] < 100:
        await ctx.send("💸 Ten użytkownik nie ma wystarczająco robuxów.")
        return
    sukces = random.choice([True, False])
    if sukces:
        kwota = random.randint(100, min(500, data[target_id]["robux"]))
        data[target_id]["robux"] -= kwota
        data[user_id]["robux"] += kwota
        await ctx.send(f"🕵️ {ctx.author.mention} ukradł {kwota} robuxów od {target.mention}!")
    else:
        kara = random.randint(50, 150)
        data[user_id]["robux"] = max(0, data[user_id]["robux"] - kara)
        await ctx.send(f"🚨 {ctx.author.mention} został złapany i stracił {kara} robuxów!")
    save_data(data)

@bot.command()
async def daily(ctx):
    user_id = str(ctx.author.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {"robux": 0, "bank": 0, "exp": 0, "level": 1}
    data[user_id]["robux"] += 500
    await ctx.send(f"📦 {ctx.author.mention}, otrzymujesz 500 robuxów za daily!")
    save_data(data)

@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    data = load_data()
    uid = str(ctx.author.id)
    mid = str(member.id)
    if uid not in data or data[uid]["robux"] < amount:
        await ctx.send("❌ Nie masz tylu robuxów.")
        return
    if mid not in data:
        data[mid] = {"robux": 0, "bank": 0, "exp": 0, "level": 1}
    data[uid]["robux"] -= amount
    data[mid]["robux"] += amount
    await ctx.send(f"💸 {ctx.author.mention} przekazał {amount} robuxów do {member.mention}")
    save_data(data)

@bot.command()
async def bal(ctx):
    data = load_data()
    uid = str(ctx.author.id)
    if uid not in data:
        await ctx.send("💼 Brak danych o Twoim koncie.")
        return
    robux = data[uid]["robux"]
    bank = data[uid]["bank"]
    await ctx.send(f"💰 {ctx.author.mention} Masz {robux} robuxów i {bank} w banku.")

@bot.command()
async def bank(ctx, typ: str, amount: int):
    data = load_data()
    uid = str(ctx.author.id)
    if uid not in data:
        return
    if typ == "wplac" and data[uid]["robux"] >= amount:
        data[uid]["robux"] -= amount
        data[uid]["bank"] += amount
    elif typ == "wyplac" and data[uid]["bank"] >= amount:
        data[uid]["bank"] -= amount
        data[uid]["robux"] += amount
    else:
        await ctx.send("❌ Nieprawidłowa operacja.")
        return
    save_data(data)
    await ctx.send("🏦 Operacja wykonana.")

@bot.command()
async def lvl(ctx):
    data = load_data()
    uid = str(ctx.author.id)
    if uid not in data:
        await ctx.send("❌ Brak danych.")
        return
    await ctx.send(f"🧬 {ctx.author.mention} – Level {data[uid]['level']} | EXP: {data[uid]['exp']}")

@bot.command()
async def ranking(ctx):
    data = load_data()
    top = sorted(data.items(), key=lambda x: x[1]["robux"] + x[1]["bank"], reverse=True)[:10]
    opis = ""
    for i, (user_id, dane) in enumerate(top, 1):
opis += f"{i}. <@{user_id}> – 💰 {dane['robux']} | 🧳 {dane['bank']} | 🔱 lvl {dane['level']}\n"

    embed = discord.Embed(title="🏆 Ranking graczy", description=opis, color=discord.Color.gold())
    await ctx.send(embed=embed)

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
    for r, c in sklep.items():
        opis += f"🎫 {r} – {c} robuxów
"
    opis += "
Aby kupić, wpisz `.kup <rola>`"
    await ctx.send(opis)

@bot.command()
async def kup(ctx, rola: str):
    sklep = {
        "PEDAŁ": 5000,
        "ZŁODZIEJ": 15000,
        "ZBIERACZ": 50000,
        "GIT": 70000,
        "VIP": 100000
    }
    user_id = str(ctx.author.id)
    data = load_data()
    if rola not in sklep:
        await ctx.send("❌ Nie ma takiej roli.")
        return
    cena = sklep[rola]
    if data.get(user_id, {}).get("robux", 0) < cena:
        await ctx.send("❌ Nie masz wystarczająco robuxów.")
        return
    data[user_id]["robux"] -= cena
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=rola)
    if not role:
        role = await guild.create_role(name=rola)
    await ctx.author.add_roles(role)
    await ctx.send(f"✅ {ctx.author.mention} kupił rolę **{rola}** za {cena} robuxów!")
    save_data(data)

if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
