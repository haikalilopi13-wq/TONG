import asyncio
import datetime
import os
import random
import re
import sqlite3
import discord
from discord.ext import commands

# ==================== KONFIGURASI BOT ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# ID Channel Discord Anda
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050

# Cooldown XP (User ID: timestamp)
xp_cooldowns = {}


# ==================== DATABASE LEVELING ====================
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
        "SELECT user_id, level, xp FROM users ORDER BY level DESC, xp DESC LIMIT 5"
    )
    data = cursor.fetchall()
    conn.close()
    return data


# Helper Function: Hitung Kebutuhan XP & Progress Bar
def get_xp_needed(level):
    return (level + 1) * 100


def create_progress_bar(current, total, length=10):
    percent = max(0, min(1, current / total)) if total > 0 else 0
    filled = int(length * percent)
    return "█" * filled + "░" * (length - filled)


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


# ==================== EVENT BOT ====================


@bot.event
async def on_ready():
    print("==========================================")
    print(f"  🤖 BOT ONLINE SEBAGAI : {bot.user}")
    print("  PREFIX BOT          : .")
    print("==========================================")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. SISTEM LEVELING OTOMATIS
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

            embed = discord.Embed(
                title="🎉 LEVEL UP!",
                description=f"Selamat {message.author.mention}, kamu telah naik ke **Level {current_level}**! 🚀",
                color=0x57F287,
            )
            try:
                await message.channel.send(embed=embed)
            except Exception:
                pass
        else:
            update_user_data(user_id, new_xp, current_level)

    # 2. EKSEKUSI PERINTAH PREFIKS '.'
    if message.content.startswith("."):
        await bot.process_commands(message)
        return

    # 3. RESPON OTOMATIS CHANNEL GENERAL
    if message.channel.id == GENERAL_CHANNEL_ID:
        try:
            async for old_msg in message.channel.history(limit=15):
                if old_msg.author.id == bot.user.id and len(old_msg.embeds) > 0:
                    await old_msg.delete()
                    await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Gagal menghapus pesan bot lama: {e}")

        embed = discord.Embed(
            title="✨ PRENSTORE - BANTUAN TIKET ✨",
            description=(
                "Halo! Demi keamanan dan kenyamanan bertransaksi, silakan gunakan "
                "jalur resmi yang telah kami sediakan di bawah ini:"
            ),
            color=0x5865F2,
        )

        embed.add_field(
            name="🛒 Pembelian Produk",
            value=f"└ <#{TICKET_CHANNEL_ID}> • Klik ` open-ticket `",
            inline=False,
        )
        embed.add_field(
            name="👥 Layanan Jasa Split",
            value=f"└ <#{TICKET_CHANNEL_ID}> • Klik ` jasa split `",
            inline=False,
        )
        embed.add_field(
            name="📌 Catatan Penting",
            value="• Hindari transaksi di luar tiket resmi untuk mencegah penipuan.\n• Tim Admin akan membalas tiket Anda secepat mungkin.",
            inline=False,
        )
        embed.set_footer(
            text="TONGSOP Assistant • Gunakan channel tiket resmi"
        )

        await message.channel.send(content=f"{message.author.mention}", embed=embed)
        return

    await bot.process_commands(message)


# ==================== PERINTAH LEVELING ====================


@bot.command(name="rank", aliases=["level"])
async def check_rank(ctx, member: discord.Member = None):
    """Cek level dan XP saat ini."""
    target = member or ctx.author
    xp, level = get_user_data(target.id)
    xp_needed = get_xp_needed(level)
    progress_bar = create_progress_bar(xp, xp_needed)
    percent = int((xp / xp_needed) * 100) if xp_needed > 0 else 0

    embed = discord.Embed(
        title=f"📊 Status Level — {target.name}", color=0x5865F2
    )
    embed.set_thumbnail(
        url=target.avatar.url if target.avatar else target.default_avatar.url
    )

    embed.add_field(name="⭐ Level", value=f"` {level} `", inline=True)
    embed.add_field(
        name="✨ Total XP", value=f"` {xp} / {xp_needed} `", inline=True
    )
    embed.add_field(
        name="📈 Progress",
        value=f"`{progress_bar}` **{percent}%**",
        inline=False,
    )

    embed.set_footer(text="Aktiflah mengobrol untuk meningkatkan level!")
    await ctx.send(embed=embed)


