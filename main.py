import discord
from discord.ext import commands
import os
import random
import datetime
import asyncio

# ==================== CONFIG BOT ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Channel ID Target
GENERAL_CHANNEL_ID = 1538646829938516048  
TARGET_CATEGORY_OR_PARENT_ID = 1517625110536786050  
TESTIMONI_CHANNEL_ID = 1517625158263898284        
REDFINGER_TESTI_CHANNEL_ID = 1538673467442856059 
STAFF_ROLE_ID = 1517580561361928463  

# Database Sederhana di Memori
user_data = {} # Format: {user_id: {"xp": 0, "level": 0, "money": 0}}

def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"xp": 0, "level": 0, "money": 0}
    return user_data[user_id]

# ==================== EVENTS BOT ====================
@bot.event
async def on_ready():
    print(f"✨ Bot Online! Semua fitur telah digabungkan.")

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # Logic XP/Leveling
    data = get_user_data(message.author.id)
    data["xp"] += random.randint(5, 10)
    
    xp_needed = (data["level"] + 1) * 100
    if data["xp"] >= xp_needed:
        data["level"] += 1
        data["xp"] = 0
        await message.channel.send(f"🎉 Selamat {message.author.mention}, kamu naik ke Level **{data['level']}**!")
    
    await bot.process_commands(message)

# ==================== PERINTAH PENGGUNA & ADMIN ====================

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

@bot.command(name="profile", aliases=["rank", "level"])
async def profile(ctx):
    data = get_user_data(ctx.author.id)
    embed = discord.Embed(title=f"Profil {ctx.author.name}", color=0x3498DB)
    embed.add_field(name="Level", value=data["level"], inline=True)
    embed.add_field(name="XP", value=data["xp"], inline=True)
    embed.add_field(name="Money", value=f"${data['money']}", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="addmoney")
@commands.has_permissions(administrator=True)
async def addmoney(ctx, member: discord.Member, amount: int):
    data = get_user_data(member.id)
    data["money"] += amount
    await ctx.send(f"✅ Ditambahkan ${amount} ke {member.name}. Total: ${data['money']}")

@bot.command(name="panelorder")
async def panelorder(ctx):
    # Cek akses staff
    is_staff = ctx.author.guild_permissions.manage_channels or any(role.id == STAFF_ROLE_ID for role in ctx.author.roles)
    if not is_staff: return await ctx.send("❌ Hanya Staff!")
    
    embed = discord.Embed(title="🛒 TONGSOP TICKET SYSTEM", description="Pilih layanan di bawah:", color=0x3498DB)
    await ctx.send(embed=embed, view=BuyButtonView())

# ==================== VIEW TIKET & MODAL (Sama seperti sebelumnya) ====================
# [Di sini Anda bisa tetap menggunakan class BuyModal, RedfingerModal, ClaimTicketView, dll yang sudah kita buat sebelumnya]

# ==================== RUN BOT ====================
TOKEN = os.getenv("BOT_TOKEN")
bot.run(TOKEN)
