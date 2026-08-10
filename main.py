import asyncio
import datetime
import os
import random
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

# ==================== EVENTS ====================

@bot.event
async def on_ready():
    print(f"🚀 Bot udah jalan nih as {bot.user}!")
    print("Prefix: '.' | Ready buat dipake.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Leveling Otomatis
    now = datetime.datetime.now().timestamp()
    user_id = message.author.id

    if user_id not in xp_cooldowns or now - xp_cooldowns[user_id] > 60:
        xp_cooldowns[user_id] = now
        current_xp, current_level = get_user_data(user_id)
        gained_xp = random.randint(15, 25)
        new_xp = current_xp + gained_xp
        xp_needed = get_xp_needed(current_level)

        if new_xp >= xp_needed:
            current_level += 1
            new_xp = new_xp - xp_needed
            update_user_data(user_id, new_xp, current_level)
            embed = discord.Embed(title="🔥 LEVEL UP!", description=f"GG {message.author.mention}! Level kamu naik jadi **Level {current_level}** 🥳", color=0x2ECC71)
            try: await message.channel.send(embed=embed)
            except: pass
        else:
            update_user_data(user_id, new_xp, current_level)

    # 2. Auto Response Tiket di General
    if message.channel.id == GENERAL_CHANNEL_ID:
        try:
            async for old_msg in message.channel.history(limit=15):
                if old_msg.author.id == bot.user.id and len(old_msg.embeds) > 0:
                    await old_msg.delete()
                    await asyncio.sleep(0.5)
        except: pass

        embed = discord.Embed(title="🛒 PRENSTORE OFFICIAL TICKET", description="Halo! Mau order atau butuh bantuan? Langsung klik channel tiket di bawah biar aman ya!", color=0x3498DB)
        embed.add_field(name="📦 Order Produk", value=f"👉 <#{TICKET_CHANNEL_ID}> (Pilih ` open-ticket `)", inline=False)
        embed.add_field(name="⚡ Jasa Split Redfinger", value=f"👉 <#{TICKET_CHANNEL_ID}> (Pilih ` jasa split `)", inline=False)
        embed.add_field(name="⚠️ Notice", value="• Jangan transaksi di luar tiket demi keamanan bersama!\n• Admin pasti respon secepatnya.", inline=False)
        embed.set_footer(text="TONGSOP Store • Safety First")
        await message.channel.send(content=f"{message.author.mention}", embed=embed)
        return

    await bot.process_commands(message)

# ==================== COMMANDS ====================

@bot.command(name="info", aliases=["help"])
async def show_info(ctx):
    embed = discord.Embed(title="📌 MENU PERINTAH BOT", description="Pake prefix titik (`.`) buat jalanin perintah ya:", color=0x3498DB)
    embed.add_field(name="🎮 Leveling", value="`.rank` — Cek level & XP\n`.lb` — Top 5 member aktif", inline=False)
    embed.add_field(name="🛡️ Moderasi & Role", value="`.role @user [nama]`\n`.to @user [waktu]`\n`.clear [jumlah]`\n`.kick`/`.ban`", inline=False)
    embed.set_footer(text="TONGSOP Assistant")
    await ctx.send(embed=embed)

@bot.command(name="rank", aliases=["level"])
async def check_rank(ctx, member: discord.Member = None):
    target = member or ctx.author
    xp, level = get_user_data(target.id)
    xp_needed = get_xp_needed(level)
    percent = int((xp / xp_needed) * 100) if xp_needed > 0 else 0
    bar = "🟩" * int(10 * (xp / xp_needed)) + "⬛" * (10 - int(10 * (xp / xp_needed))) if xp_needed > 0 else "⬛"*10
    embed = discord.Embed(title=f"📊 Status Level — {target.display_name}", color=0x3498DB)
    embed.add_field(name="Level", value=f"**{level}**", inline=True)
    embed.add_field(name="XP", value=f"**{xp} / {xp_needed}**", inline=True)
    embed.add_field(name="Progress", value=f"{bar} **{percent}%**", inline=False)
    await ctx.send(embed=embed)

# [Tambahkan kembali command moderasi lain (.to, .role, .clear, dll) di sini sesuai kebutuhan sebelumnya]

TOKEN = os.getenv("BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