@bot.command(name="leaderboard", aliases=["lb", "top"])
async def show_leaderboard(ctx):
    """Menampilkan 5 member dengan level tertinggi."""
    top_users = get_top_users()

    embed = discord.Embed(
        title="🏆 LEADERBOARD TERTINGGI 🏆",
        description="Berikut daftar member paling aktif di server:",
        color=0xFEE75C,
    )

    if not top_users:
        embed.description = "Belum ada data level terdaftar."
    else:
        ranks = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, (u_id, lvl, xp) in enumerate(top_users):
            user = bot.get_user(u_id)
            user_name = user.name if user else f"User ID: {u_id}"
            badge = ranks[i] if i < len(ranks) else "🏅"

            embed.add_field(
                name=f"{badge} #{i+1} {user_name}",
                value=f"└ **Level {lvl}** • `{xp} XP`",
                inline=False,
            )

    embed.set_footer(text="TONGSOP Assistant • Leveling System")
    await ctx.send(embed=embed)


@bot.command(name="addxp")
@commands.has_permissions(administrator=True)
async def add_xp(ctx, member: discord.Member, amount: int):
    """Admin: Menambah XP pengguna."""
    current_xp, current_level = get_user_data(member.id)
    new_xp = current_xp + amount
    xp_needed = get_xp_needed(current_level)

    while new_xp >= xp_needed:
        new_xp -= xp_needed
        current_level += 1
        xp_needed = get_xp_needed(current_level)

    update_user_data(member.id, new_xp, current_level)

    embed = discord.Embed(
        title="✅ PENAMBAHAN XP BERHASIL",
        description=f"Berhasil menambahkan **+{amount} XP** untuk {member.mention}.",
        color=0x57F287,
    )
    embed.add_field(
        name="Status Terbaru",
        value=f"• **Level:** {current_level}\n• **XP:** {new_xp} / {xp_needed}",
        inline=False,
    )
    await ctx.send(embed=embed)


@bot.command(name="setlevel")
@commands.has_permissions(administrator=True)
async def set_level(ctx, member: discord.Member, new_level: int):
    """Admin: Mengubah level pengguna secara instan."""
    update_user_data(member.id, 0, new_level)
    embed = discord.Embed(
        title="✅ LEVEL BERHASIL DIUBAH",
        description=f"Level untuk {member.mention} berhasil diatur ke **Level {new_level}**.",
        color=0x57F287,
    )
    await ctx.send(embed=embed)


# ==================== PERINTAH BANTUAN & BANTUAN ====================


@bot.command(name="info", aliases=["help"])
async def show_info(ctx):
    """Daftar perintah bot lengkap."""
    embed = discord.Embed(
        title="ℹ️ PUSAT BANTUAN TONGSOP ASSISTANT",
        description="Gunakan awalan titik (`.`) untuk menjalankan setiap perintah:",
        color=0x5865F2,
    )

    embed.add_field(
        name="📈 Sistem Level",
        value="• `.rank` / `.level` — Cek status level & XP\n"
        "• `.leaderboard` / `.lb` — Top 5 member paling aktif\n"
        "• `.addxp @user [jumlah]` — Tambah XP (Admin)\n"
        "• `.setlevel @user [level]` — Ubah level (Admin)",
        inline=False,
    )

    embed.add_field(
        name="🛡️ Moderasi Server",
        value="• `.to @user [durasi] [alasan]` — Timeout member (Cth: `.to @user 1h Spam`)\n"
        "• `.unto @user` — Hapus status timeout\n"
        "• `.warn @user [alasan]` — Berikan peringatan\n"
        "• `.clear [jumlah]` — Hapus riwayat pesan\n"
        "• `.kick @user` & `.ban @user` — Keluarkan member",
        inline=False,
    )

    embed.add_field(
        name="📊 Informasi & Layanan",
        value="• `.price` — Informasi daftar harga Prenstore\n"
        "• `.payment` — Saluran pembayaran resmi\n"
        "• `.userinfo @user` — Detail akun pengguna\n"
        "• `.serverinfo` — Detail informasi server\n"
        "• `.ping` — Cek kecepatan respon bot",
        inline=False,
    )

    embed.set_footer(text="TONGSOP Assistant • Always Ready to Serve")
    await ctx.send(embed=embed)


# ==================== MODERASI & UTILITY ====================


