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

DATA_FILE = 'data.json'

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_user_data(user_id):
    data = load_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {'robux': 0, 'bank': 0, 'exp': 0, 'level': 1}
        save_data(data)
    return data[user_id]

def update_user_data(user_id, user_data):
    data = load_data()
    data[str(user_id)] = user_data
    save_data(data)

def get_level_from_exp(exp):
    return exp // 100

async def assign_level_role(member, level):
    guild = member.guild
    old_roles = [role for role in member.roles if role.name.startswith("Rybak lvl")]
    for role in old_roles:
        await member.remove_roles(role)
    role_name = f"Rybak lvl {level}"
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        role = await guild.create_role(name=role_name)
    await member.add_roles(role)

@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user}')

@bot.command()
async def bal(ctx):
    user_data = get_user_data(ctx.author.id)
    await ctx.send(f"{ctx.author.mention}, masz {user_data['robux']} Robuxów w portfelu i {user_data['bank']} w banku.")


import random

games = {}  # Przechowuje stany gier per user_id

deck = [2,3,4,5,6,7,8,9,10,10,10,10,11]*4  # Prosta talia (10=J,Q,K), as=11

def hand_value(hand):
    value = sum(hand)
    # As liczymy jako 1 jeśli przekracza 21
    aces = hand.count(11)
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

@bot.command()
async def bj(ctx, bet: int):
    user_data = get_user_data(ctx.author.id)
    if bet <= 0:
        return await ctx.send("Podaj poprawną stawkę.")
    if user_data['robux'] < bet:
        return await ctx.send("Nie masz tyle Robuxów!")

    user_data['robux'] -= bet
    update_user_data(ctx.author.id, user_data)

    hand = random.sample(deck, 2)
    dealer_hand = random.sample(deck, 2)
    games[ctx.author.id] = {
        'bet': bet,
        'hand': hand,
        'dealer_hand': dealer_hand,
        'finished': False
    }

    await ctx.send(f"Twoje karty: {hand} (suma: {hand_value(hand)})\nKrupier pokazuje: {dealer_hand[0]}\nNapisz `.hit` aby dobrać, `.stand` aby zatrzymać.")

@bot.command()
async def hit(ctx):
    game = games.get(ctx.author.id)
    if not game or game['finished']:
        return await ctx.send("Nie masz aktywnej gry. Zacznij od `.bj [stawka]`.")

    game['hand'].append(random.choice(deck))
    value = hand_value(game['hand'])

    if value > 21:
        game['finished'] = True
        await ctx.send(f"Twoje karty: {game['hand']} (suma: {value})\nPrzegrałeś! Straciłeś {game['bet']} Robuxów.")
    else:
        await ctx.send(f"Twoje karty: {game['hand']} (suma: {value})\nNapisz `.hit` lub `.stand`.")

@bot.command()
async def stand(ctx):
    game = games.get(ctx.author.id)
    if not game or game['finished']:
        return await ctx.send("Nie masz aktywnej gry. Zacznij od `.bj [stawka]`.")

    game['finished'] = True
    player_val = hand_value(game['hand'])
    dealer_hand = game['dealer_hand']

    while hand_value(dealer_hand) < 17:
        dealer_hand.append(random.choice(deck))

    dealer_val = hand_value(dealer_hand)

    user_data = get_user_data(ctx.author.id)

    result_msg = f"Twoje karty: {game['hand']} (suma: {player_val})\nKarty krupiera: {dealer_hand} (suma: {dealer_val})\n"

    if dealer_val > 21 or player_val > dealer_val:
        wygrana = game['bet'] * 2
        user_data['robux'] += wygrana
        update_user_data(ctx.author.id, user_data)
        result_msg += f"Wygrałeś! Otrzymujesz {wygrana} Robuxów."
    elif player_val == dealer_val:
        user_data['robux'] += game['bet']
        update_user_data(ctx.author.id, user_data)
        result_msg += "Remis! Stawka została zwrócona."
    else:
        result_msg += "Przegrałeś!"

    await ctx.send(result_msg)


