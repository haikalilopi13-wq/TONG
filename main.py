import discord
from discord.ext import commands
import os
import random
import datetime

# ==================== CONFIG BOT ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Channel ID Target
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050

# Sistem Penyimpanan Level & XP di Memori
user_data = {}
xp_cooldowns = {}

def get_user_xp(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"xp": 0, "level": 0}
    return user_data[user_id]

# ==================== EVENTS BOT ====================
@bot.event
async def on_ready():
    print(f"✨ Bot Berhasil Terhubung as {bot.user}!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Sistem Level & XP Otomatis
    now = datetime.datetime.now().timestamp()
    user_id = message.author.id

    if user_id not in xp_cooldowns or (now - xp_cooldowns[user_id]) > 60:
        xp_cooldowns[user_id] = now
        data = get_user_xp(user_id)
        gained_xp = random.randint(15, 25)
        data["xp"] += gained_xp
        xp_needed = (data["level"] + 1) * 100

        if data["xp"] >= xp_needed:
            data["level"] += 1
            data["xp"] = data["xp"] - xp_needed
            await message.channel.send(f"🎉 Selamat {message.author.mention}, kamu naik ke **Level {data['level']}**!")

    await bot.process_commands(message)

# ==================== KUMPULAN PERINTAH ====================

# --- PERINTAH BARU: LEADERBOARD ---
@bot.command(name="leaderboard", aliases=["lb", "top", "levels"])
async def show_leaderboard(ctx):
    if not user_data:
        await ctx.send("❌ Belum ada data level di server ini.")
        return

    # Sort berdasarkan level (desc), lalu XP (desc)
    sorted_users = sorted(user_data.items(), key=lambda item: (item[1]['level'], item[1]['xp']), reverse=True)

    embed = discord.Embed(title="🏆 Leaderboard Level Server", color=0xF1C40F)
    
    description = ""
    for i, (user_id, data) in enumerate(sorted_users[:10]): # Top 10
        user = bot.get_user(user_id)
        name = user.name if user else f"User {user_id}"
        description += f"{i+1}. **{name}** - Level {data['level']} (XP: {data['xp']})\n"

    embed.description = description
    await ctx.send(embed=embed)

# --- PERINTAH LAINNYA (SAMA SEPERTI SEBELUMNYA) ---
@bot.command(name="rank", aliases=["lvl", "level"])
async def check_rank(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = get_user_xp(target.id)
    xp_needed = (data["level"] + 1) * 100
    
    embed = discord.Embed(title=f"📊 Profil — {target.display_name}", color=0x3498DB)
    embed.add_field(name="Level", value=str(data['level']))
    embed.add_field(name="XP", value=f"{data['xp']} / {xp_needed}")
    await ctx.send(embed=embed)

@bot.command(name="avatar", aliases=["pp"])
async def show_avatar(ctx, member: discord.Member = None):
    target = member or ctx.author
    roles = [role.mention for role in target.roles if role != ctx.guild.default_role]
    role_list = ", ".join(roles) if roles else "Tidak ada"

    embed = discord.Embed(title=f"🖼️ Profil & Avatar — {target.name}", color=0x9B59B6)
    embed.set_image(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.add_field(name="🆔 ID", value=f"`{target.id}`", inline=True)
    embed.add_field(name="🛡️ Role", value=role_list, inline=False)
    await ctx.send(embed=embed)

# ... (Tambahkan sisa perintah lainnya di sini) ...

# ==================== RUN BOT ====================
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
