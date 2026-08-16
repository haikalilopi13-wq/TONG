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
    print("🚀 Siap melayani server dengan puluhan perintah baru!")

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

# ==================== KUMPULAN PERINTAH LENGKAP ====================

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
        value="`.ping` — Cek kecepatan respon bot\n"
              "`.say [pesan]` — Menyuruh bot mengulang pesan\n"
              "`.server` — Menampilkan info lengkap server\n"
              "`.whois [@user]` — Melihat detail profil member\n"
              "`.avatar [@user]` — Melihat foto profil member",
        inline=False
    )
    embed.add_field(
        name="🎮 Fun, Games & Hiburan",
        value="`.roll` — Mengacak angka 1 sampai 100\n"
              "`.coinflip` — Lempar koin (Kepala/Buntut)\n"
              "`.rps [batu/kertas/gunting]` — Main Suit Jepang\n"
              "`.rate [sesuatu]` — Menilai sesuatu 0-100\n"
              "`.quote` — Menampilkan kata-kata bijak acak",
        inline=False
    )
    embed.add_field(
        name="🧮 Alat Praktis",
        value="`.calc [angka1] [+|-|*|/] [angka2]` — Kalkulator cepat\n"
              "`.choose [pilihan1], [pilihan2]` — Membantu membuat keputusan",
        inline=False
    )
    embed.set_footer(text="TONGSOP Store • All Rights Reserved")
    await ctx.send(embed=embed)

# --- UTILITY COMMANDS ---
@bot.command(name="say")
async def say_message(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command(name="server", aliases=["serverinfo"])
async def server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 Informasi Server: {guild.name}", color=0x2ECC71)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="👑 Pemilik", value=guild.owner.mention if guild.owner else "N/A", inline=True)
    embed.add_field(name="👥 Total Member", value=f"`{guild.member_count}`", inline=True)
    embed.add_field(name="🏷️ Total Role", value=f"`{len(guild.roles)}`", inline=True)
    embed.set_footer(text=f"Server ID: {guild.id}")
    await ctx.send(embed=embed)

@bot.command(name="whois", aliases=["userinfo"])
async def whois_member(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 User Info — {member.name}", color=0x3498DB)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
    embed.add_field(name="Nama Panggilan", value=member.display_name, inline=True)
    embed.add_field(name="Bergabung Sejak", value=member.joined_at.strftime("%d %b %Y") if member.joined_at else "-", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="avatar", aliases=["pp"])
async def show_avatar(ctx, member: discord.Member = None):
    target = member or ctx.author
    embed = discord.Embed(title=f"🖼️ Foto Profil — {target.name}", color=0x9B59B6)
    avatar_url = target.avatar.url if target.avatar else target.default_avatar.url
    embed.set_image(url=avatar_url)
    await ctx.send(embed=embed)

# --- FUN & GAMES COMMANDS ---
@bot.command(name="roll")
async def roll_dice(ctx):
    result = random.randint(1, 100)
    await ctx.send(f"🎲 {ctx.author.mention}, hasil lemparan dadu kamu: **{result}** (1-100)")

@bot.command(name="coinflip", aliases=["koin"])
async def coin_flip(ctx):
    result = random.choice(["Kepala (Head) 🦅", "Buntut (Tail) 🪙"])
    await ctx.send(f"🪙 {ctx.author.mention} melempar koin dan mendapatkan: **{result}**")

@bot.command(name="rps")
async def rock_paper_scissors(ctx, pilihan: str):
    pilihan = pilihan.lower()
    valid_choices = ["batu", "kertas", "gunting"]
    if pilihan not in valid_choices:
        await ctx.send("⚠️ Pilihan tidak valid! Gunakan: `.rps batu`, `.rps kertas`, atau `.rps gunting`")
        return
    
    bot_choice = random.choice(valid_choices)
    
    if pilihan == bot_choice:
        result = "Seri! 🤝"
    elif (pilihan == "batu" and bot_choice == "gunting") or \
         (pilihan == "kertas" and bot_choice == "batu") or \
         (pilihan == "gunting" and bot_choice == "kertas"):
        result = "Kamu Menang! 🎉"
    else:
        result = "Kamu Kalah! 🤖"

    await ctx.send(f"Kamu memilih: **{pilihan}** | Bot memilih: **{bot_choice}**\nHasil: **{result}**")

@bot.command(name="rate")
async def rate_something(ctx, *, item: str):
    score = random.randint(0, 100)
    await ctx.send(f"⭐ Saya menilai **{item}** sebesar **{score}/100**!")

@bot.command(name="quote")
async def random_quote(ctx):
    quotes = [
        "“Kesuksesan besar dimulai dari langkah kecil yang konsisten.”",
        "“Jangan menunggu waktu yang tepat, karena waktu yang tepat adalah sekarang.”",
        "“Tetap semangat, hasil tidak akan mengkhianati usaha!”",
        "“Kegagalan adalah sukses yang tertunda, teruslah mencoba.”"
    ]
    await ctx.send(f"💬 *{random.choice(quotes)}*")

# --- UTILITY TAMBAHAN ---
@bot.command(name="calc")
async def calculator(ctx, num1: float, op: str, num2: float):
    try:
        if op == "+":
            res = num1 + num2
        elif op == "-":
            res = num1 - num2
        elif op in ["*", "x"]:
            res = num1 * num2
        elif op == "/":
            if num2 == 0:
                await ctx.send("❌ Tidak bisa membagi angka dengan nol!")
                return
            res = num1 / num2
        else:
            await ctx.send("⚠️ Operator salah! Gunakan `+`, `-`, `*`, atau `/`")
            return
        await ctx.send(f"🧮 Hasil dari `{num1} {op} {num2}` adalah **{res}**")
    except Exception:
        await ctx.send("⚠️ Format penulisan salah! Contoh: `.calc 10 + 5`")

@bot.command(name="choose")
async def choose_option(ctx, *, options: str):
    choices = [c.strip() for c in options.split(",")]
    if len(choices) < 2:
        await ctx.send("⚠️ Berikan minimal 2 pilihan yang dipisahkan dengan koma! Contoh: `.choose Makan Nasi, Makan Mie`")
        return
    chosen = random.choice(choices)
    await ctx.send(f"🤔 Dari pilihan tersebut, saya memilih: **{chosen}**!")

# ==================== RUN BOT ====================
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token bot tidak ditemukan!")