OWNER_ID = 987130076866949230

@bot.command()
async def dodajkase(ctx, member: discord.Member, kwota: int):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Tylko właściciel bota może używać tej komendy.")
    
    if kwota <= 0:
        return await ctx.send("Podaj poprawną kwotę większą niż 0.")
    
    user_data = get_user_data(member.id)
    user_data['robux'] += kwota
    update_user_data(member.id, user_data)
    
    await ctx.send(f"✅ Dodano {kwota} Robuxów użytkownikowi {member.mention}!")

@bot.command()
async def bank(ctx, operacja: str, kwota: int):
    user_data = get_user_data(ctx.author.id)
    if operacja == "wplac":
        if user_data['robux'] >= kwota:
            user_data['robux'] -= kwota
            user_data['bank'] += kwota
            await ctx.send(f"Wpłacono {kwota} Robuxów do banku.")
        else:
            await ctx.send("Nie masz tyle Robuxów.")
    elif operacja == "wyplac":
        if user_data['bank'] >= kwota:
            user_data['bank'] -= kwota
            user_data['robux'] += kwota
            await ctx.send(f"Wypłacono {kwota} Robuxów z banku.")
        else:
            await ctx.send("Nie masz tyle w banku.")
    update_user_data(ctx.author.id, user_data)

@bot.command()
@commands.cooldown(1, 20, commands.BucketType.user)
async def lowienie(ctx):
    ryby = [
        ("Płotka", 0.425, (30, 60)),
        ("Szczupak", 0.255, (60, 120)),
        ("Szczupak", 0.255, (150, 180)),
        ("Łosoś", 0.1275, (200, 250)),
        ("Rekin", 0.034, (400, 500)),
        ("Nemo", 0.0085, (1000, 2000)),
    ]
    r = random.random()
    suma = 0

    for nazwa, szansa, (min_r, max_r) in ryby:
        suma += szansa
        if r < suma:
            nagroda = random.randint(min_r, max_r)
            user_data = get_user_data(ctx.author.id)
            user_data['robux'] += nagroda
            user_data['exp'] += 5

            new_level = get_level_from_exp(user_data['exp'])
            if new_level > user_data['level']:
                user_data['level'] = new_level
                await assign_level_role(ctx.author, new_level)
                await ctx.send(f"{ctx.author.mention} awansował na poziom {new_level}!")

            update_user_data(ctx.author.id, user_data)
            await ctx.send(f"{ctx.author.mention} złowił: **{nazwa}** i zarobił {nagroda} Robuxów!")
            return

    # Jeśli nie złowił nic (15% szans)
    await ctx.send(f"{ctx.author.mention}, niestety nic nie złowiłeś tym razem 🎣")

@bot.command()
@commands.cooldown(1, 60, commands.BucketType.user)
async def work(ctx):
    zarobek = random.randint(100, 300)
    user_data = get_user_data(ctx.author.id)
    user_data['robux'] += zarobek
    user_data['exp'] += 10
    update_user_data(ctx.author.id, user_data)
    await ctx.send(f"{ctx.author.mention}, zarobiłeś {zarobek} Robuxów za pracę!")

@bot.command()
@commands.cooldown(1, 90, commands.BucketType.user)
async def slut(ctx):
    wynik = random.choice(["win", "lose"])
    if wynik == "win":
        kasa = random.randint(50, 150)
        user_data = get_user_data(ctx.author.id)
        user_data['robux'] += kasa
        await ctx.send(f"{ctx.author.mention}, wygrałeś {kasa} Robuxów!")
    else:
        strata = random.randint(10, 100)
        user_data = get_user_data(ctx.author.id)
        user_data['robux'] = max(0, user_data['robux'] - strata)
        await ctx.send(f"{ctx.author.mention}, przegrałeś {strata} Robuxów.")
    update_user_data(ctx.author.id, user_data)


