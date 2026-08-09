import asyncio
import datetime
import os
import re
import discord
from discord.ext import commands

# Konfigurasi Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID Channel milik Anda
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050


# Helper Function: Parse durasi waktu (misal: 30m, 1h, 1d)
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
    print("Bot siap melayani di channel general & menjalankan seluruh perintah Admin!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Jika berupa perintah dengan prefix !, jalankan perintah
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # 2. Respon otomatis tiket jika diketik di channel general
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


# ==================== PERINTAH BANTUAN & INFORMASI ====================


# 1. PERINTAH INFO / HELP
@bot.command(name="info", aliases=["help"])
async def show_info(ctx):
    """Menampilkan daftar lengkap perintah bot"""
    embed = discord.Embed(
        title="ℹ️ INFORMASI BOT TONGSOP Assistant ℹ️",
        description="Berikut adalah daftar perintah yang tersedia di server:",
        color=discord.Color.blue(),
    )

    embed.add_field(
        name="🛡️ Moderasi (Admin/Mod)",
        value="• `!to @user [durasi] [alasan]` (Contoh: `!to @user 1h Spam`)\n"
        "• `!unto @user` (Membatalkan timeout)\n"
        "• `!warn @user [alasan]` (Beri peringatan)\n"
        "• `!kick @user [alasan]` & `!ban @user [alasan]`\n"
        "• `!clear [jumlah]` (Hapus pesan banyak)\n"
        "• `!slowmode [detik]` & `!lock` / `!unlock`",
        inline=False,
    )

    embed.add_field(
        name="📊 Informasi & Utility",
        value="• `!userinfo @user` (Cek info akun member)\n"
        "• `!serverinfo` (Cek statistik server)\n"
        "• `!price` (Daftar harga Prenstore)\n"
        "• `!payment` (Metode pembayaran resmi)\n"
        "• `!ping` (Cek respon bot)",
        inline=False,
    )

    embed.set_footer(text="TONGSOP Assistant • Gunakan prefix ! di awal perintah")
    await ctx.send(embed=embed)


# ==================== PERINTAH MODERASI ====================


# 2. PERINTAH TIMEOUT / TO
@bot.command(name="to", aliases=["timeout"])
@commands.has_permissions(moderate_members=True)
async def timeout_member(
    ctx,
    member: discord.Member,
    duration_str: str = "10m",
    *,
    reason: str = "Tidak ada alasan yang diberikan.",
):
    """Contoh: !to @user 1h Berisik / !to @user 30m Spam"""
    duration = parse_duration(duration_str)
    if duration is None:
        await ctx.send(
            "⚠️ Format waktu salah! Gunakan contoh: `10m` (10 menit), `1h` (1 jam), `1d` (1 hari)."
        )
        return

    try:
        await member.timeout(duration, reason=reason)
        await ctx.send(
            f"🤐 **{member.name}** berhasil di-timeout selama **{duration_str}**. Alasan: {reason}"
        )
    except Exception as e:
        await ctx.send(
            f"❌ Gagal melakukan timeout: {e}\n*(Pastikan Role Bot berada di atas Role target)*"
        )


# 3. PERINTAH UNTIMEOUT / UNTO
@bot.command(name="unto", aliases=["untimeout"])
@commands.has_permissions(moderate_members=True)
async def untimeout_member(ctx, member: discord.Member):
    """Contoh: !unto @user"""
    try:
        await member.timeout(None)
        await ctx.send(f"🔊 Timeout untuk **{member.name}** telah dicabut!")
    except Exception as e:
        await ctx.send(f"❌ Gagal menghapus timeout: {e}")


# 4. PERINTAH WARN
@bot.command(name="warn")
@commands.has_permissions(moderate_members=True)
async def warn_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan yang diberikan."
):
    """Contoh: !warn @user Jangan spamming"""
    embed = discord.Embed(
        title="⚠️ PERINGATAN RESMI ⚠️",
        description=f"Member **{member.mention}** telah diberi peringatan oleh Admin/Moderator.",
        color=discord.Color.gold(),
    )
    embed.add_field(name="Alasan", value=reason, inline=False)
    embed.set_footer(text="Harap patuhi aturan server demi kenyamanan bersama.")
    await ctx.send(embed=embed)


# 5. PERINTAH BAN
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan yang diberikan."
):
    """Contoh: !ban @user Spammer"""
    try:
        await member.ban(reason=reason)
        await ctx.send(
            f"✅ **{member.name}** berhasil di-ban dari server. Alasan: {reason}"
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan ban: {e}")


# 6. PERINTAH KICK
@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan yang diberikan."
):
    """Contoh: !kick @user Melanggar aturan"""
    try:
        await member.kick(reason=reason)
        await ctx.send(
            f"✅ **{member.name}** berhasil di-kick dari server. Alasan: {reason}"
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan kick: {e}")


# 7. PERINTAH CLEAR
@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 5):
    """Contoh: !clear 10"""
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Berhasil menghapus {len(deleted)-1} pesan.")
    await asyncio.sleep(3)
    await msg.delete()


# 8. PERINTAH SLOWMODE
@bot.command(name="slowmode")
@commands.has_permissions(manage_channels=True)
async def set_slowmode(ctx, seconds: int = 0):
    """Contoh: !slowmode 5 (atau 0 untuk matikan)"""
    await ctx.channel.edit(slowmode_delay=seconds)
    if seconds == 0:
        await ctx.send("🚀 Slowmode berhasil dimatikan!")
    else:
        await ctx.send(f"⏱️ Slowmode diatur ke **{seconds} detik** per pesan.")


# 9. PERINTAH LOCK & UNLOCK
@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock_channel(ctx):
    """Mengunci channel"""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Channel ini telah dikunci oleh Admin.")


@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock_channel(ctx):
    """Membuka channel"""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Channel ini telah dibuka kembali.")


# ==================== PERINTAH UTILITY & UTILS ====================


# 10. PERINTAH PING
@bot.command(name="ping")
async def check_ping(ctx):
    """Cek koneksi bot"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latensi bot: **{latency}ms**")


# 11. PERINTAH USERINFO
@bot.command(name="userinfo", aliases=["whois"])
async def user_info(ctx, member: discord.Member = None):
    """Contoh: !userinfo @user"""
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
        name="Pembuatan Akun",
        value=member.created_at.strftime("%d-%m-%Y %H:%M"),
        inline=False,
    )
    embed.add_field(
        name=f"Role ({len(roles)})",
        value=", ".join(roles) if roles else "Tidak ada role",
        inline=False,
    )

    await ctx.send(embed=embed)


# 12. PERINTAH SERVERINFO
@bot.command(name="serverinfo")
async def server_info(ctx):
    """Cek informasi server"""
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
    embed.add_field(
        name="Dibuat Pada", value=guild.created_at.strftime("%d-%m-%Y"), inline=False
    )

    await ctx.send(embed=embed)


# 13. PERINTAH PRICELIST
@bot.command(name="price", aliases=["pricelist", "harga"])
async def show_price(ctx):
    """Menampilkan harga produk"""
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


# 14. PERINTAH PAYMENT
@bot.command(name="payment", aliases=["pembayaran"])
async def show_payment(ctx):
    """Menampilkan opsi pembayaran"""
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
    embed.add_field(
        name="⚠️ Perhatian",
        value="Selalu konfirmasi nomor tujuan pembayaran hanya di dalam **Tiket Resmi**!",
        inline=False,
    )
    await ctx.send(embed=embed)


# Error Handling Umum
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
