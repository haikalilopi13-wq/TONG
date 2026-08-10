import asyncio
import datetime
import os
import random
import re
import sqlite3
import discord
from discord.ext import commands

# Config Bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Channel ID
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050

xp_cooldowns = {}

# ==================== DATABASE ====================
def init_db():
    conn = sqlite3.connect("levels.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user_data(user_id):
    conn = sqlite3.connect("levels.db")
    cursor = conn.cursor()
    cursor.execute("SELECT xp, level FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    if not data:
        cursor.execute("INSERT INTO users (user_id, xp, level) VALUES (?, ?, ?)", (user_id, 0, 0))
        conn.commit()
        data = (0, 0)
    conn.close()
    return data

def update_user_data(user_id, xp, level):
    conn = sqlite3.connect("levels.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (xp, level, user_id))
    conn.commit()
    conn.close()

def get_top_users():
    conn = sqlite3.connect("levels.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, level, xp FROM users ORDER BY level DESC, xp DESC LIMIT 5")
    data = cursor.fetchall()
    conn.close()
    return data

def get_xp_needed(level):
    return (level + 1) * 100

def parse_duration(time_str: str) -> datetime.timedelta:
    match = re.match(r"^(\d+)([smhd])?$", time_str.lower())
    if not match: return None
    val, unit = match.groups()
    val = int(val)
    if unit == "s": return datetime.timedelta(seconds=val)
    elif unit == "m" or unit is None: return datetime.timedelta(minutes=val)
    elif unit == "h": return datetime.timedelta(hours=val)
    elif unit == "d": return datetime.timedelta(days=val)
    return None

# ==================== EVENTS ====================
@bot.event
async def on_ready():
    print(f"🚀 Bot online as {bot.user}!")

@bot.event
async def on_message(message):
    if message.author.bot: return

    # Leveling System
    now = datetime.datetime.now().timestamp()
    if message.author.id not in xp_cooldowns or now - xp_cooldowns[message.author.id] > 60:
        xp_cooldowns[message.author.id] = now
        current_xp, current_level = get_user_data(message.author.id)
        gained_xp = random.randint(15, 25)
        new_xp = current_xp + gained_xp
        xp_needed = get_xp_needed(current_level)

        if new_xp >= xp_needed:
            current_level += 1
            new_xp -= xp_needed
            update_user_data(message.author.id, new_xp, current_level)
            await message.channel.send(f"🔥 {message.author.mention} naik ke **Level {current_level}**!")
        else:
            update_user_data(message.author.id, new_xp, current_level)

    # Auto Ticket
    if message.channel.id == GENERAL_CHANNEL_ID and message.content.startswith("."):
        await bot.process_commands(message)
    elif message.channel.id == GENERAL_CHANNEL_ID:
        embed = discord.Embed(title="🛒 PRENSTORE TICKET", description=f"Butuh bantuan? Silakan buka tiket di <#{TICKET_CHANNEL_ID}>", color=0x3498DB)
        await message.channel.send(embed=embed)
    
    await bot.process_commands(message)

# ==================== COMMANDS ====================
@bot.command(name="leaderboard", aliases=["lb", "top"])
async def show_leaderboard(ctx):
    top_users = get_top_users()
    if not top_users:
        await ctx.send("❌ Data kosong.")
        return

    medals = ["#1", "#2", "#3", "#4", "#5"]
    embed = discord.Embed(color=0x2B2D31)
    embed.set_author(name=f"{ctx.guild.name} server", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)

    description = ""
    for i, (u_id, lvl, xp) in enumerate(top_users):
        user = bot.get_user(u_id) or await bot.fetch_user(u_id)
        name = user.name if user else f"User_{u_id}"
        rank = medals[i] if i < len(medals) else f"#{i+1}"
        
        xp_needed = get_xp_needed(lvl)
        progress = int((xp / xp_needed) * 15) if xp_needed > 0 else 0
        bar = "▬" * progress + " " * (15 - progress)
        
        description += f"`{rank}` • **@{name}** • LVL: {lvl}\n[{bar}]\n\n"

    embed.description = description
    embed.set_footer(text="Overall XP")
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

# Jalankan Bot
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: BOT_TOKEN tidak ditemukan.")