OWNER_ID = 987130076866949230

@bot.command()
async def dodajlvl(ctx, member: discord.Member, ile: int):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Tylko właściciel bota może używać tej komendy.")
    
    if ile <= 0:
        return await ctx.send("Podaj poprawną liczbę poziomów do dodania.")
    
    user_data = get_user_data(member.id)
    user_data['level'] = user_data.get('level', 1) + ile
    update_user_data(member.id, user_data)
    
    await ctx.send(f"✅ Dodano {ile} poziomów użytkownikowi {member.mention}. Nowy poziom: {user_data['level']}")



@bot.command()
@commands.cooldown(1, 120, commands.BucketType.user)
async def rob(ctx, target: discord.Member):
    if target.bot:
        return await ctx.send("Nie możesz okraść bota!")
    user_data = get_user_data(ctx.author.id)
    target_data = get_user_data(target.id)
    if random.random() < 0.4 and target_data['robux'] >= 50:
        kradziez = random.randint(30, min(150, target_data['robux']))
        user_data['robux'] += kradziez
        target_data['robux'] -= kradziez
        await ctx.send(f"{ctx.author.mention} ukradł {kradziez} Robuxów od {target.mention}!")
    else:
        kara = random.randint(20, 70)
        user_data['robux'] = max(0, user_data['robux'] - kara)
        await ctx.send(f"{ctx.author.mention} nieudana próba kradzieży! Straciłeś {kara} Robuxów.")
    update_user_data(ctx.author.id, user_data)
    update_user_data(target.id, target_data)



import random

@bot.command()
async def ruletka(ctx, kwota: int, kolor: str):
    kolor = kolor.lower()
    kolory = ['czerwony', 'czarny', 'zielony']

    if kolor not in kolory:
        return await ctx.send("Podaj poprawny kolor: czerwony, czarny lub zielony.")

    if kwota <= 0:
        return await ctx.send("Podaj poprawną kwotę większą niż 0.")

    user_data = get_user_data(ctx.author.id)
    if user_data['robux'] < kwota:
        return await ctx.send("Nie masz tyle Robuxów.")

    user_data['robux'] -= kwota

    # Losujemy wynik ruletki z wagami 2% zielony, 49% czerwony, 49% czarny
    wynik = random.choices(
        population=['zielony', 'czerwony', 'czarny'],
        weights=[2, 49, 49],
        k=1
    )[0]

    if wynik == kolor:
        if wynik == 'zielony':
            wygrana = kwota * 10
        else:
            wygrana = kwota * 2

        user_data['robux'] += wygrana
        update_user_data(ctx.author.id, user_data)
        await ctx.send(f"🎉 Wylosowano **{wynik}**! Gratulacje, wygrałeś {wygrana} Robuxów!")
    else:
        update_user_data(ctx.author.id, user_data)
        await ctx.send(f"😢 Wylosowano **{wynik}**. Przegrałeś {kwota} Robuxów.")
        
@bot.command()
async def kup(ctx, *, nazwa: str):
    role_map = {
        "PEDAŁ": 5000,
        "ZŁODZIEJ": 15000,
        "ZBIERACZ": 50000,
        "GIT": 70000,
        "VIP": 100000
    }

    nazwa = nazwa.upper()  # Żeby działało też np. "vip" czy "Vip"
    if nazwa not in role_map:
        return await ctx.send("Nie ma takiej rangi.")

    cena = role_map[nazwa]
    user_data = get_user_data(ctx.author.id)

    # Sprawdzamy robuxy + bank razem
    total = user_data['robux'] + user_data['bank']
    if total < cena:
        return await ctx.send(f"Brakuje Ci {cena - total} Robuxów do zakupu tej rangi.")

    # Odejmujemy z banku, potem z robux
    if user_data['bank'] >= cena:
        user_data['bank'] -= cena
    else:
        reszta = cena - user_data['bank']
        user_data['bank'] = 0
        user_data['robux'] -= reszta

    rola = discord.utils.get(ctx.guild.roles, name=nazwa)
    if not rola:
        rola = await ctx.guild.create_role(name=nazwa)

    await ctx.author.add_roles(rola)
    update_user_data(ctx.author.id, user_data)

    await ctx.send(f"{ctx.author.mention}, kupiłeś rolę {nazwa} za {cena} Robuxów!")

