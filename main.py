import asyncio
import datetime
import os
import random
import re
import sqlite3
import discord
from discord.ext import commands

# Konfigurasi Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ID Channel milik Anda
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050

# Cooldown XP agar user tidak spamming (User ID: timestamp)
xp_cooldowns = {}


# ==================== DATABASE LEVELING (SQLite) ====================
def init_db():
    conn = sqlite3.connect("levels.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0
        )
    """
    )
    conn.commit()
    conn.close()


init_db()


def get_user_data(user_id):
    conn = sqlite3.connect("levels.db")
    cursor = conn.cursor()
    cursor.execute("SELECT xp, level FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    if not data:
        cursor.execute(
            "INSERT INTO users (user_id, xp, level) VALUES (?, ?, ?)",
            (user_id, 0, 0),
        )
        conn.commit()
        data = (0, 0)
    conn.close()
    return data


def update_user_data(user_id, xp, level):
    conn = sqlite3.connect("levels.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET xp = ?, level = ? WHERE user_id = ?",
        (xp, level, user_id),
    )
    conn.commit()
    conn.close()


def get_top_users():
    conn = sqlite3.connect("levels.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, level, xp FROM users ORDER OR level DESC, xp DESC LIMIT 5"
    )
    data = cursor.fetchall()
    conn.close()
    return data


# Helper Function: Parse durasi waktu
def parse_duration(time_str: str) -> datetime.timedelta:
    match = re.match(r"^(\d+)([smhd])?$", time_str.lower())
    if not match:
        return None
    val, unit = match.groups()
    val = int(val)
    if unit == "s":
        return datetime.timedelta(seconds=val)
    elif unit == "m" or unit is None:
        return datetime.timedelta(minutes=val)
    elif unit == "h":
        return datetime.timedelta(hours=val)
    elif unit == "d":
        return datetime.timedelta(days=val)
    return None


@bot.event
async def on_ready():
    print(f"=== BOT ONLINE SEBAGAI {bot.user} ===")
    print("Bot siap melayani di channel general & sistem leveling aktif!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. LOGIKA SISTEM LEVELING (Gaining XP)
    now = datetime.datetime.now().timestamp()
    user_id = message.author.id

    # Cek cooldown 60 detik per user
    if user_id not in xp_cooldowns or now - xp_cooldowns[user_id] > 60:
        xp_cooldowns[user_id] = now
        current_xp, current_level = get_user_data(user_id)

        # Tambah XP acak antara 15 sampai 25
        gained_xp = random.randint(15, 25)
        new_xp = current_xp + gained_xp

        # Rumus XP per Level: level_selanjutnya = 100 * (level ** 2) + 100
        xp_needed = 100 * ((current_level + 1) ** 2)

        if new_xp >= xp_needed:
            current_level += 1
            update_user_data(user_id, new_xp, current_level)
            try:
                await message.channel.send(
                    f"🎉 Selamat {message.author.mention}, level kamu naik ke **Level {current_level}**! 🚀"
                )
            except Exception:
                pass
        else:
            update_user_data(user_id, new_xp, current_level)

    # 2. Jika berupa perintah !, jalankan perintah
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # 3. Respon otomatis tiket jika diketik di channel general
    if message.channel.id == GENERAL_CHANNEL_ID:
        try:
            async for old_msg in message.channel.history(limit=15):
                if old_msg.author.id == bot.user.id and len(old_msg.embeds) > 0:
                    await old_msg.delete()
                    await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Gagal menghapus pesan bot lama: {e}")

        embed = discord.Embed(
            title="👋 TONGSOP DI SINI! 👋",
            description="Halo! Untuk keamanan dan kenyamanan bertransaksi, silakan gunakan jalur resmi yang telah kami sediakan untuk melayani Anda :",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="🛒 Pembelian Produk Prenstore",
            value=f"• <#{TICKET_CHANNEL_ID}> • ` open-ticket `",
            inline=False,
        )

        embed.add_field(
            name="👥 Layanan jasa split Redfinger",
            value=f"• <#{TICKET_CHANNEL_ID}> • ` jasa split `",
            inline=False,
        )

        embed.add_field(
            name="📄 Note",
            value="• Harap tidak melakukan transaksi di luar tiket resmi demi keamanan Anda.\n• Tim Admin Prenstore akan merespons tiket Anda sesegera mungkin.",
            inline=False,
        )

        embed.set_footer(text="TONGSOP Assistant • Klik channel tiket di atas")

        await message.channel.send(content=f"{message.author.mention}", embed=embed)
        return

    await bot.process_commands(message)


# ==================== PERINTAH LEVELING ====================


# 1. CEK RANK / LEVEL
@bot.command(name="rank", aliases=["level"])
async def check_rank(ctx, member: discord.Member = None):
    """Cek level dan XP saat ini. Contoh: !rank atau !rank @user"""
    target = member or ctx.author
    xp, level = get_user_data(target.id)
    xp_needed = 100 * ((level + 1) ** 2)

    embed = discord.Embed(
        title=f"📊 Status Level - {target.name}", color=discord.Color.green()
    )
    embed.set_thumbnail(
        url=target.avatar.url if target.avatar else target.default_avatar.url
    )
    embed.add_field(name="Level saat ini", value=f"⭐ **{level}**", inline=True)
    embed.add_field(
        name="Total XP", value=f"✨ **{xp} / {xp_needed} XP**", inline=True
    )
    embed.set_footer(text="Aktif mengobrol di channel untuk meningkatkan level!")

    await ctx.send(embed=embed)


# 2. LEADERBOARD LEVEL
@bot.command(name="leaderboard", aliases=["lb", "top"])
async def show_leaderboard(ctx):
    """Menampilkan 5 member dengan level tertinggi"""
    top_users = get_top_users()

    embed = discord.Embed(
        title="🏆 LEADERBOARD LEVEL SERVER 🏆",
        description="Top 5 member paling aktif:",
        color=discord.Color.gold(),
    )

    if not top_users:
        embed.description = "Belum ada data level."
    else:
        for i, (u_id, lvl, xp) in enumerate(top_users, start=1):
            user = bot.get_user(u_id)
            user_name = user.name if user else f"User ID: {u_id}"
            embed.add_field(
                name=f"#{i} {user_name}",
                value=f"Level: **{lvl}** | XP: **{xp}**",
                inline=False,
            )

    await ctx.send(embed=embed)


# 3. SET LEVEL (ADMIN ONLY)
@bot.command(name="setlevel")
@commands.has_permissions(administrator=True)
async def set_level(ctx, member: discord.Member, new_level: int):
    """Perintah Admin untuk mengubah level user. Contoh: !setlevel @user 5"""
    calc_xp = 100 * (new_level**2)
    update_user_data(member.id, calc_xp, new_level)
    await ctx.send(
        f"✅ Level untuk **{member.name}** berhasil diubah menjadi **Level {new_level}**!"
    )


# ==================== PERINTAH BANTUAN & INFORMASI ====================


@bot.command(name="info", aliases=["help"])
async def show_info(ctx):
    """Menampilkan daftar lengkap perintah bot"""
    embed = discord.Embed(
        title="ℹ️ INFORMASI BOT TONGSOP Assistant ℹ️",
        description="Berikut adalah daftar perintah yang tersedia di server:",
        color=discord.Color.blue(),
    )

    embed.add_field(
        name="📈 Sistem Leveling",
        value="• `!rank` / `!level` (Cek status level & XP kamu)\n"
        "• `!leaderboard` / `!lb` (Lihat top level server)\n"
        "• `!setlevel @user [level]` (Admin: ubah level member)",
        inline=False,
    )

    embed.add_field(
        name="🛡️ Moderasi (Admin/Mod)",
        value="• `!to @user [durasi] [alasan]` (Contoh: `!to @user 1h Spam`)\n"
        "• `!unto @user` (Membatalkan timeout)\n"
        "• `!warn @user [alasan]` & `!clear [jumlah]`\n"
        "• `!kick @user` & `!ban @user`",
        inline=False,
    )

    embed.add_field(
        name="📊 Informasi & Utility",
        value="• `!price` (Daftar harga Prenstore)\n"
        "• `!payment` (Metode pembayaran resmi)\n"
        "• `!userinfo @user` & `!serverinfo` & `!ping`",
        inline=False,
    )

    embed.set_footer(text="TONGSOP Assistant • Gunakan prefix ! di awal perintah")
    await ctx.send(embed=embed)


# ==================== PERINTAH MODERASI & LAINNYA ====================


@bot.command(name="to", aliases=["timeout"])
@commands.has_permissions(moderate_members=True)
async def timeout_member(
    ctx,
    member: discord.Member,
    duration_str: str = "10m",
    *,
    reason: str = "Tidak ada alasan yang diberikan.",
):
    duration = parse_duration(duration_str)
    if duration is None:
        await ctx.send(
            "⚠️ Format waktu salah! Gunakan contoh: `10m` (10 menit), `1h` (1 jam)."
        )
        return
    try:
        await member.timeout(duration, reason=reason)
        await ctx.send(
            f"🤐 **{member.name}** berhasil di-timeout selama **{duration_str}**. Alasan: {reason}"
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan timeout: {e}")


@bot.command(name="unto", aliases=["untimeout"])
@commands.has_permissions(moderate_members=True)
async def untimeout_member(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"🔊 Timeout untuk **{member.name}** telah dicabut!")
    except Exception as e:
        await ctx.send(f"❌ Gagal menghapus timeout: {e}")


@bot.command(name="warn")
@commands.has_permissions(moderate_members=True)
async def warn_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan yang diberikan."
):
    embed = discord.Embed(
        title="⚠️ PERINGATAN RESMI ⚠️",
        description=f"Member **{member.mention}** telah diberi peringatan oleh Admin/Moderator.",
        color=discord.Color.gold(),
    )
    embed.add_field(name="Alasan", value=reason, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan yang diberikan."
):
    try:
        await member.ban(reason=reason)
        await ctx.send(
            f"✅ **{member.name}** berhasil di-ban dari server. Alasan: {reason}"
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan ban: {e}")


@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan yang diberikan."
):
    try:
        await member.kick(reason=reason)
        await ctx.send(
            f"✅ **{member.name}** berhasil di-kick dari server. Alasan: {reason}"
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan kick: {e}")


@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 5):
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Berhasil menghapus {len(deleted)-1} pesan.")
    await asyncio.sleep(3)
    await msg.delete()


@bot.command(name="ping")
async def check_ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latensi bot: **{latency}ms**")


@bot.command(name="userinfo", aliases=["whois"])
async def user_info(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [role.mention for role in member.roles if role.name != "@everyone"]
    embed = discord.Embed(
        title=f"👤 Informasi Pengguna - {member.name}", color=discord.Color.blue()
    )
    embed.set_thumbnail(
        url=member.avatar.url if member.avatar else member.default_avatar.url
    )
    embed.add_field(name="Nama Discord", value=str(member), inline=True)
    embed.add_field(name="ID Discord", value=member.id, inline=True)
    embed.add_field(
        name="Bergabung di Server",
        value=member.joined_at.strftime("%d-%m-%Y %H:%M"),
        inline=False,
    )
    embed.add_field(
        name=f"Role ({len(roles)})",
        value=", ".join(roles) if roles else "Tidak ada role",
        inline=False,
    )
    await ctx.send(embed=embed)


@bot.command(name="serverinfo")
async def server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📊 Informasi Server - {guild.name}", color=discord.Color.green()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(
        name="Pemilik Server",
        value=guild.owner.mention if guild.owner else "N/A",
        inline=True,
    )
    embed.add_field(name="Total Anggota", value=guild.member_count, inline=True)
    embed.add_field(name="Total Role", value=len(guild.roles), inline=True)
    await ctx.send(embed=embed)


@bot.command(name="price", aliases=["pricelist", "harga"])
async def show_price(ctx):
    embed = discord.Embed(
        title="🛒 DAFTAR HARGA & LAYANAN PRENSTORE 🛒",
        description="Silakan buka tiket resmi untuk memesan produk di bawah ini:",
        color=discord.Color.purple(),
    )
    embed.add_field(
        name="📱 Produk Redfinger & Split",
        value="• Jasa Split Redfinger\n• Sewa Cloud Phone / VIP",
        inline=False,
    )
    embed.add_field(
        name="💳 Pembelian Tiket",
        value=f"Silakan klik channel tiket: <#{TICKET_CHANNEL_ID}>",
        inline=False,
    )
    embed.set_footer(text="TONGSOP Store • Hubungi Admin via Tiket")
    await ctx.send(embed=embed)


@bot.command(name="payment", aliases=["pembayaran"])
async def show_payment(ctx):
    embed = discord.Embed(
        title="💳 METODE PEMBAYARAN RESMI PRENSTORE 💳",
        description="Berikut adalah saluran pembayaran resmi yang didukung:",
        color=discord.Color.gold(),
    )
    embed.add_field(
        name="E-Wallet & Bank",
        value="• DANA\n• OVO / GoPay\n• QRIS All Payment\n• Transfer Bank",
        inline=False,
    )
    await ctx.send(embed=embed)


# Error Handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Anda tidak memiliki izin untuk menggunakan perintah ini!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "⚠️ Argumen kurang lengkap! Ketik `!info` untuk melihat petunjuk."
        )
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        raise error


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("ERROR: BOT_TOKEN tidak ditemukan di Environment Variables Railway!")
else:
    bot.run(TOKEN)