@bot.command(name="to", aliases=["timeout"])
@commands.has_permissions(moderate_members=True)
async def timeout_member(
    ctx,
    member: discord.Member,
    duration_str: str = "10m",
    *,
    reason: str = "Tidak ada alasan.",
):
    duration = parse_duration(duration_str)
    if duration is None:
        await ctx.send(
            "⚠️ Format waktu salah! Contoh: `.to @user 10m` atau `.to @user 1h`."
        )
        return
    try:
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(
            title="🤐 TIMEOUT BERHASIL",
            description=f"**{member.name}** telah di-timeout selama **{duration_str}**.\n**Alasan:** {reason}",
            color=0xED4245,
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan timeout: {e}")


@bot.command(name="unto", aliases=["untimeout"])
@commands.has_permissions(moderate_members=True)
async def untimeout_member(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"🔊 Status timeout untuk **{member.name}** telah dicabut.")
    except Exception as e:
        await ctx.send(f"❌ Gagal menghapus timeout: {e}")


@bot.command(name="warn")
@commands.has_permissions(moderate_members=True)
async def warn_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan."
):
    embed = discord.Embed(
        title="⚠️ PERINGATAN MODERASI",
        description=f"Peringatan resmi diberikan kepada {member.mention}.",
        color=0xFEE75C,
    )
    embed.add_field(name="Alasan", value=reason, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan."
):
    try:
        await member.ban(reason=reason)
        await ctx.send(
            f"✅ **{member.name}** berhasil di-ban dari server. Alasan: {reason}"
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal ban: {e}")


@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan."
):
    try:
        await member.kick(reason=reason)
        await ctx.send(
            f"✅ **{member.name}** berhasil di-kick dari server. Alasan: {reason}"
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal kick: {e}")


@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 5):
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Berhasil membersihkan {len(deleted)-1} pesan.")
    await asyncio.sleep(3)
    await msg.delete()


@bot.command(name="ping")
async def check_ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"**Pong!** Latensi bot saat ini: `{latency}ms`")


@bot.command(name="userinfo", aliases=["whois"])
async def user_info(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [role.mention for role in member.roles if role.name != "@everyone"]

    embed = discord.Embed(
        title=f"👤 Informasi Pengguna — {member.name}", color=0x5865F2
    )
    embed.set_thumbnail(
        url=member.avatar.url if member.avatar else member.default_avatar.url
    )
    embed.add_field(name="ID Discord", value=f"`{member.id}`", inline=True)
    embed.add_field(
        name="Bergabung Server",
        value=member.joined_at.strftime("%d %b %Y"),
        inline=True,
    )
    embed.add_field(
        name=f"Role ({len(roles)})",
        value=", ".join(roles) if roles else "Tidak ada role khusus",
        inline=False,
    )
    await ctx.send(embed=embed)


@bot.command(name="serverinfo")
async def server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📊 Informasi Server — {guild.name}", color=0x57F287
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(
        name="Pemilik",
        value=guild.owner.mention if guild.owner else "N/A",
        inline=True,
    )
    embed.add_field(name="Total Member", value=f"`{guild.member_count}`", inline=True)
    embed.add_field(name="Total Role", value=f"`{len(guild.roles)}`", inline=True)
    await ctx.send(embed=embed)


@bot.command(name="price", aliases=["pricelist", "harga"])
async def show_price(ctx):
    embed = discord.Embed(
        title="🛒 DAFTAR HARGA & LAYANAN PRENSTORE 🛒",
        description="Buka tiket resmi untuk memesan produk di bawah ini:",
        color=0x9B59B6,
    )
    embed.add_field(
        name="📱 Produk Redfinger & Split",
        value="• Jasa Split Redfinger\n• Sewa Cloud Phone / VIP",
        inline=False,
    )
    embed.add_field(
        name="💳 Pembelian Tiket",
        value=f"Silakan menuju channel tiket: <#{TICKET_CHANNEL_ID}>",
        inline=False,
    )
    embed.set_footer(text="TONGSOP Store • Pelayanan Cepat & Aman")
    await ctx.send(embed=embed)


@bot.command(name="payment", aliases=["pembayaran"])
async def show_payment(ctx):
    embed = discord.Embed(
        title="💳 METODE PEMBAYARAN RESMI PRENSTORE 💳",
        description="Berikut opsi transaksi resmi yang tersedia:",
        color=0xFEE75C,
    )
    embed.add_field(
        name="E-Wallet & Transfer Bank",
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
        await ctx.send("⚠️ Argumen kurang lengkap! Ketik `.info` untuk bantuan.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        raise error


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("ERROR: BOT_TOKEN tidak ditemukan di Environment Variables Railway!")
else:
    bot.run(TOKEN)