@bot.command()
async def ranking(ctx):
    data = load_data()
    top = sorted(data.items(), key=lambda x: x[1]['robux'] + x[1]['bank'], reverse=True)[:10]
    opis = ""
    for i, (user_id, dane) in enumerate(top, 1):
        opis += f"{i}. <@{user_id}> - 💰 {dane['robux']} | 🧳 {dane['bank']} | 🔱 lvl {dane['level']}\n"
        
    embed = discord.Embed(title="🏆 Ranking graczy", description=opis, color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.command()
async def lvl(ctx):
    user_data = get_user_data(ctx.author.id)
    await ctx.send(f"{ctx.author.mention}, masz {user_data['exp']} EXP i jesteś na poziomie {user_data['level']}.")

@bot.command()
async def shop(ctx):
    role_map = {
        5000: "PEDAŁ",
        15000: "ZŁODZIEJ",
        50000: "ZBIERACZ",
        70000: "GIT",
        100000: "VIP"
    }
    opis = ""
    for cena, nazwa in sorted(role_map.items()):
        opis += f"💸 {cena} Robuxów — **{nazwa}**\n"
    embed = discord.Embed(title="🛍️ Sklep z rangami", description=opis, color=discord.Color.blue())
    await ctx.send(embed=embed)

last_daily = {}

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def daily(ctx):
    user_id = str(ctx.author.id)
    now = datetime.utcnow()
    last = last_daily.get(user_id)

    if last and (now - last).days < 1:
        await ctx.send(f"{ctx.author.mention}, dzienną nagrodę możesz odebrać raz na 24 godziny.")
        return

    nagroda = 500
    user_data = get_user_data(ctx.author.id)
    user_data['robux'] += nagroda
    user_data['exp'] += 5
    update_user_data(ctx.author.id, user_data)
    last_daily[user_id] = now
    await ctx.send(f"{ctx.author.mention}, otrzymałeś {nagroda} Robuxów w ramach dziennej nagrody!")

@bot.command()
async def give(ctx, member: discord.Member, kwota: int):
    if member.bot:
        return await ctx.send("Nie możesz przekazać Robuxów botowi.")
    if kwota <= 0:
        return await ctx.send("Podaj prawidłową kwotę.")

    user_data = get_user_data(ctx.author.id)
    target_data = get_user_data(member.id)

    if user_data['robux'] < kwota:
        return await ctx.send("Nie masz wystarczająco Robuxów.")

    user_data['robux'] -= kwota
    target_data['robux'] += kwota

    update_user_data(ctx.author.id, user_data)
    update_user_data(member.id, target_data)

    await ctx.send(f"{ctx.author.mention} przekazał {kwota} Robuxów dla {member.mention}!")

@bot.command()
async def cooldown(ctx):
    command = bot.get_command("lowienie")
    bucket = command._buckets.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()
    if retry_after:
        await ctx.send(f"{ctx.author.mention}, możesz łowić ponownie za {int(retry_after)} sekund.")
    else:
        await ctx.send(f"{ctx.author.mention}, możesz łowić teraz!")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"{ctx.author.mention}, możesz użyć tej komendy ponownie za {int(error.retry_after)} sekund.")
    else:
        raise error
        
if __name__ == "__main__":
    import os
    bot.run(os.getenv("DISCORD_TOKEN"))
