import discord
from discord.ext import commands
import os
import random
import datetime
import sqlite3

# ==================== CONFIG BOT ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Channel ID Target (Dari skrip awal Anda)
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050

xp_cooldowns = {}

# ==================== DATABASE SETUP (LEVEL & XP) ====================
def init_db():
    with sqlite3.connect("levels.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0
            )
        """)
        conn.commit()

init_db()

def get_user_data(user_id):
    with sqlite3.connect("levels.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT xp, level FROM users WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        if not data:
            cursor.execute("INSERT INTO users (user_id, xp, level) VALUES (?, ?, ?)", (user_id, 0, 0))
            conn.commit()
            data = (0, 0)
        return data

def update_user_data(user_id, xp, level):
    with sqlite3.connect("levels.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (xp, level, user_id))
        conn.commit()

def get_xp_needed(level):
    return (level + 1) * 100

# ==================== EVENTS BOT ====================
@bot.event
async def on_ready():
    print(f"✨ Bot Berhasil Terhubung as {bot.user}!")
    print("🚀 Siap melayani server dengan fitur Role, Leveling, dan Panel Tiket!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Sistem Leveling & XP Otomatis (Cooldown 60 Detik per User)
    now = datetime.datetime.now().timestamp()
    user_id = message.author.id

    if user_id not in xp_cooldowns or (now - xp_cooldowns[user_id]) > 60:
        xp_cooldowns[user_id] = now
        current_xp, current_level = get_user_data(user_id)

        gained_xp = random.randint(15, 25)
        new_xp = current_xp + gained_xp
        xp_needed = get_xp_needed(current_level)

        if new_xp >= xp_needed:
            current_level += 1
            new_xp = new_xp - xp_needed
            update_user_data(user_id, new_xp, current_level)

            embed = discord.Embed(
                title="🎉 LEVEL UP EXCELLENT!",
                description=f"Hebat {message.author.mention}! Keaktifanmu membawamu naik ke **Level {current_level}** 🚀",
                color=0x2ECC71
            )
            embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
            try:
                await message.channel.send(embed=embed)
            except Exception:
                pass
        else:
            update_user_data(user_id, new_xp, current_level)

    # 2. Auto Response Tiket di Channel General (Fitur dari skrip awal Anda)
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

@bot.command(name="info", aliases=["help", "h"])
async def show_info(ctx):
    embed = discord.Embed(
        title="📌 PUSAT BANTUAN & DAFTAR PERINTAH",
        description="Gunakan awalan titik (`.`) untuk menjalankan perintah berikut:",
        color=0x3498DB,
    )
    embed.add_field(
        name="🛡️ Moderasi & Role",
        value="`.role @user [nama role]` — Memberikan/melepas role member\n"
              "`.clear [jumlah]` (alias `.purge`/`.cls`) — Menghapus pesan chat",
        inline=False
    )
    embed.add_field(
        name="📊 Leveling & XP",
        value="`.rank` (alias `.lvl`/`.level`) — Cek level dan XP kamu",
        inline=False
    )
    embed.add_field(
        name="🛠️ Utility & Informasi (Bisa Disingkat)",
        value="`.ping` — Cek kecepatan respon bot\n"
              "`.say [pesan]` — Menyuruh bot mengulang pesan\n"
              "`.server` (alias `.serv`/`.s`) — Info lengkap server\n"
              "`.whois` (alias `.who`/`.u`) — Detail profil member\n"
              "`.avatar` (alias `.pp`/`.av`) — Foto profil member",
        inline=False
    )
    embed.add_field(
        name="🎮 Fun, Games & Alat Praktis",
        value="`.roll` — Acak angka 1-100\n"
              "`.coinflip` (alias `.koin`) — Lempar koin\n"
              "`.rps [batu/kertas/gunting]` — Main suit\n"
              "`.rate [sesuatu]` — Nilai sesuatu 0-100\n"
              "`.calc [angka1] [+|-|*|/] [angka2]` — Kalkulator\n"
              "`.choose [pilihan1], [pilihan2]` — Pilihkan opsi",
        inline=False
    )
    embed.set_footer(text="TONGSOP Store • All Rights Reserved")
    await ctx.send(embed=embed)

# --- MODERASI: MEMBERI / MENGHAPUS ROLE ---
@bot.command(name="role", aliases=["give role", "addrole"])
@commands.has_permissions(manage_roles=True)
async def manage_role(ctx, member: discord.Member, *, rolename: str):
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=rolename)
    
    if not role:
        try:
            role = await guild.create_role(name=rolename, reason=f"Dibuat otomatis oleh perintah .role dari {ctx.author}")
            await ctx.send(⚠️ Role `{rolename}` tidak ditemukan di server, tetapi berhasil dibuat secara otomatis!")
        except Exception as e:
            await ctx.send(f"❌ Gagal membuat role baru: {e}")
            return

    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"✅ Berhasil **mencabut** role `{role.name}` dari {member.mention}.")
    else:
        try:
            await member.add_roles(role)
            await ctx.send(f"✅ Berhasil **memberikan** role `{role.name}` kepada {member.mention}!")
        except Exception:
            await ctx.send("❌ Bot gagal memberikan role tersebut. Pastikan posisi Role Bot di pengaturan server berada di atas role yang ingin diberikan!")

@manage_role.error
async def role_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Maaf, kamu tidak memiliki izin *Manage Roles* untuk menggunakan perintah ini!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Format salah! Contoh penggunaan: `.role @NamaMember VIP`")

# --- LEVEL & XP COMMANDS ---
@bot.command(name="rank", aliases=["lvl", "level"])
async def check_rank(ctx, member: discord.Member = None):
    target = member or ctx.author
    xp, level = get_user_data(target.id)
    xp_needed = get_xp_needed(level)

    percent = int((xp / xp_needed) * 100) if xp_needed > 0 else 0
    filled = int(10 * (xp / xp_needed)) if xp_needed > 0 else 0
    bar = "🟩" * filled + "⬛" * (10 - filled)

    embed = discord.Embed(title=f"📊 Status Kartu Profil — {target.display_name}", color=0x3498DB)
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.add_field(name="✨ Level", value=f"**{level}**", inline=True)
    embed.add_field(name="⚡ Total XP", value=f"**{xp} / {xp_needed}**", inline=True)
    embed.add_field(name="📈 Progress", value=f"{bar} **{percent}%**", inline=False)
    await ctx.send(embed=embed)

# --- MODERASI PENGHAPUS PESAN ---
@bot.command(name="clear", aliases=["purge", "cls"])
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 5):
    if amount < 1:
        await ctx.send("⚠️ Masukkan jumlah pesan yang valid untuk dihapus (minimal 1).")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Berhasil menghapus **{len(deleted) - 1}** pesan.")
    
    import asyncio
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass

@clear_messages.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Maaf, kamu tidak memiliki izin *Manage Messages* untuk menggunakan perintah ini!")

# --- UTILITY COMMANDS (DENGAN ALIASES/SINGKATAN) ---
@bot.command(name="say")
async def say_message(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command(name="server", aliases=["serverinfo", "serv", "s"])
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

@bot.command(name="whois", aliases=["who", "u", "userinfo"])
async def whois_member(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 User Info — {member.name}", color=0x3498DB)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
    embed.add_field(name="Nama Panggilan", value=member.display_name, inline=True)
    embed.add_field(name="Bergabung Sejak", value=member.joined_at.strftime("%d %b %Y") if member.joined_at else "-", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="avatar", aliases=["pp", "av"])
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
