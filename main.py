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

# ==================== EVENTS BOT ====================
@bot.event
async def on_ready():
    print(f"✨ Bot Berhasil Terhubung as {bot.user}!")
    print("🚀 Siap melayani server dengan berbagai perintah baru!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Auto Response Tiket di Channel General
    if message.channel.id == GENERAL_CHANNEL_ID:
        try:
            async for old_msg in message.channel.history(limit=15):
                if old_msg.author.id == bot.user.id and len(old_msg.embeds) > 0:
                    await old_msg.delete()
        except Exception:
            pass

        embed = discord.Embed(
            title="🛒 PRENSTORE OFFICIAL TICKET SYSTEM",
            description="Selamat datang! Butuh bantuan cepat atau ingin melakukan pemesanan produk? Silakan akses panel tiket di bawah ini.",
            color=0x3498DB,
        )

        embed.add_field(
            name="📦 Layanan Order Produk",
            value=f"👉 Masuk ke <#{TICKET_CHANNEL_ID}>",
            inline=False,
        )
        embed.set_footer(text="TONGSOP Store • Secure & Trusted Service")

        await message.channel.send(content=f"{message.author.mention}", embed=embed)
        return

    await bot.process_commands(message)

# ==================== TAMBAHAN BANYAK PERINTAH BARU ====================

@bot.command(name="ping")
async def check_ping(ctx):
    latency_ms = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: `{latency_ms}ms`")

@bot.command(name="info", aliases=["help"])
async def show_info(ctx):
    embed = discord.Embed(
        title="📌 PUSAT BANTUAN & DAFTAR PERINTAH",
        description="Gunakan awalan titik (`.`) untuk menjalankan perintah berikut:",
        color=0x3498DB,
    )
    embed.add_field(
        name="🛠️ Utility & Informasi",
        value="`.ping` — Mengecek kecepatan respon bot\n"
              "`.say [pesan]` — Menyuruh bot mengulang pesan\n"
              "`.server` — Menampilkan info singkat server\n"
              "`.avatar [@user]` — Melihat foto profil member",
        inline=False
    )
    embed.add_field(
        name="🎮 Fun & Hiburan",
        value="`.roll` — Mengacak angka 1 sampai 100\n"
              "`.coinflip` — Lempar koin (Koin / Gambar)\n"
              "`.rate [sesuatu]` — Menilai sesuatu secara acak",
        inline=False
    )
    embed.set_footer(text="TONGSOP Store • All Rights Reserved")
    await ctx.send(embed=embed)

@bot.command(name="say")
async def say_message(ctx, *, message: str):
    await ctx.message.delete() # Hapus pesan command asli agar rapi
    await ctx.send(message)

@bot.command(name="server", aliases=["serverinfo"])
async def server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📊 Informasi Server: {guild.name}",
        color=0x2ECC71
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="👑 Pemilik", value=guild.owner.mention if guild.owner else "N/A", inline=True)
    embed.add_field(name="👥 Total Member", value=f"`{guild.member_count}`", inline=True)
    embed.set_footer(text=f"Server ID: {guild.id}")
    await ctx.send(embed=embed)

@bot.command(name="avatar", aliases=["pp"])
async def show_avatar(ctx, member: discord.Member = None):
    target = member or ctx.author
    embed = discord.Embed(
        title=f"🖼️ Foto Profil — {target.name}",
        color=0x9B59B6
    )
    avatar_url = target.avatar.url if target.avatar else target.default_avatar.url
    embed.set_image(url=avatar_url)
    await ctx.send(embed=embed)

@bot.command(name="roll")
async def roll_dice(ctx):
    result = random.randint(1, 100)
    await ctx.send(f"🎲 {ctx.author.mention}, hasil lemparan dadu kamu adalah: **{result}** (dari 1-100)")

@bot.command(name="coinflip", aliases=["koin"])
async def coin_flip(ctx):
    result = random.choice(["Kepala (Head) 🦅", "Buntut (Tail) 🪙"])
    await ctx.send(f"🪙 {ctx.author.mention} melempar koin dan mendapatkan: **{result}**")

@bot.command(name="rate")
async def rate_something(ctx, *, item: str):
    score = random.randint(0, 100)
    await ctx.send(f"⭐ Saya menilai **{item}** sebesar **{score}/100**!")

# ==================== RUN BOT ====================
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token bot tidak ditemukan!")
