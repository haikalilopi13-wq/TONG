import asyncio
import datetime
import os
import random
import re
import sqlite3
import discord
from discord.ext import commands

# ==================== CONFIG BOT ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Channel ID Target
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050

xp_cooldowns = {}


# ==================== DATABASE SETUP ====================
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


def get_xp_needed(level):
    return (level + 1) * 100


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


# ==================== EVENTS BOT ====================


@bot.event
async def on_ready():
    print(f"✨ Tongsop Assistant Berhasil Terhubung as {bot.user}!")
    print("🚀 Status: Siap melayani server dengan sistem interaktif maksimal.")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Sistem Leveling & XP Otomatis (Cooldown 60 Detik)
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
                title="🎉 LEVEL UP EXCELLENT!",
                description=f"Hebat {message.author.mention}! Semangat aktifmu membawamu naik ke **Level {current_level}** 🚀",
                color=0x2ECC71,
            )
            embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
            try:
                await message.channel.send(embed=embed)
            except Exception:
                pass
        else:
            update_user_data(user_id, new_xp, current_level)

    # 2. Eksekusi Command Berbasis Prefix
    if message.content.startswith("."):
        await bot.process_commands(message)
        return

    # 3. Auto Response Tiket Premium di Channel General
    if message.channel.id == GENERAL_CHANNEL_ID:
        try:
            async for old_msg in message.channel.history(limit=15):
                if old_msg.author.id == bot.user.id and len(old_msg.embeds) > 0:
                    await old_msg.delete()
                    await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Gagal membersihkan pesan lama: {e}")

        embed = discord.Embed(
            title="🛒 PRENSTORE OFFICIAL TICKET SYSTEM",
            description="Selamat datang! Butuh bantuan cepat atau ingin melakukan pemesanan produk? Silakan akses panel tiket di bawah ini.",
            color=0x3498DB,
        )

        embed.add_field(
            name="📦 Layanan Order Produk",
            value=f"👉 Masuk ke <#{TICKET_CHANNEL_ID}> (Pilih tombol ` open-ticket `)",
            inline=False,
        )
        embed.add_field(
            name="⚡ Layanan Jasa Split Redfinger",
            value=f"👉 Masuk ke <#{TICKET_CHANNEL_ID}> (Pilih tombol ` jasa split `)",
            inline=False,
        )
        embed.add_field(
            name="🛡️ Keamanan & Kenyamanan",
            value="• **Dilarang keras** melakukan transaksi di luar sistem tiket!\n• Admin dan Staff resmi akan merespon dengan cepat.",
            inline=False,
        )
        embed.set_footer(text="TONGSOP Store • Secure & Trusted Service")

        await message.channel.send(content=f"{message.author.mention}", embed=embed)
        return

    await bot.process_commands(message)


# ==================== COMMANDS LEVELING & LEADERBOARD ====================


@bot.command(name="rank", aliases=["level"])
async def check_rank(ctx, member: discord.Member = None):
    target = member or ctx.author
    xp, level = get_user_data(target.id)
    xp_needed = get_xp_needed(level)

    percent = int((xp / xp_needed) * 100) if xp_needed > 0 else 0
    filled = int(10 * (xp / xp_needed)) if xp_needed > 0 else 0
    bar = "🟩" * filled + "⬛" * (10 - filled)

    embed = discord.Embed(
        title=f"📊 Status Kartu Profil — {target.display_name}", color=0x3498DB
    )
    embed.set_thumbnail(
        url=target.avatar.url if target.avatar else target.default_avatar.url
    )

    embed.add_field(name="✨ Level", value=f"**{level}**", inline=True)
    embed.add_field(name="⚡ Total XP", value=f"**{xp} / {xp_needed}**", inline=True)
    embed.add_field(name="📈 Progress Level", value=f"{bar} **{percent}%**", inline=False)
    embed.set_footer(text=f"Diminta oleh {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)


@bot.command(name="leaderboard", aliases=["lb", "top"])
async def show_leaderboard(ctx):
    top_users = get_top_users()

    if not top_users:
        await ctx.send("❌ Belum ada data peringkat member yang tercatat.")
        return

    # Tampilan Premium Estetik ala Arcane Bot menggunakan Embed Gelap yang Bersih
    embed = discord.Embed(color=0x2B2D31)
    
    if ctx.guild.icon:
        embed.set_author(name=f"{ctx.guild.name} server Leaderboard", icon_url=ctx.guild.icon.url)
    else:
        embed.set_author(name=f"{ctx.guild.name} server Leaderboard")

    description_text = ""
    medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]

    for i, (u_id, lvl, xp) in enumerate(top_users):
        user = bot.get_user(u_id)
        if not user:
            try:
                user = await bot.fetch_user(u_id)
            except Exception:
                user = None

        name = user.name if user else f"User_{u_id}"
        rank_icon = medals[i] if i < len(medals) else "🔹"
        
        xp_needed = get_xp_needed(lvl)
        progress = int((xp / xp_needed) * 12) if xp_needed > 0 else 0
        progress = max(0, min(progress, 12))
        
        # Progress Bar Solid Modern
        bar = "█" * progress + "░" * (12 - progress)

        description_text += f"{rank_icon} **{name}**\n"
        description_text += f"└ `LVL {lvl}` • `{xp}/{xp_needed} XP`\n"
        description_text += f"`{bar}`\n\n"

    embed.description = description_text
    embed.set_footer(text="Overall XP • Sistem Peringkat Resmi Tongsop")
    
    await ctx.send(embed=embed)


@bot.command(name="addxp")
@commands.has_permissions(administrator=True)
async def add_xp(ctx, member: discord.Member, amount: int):
    current_xp, current_level = get_user_data(member.id)
    new_xp = current_xp + amount
    xp_needed = get_xp_needed(current_level)

    while new_xp >= xp_needed:
        new_xp -= xp_needed
        current_level += 1
        xp_needed = get_xp_needed(current_level)

    update_user_data(member.id, new_xp, current_level)

    embed = discord.Embed(
        title="✨ Berhasil Menambahkan XP!",
        description=f"Menambahkan **+{amount} XP** kepada {member.mention}.",
        color=0x2ECC71,
    )
    embed.add_field(
        name="Pembaruan Status",
        value=f"• **Level Terbaru:** {current_level}\n• **Jumlah XP:** {new_xp}/{xp_needed}",
        inline=False,
    )
    await ctx.send(embed=embed)


@bot.command(name="setlevel")
@commands.has_permissions(administrator=True)
async def set_level(ctx, member: discord.Member, new_level: int):
    update_user_data(member.id, 0, new_level)
    embed = discord.Embed(
        title="⚙️ Level Diperbarui Admin",
        description=f"Berhasil menyetel level {member.mention} langsung ke **Level {new_level}**.",
        color=0xE67E22,
    )
    await ctx.send(embed=embed)


# ==================== COMMANDS BANTUAN & UTILITY ====================


@bot.command(name="info", aliases=["help"])
async def show_info(ctx):
    embed = discord.Embed(
        title="📌 PUSAT INFORMASI & MENU PERINTAH",
        description="Gunakan awalan titik (`.`) untuk menjalankan setiap perintah di bawah ini:",
        color=0x3498DB,
    )

    embed.add_field(
        name="🎮 Sistem Leveling",
        value="`.rank` — Mengecek level dan progress XP kamu\n"
         "`.lb` / `.top` — Menampilkan top leaderboard server\n"
         "`.addxp @user [jumlah]` — Menambah XP (Admin)\n"
         "`.setlevel @user [level]` — Menyetel level (Admin)",
        inline=False,
    )

    embed.add_field(
        name="🛡️ Moderasi & Pengaturan",
        value="`.role @user [nama]` — Pasang atau buat role otomatis\n"
         "`.nick @user [nama]` — Mengubah nama panggilan member\n"
         "`.to @user [waktu] [alasan]` — Memberikan timeout/mute\n"
         "`.unto @user` — Mencabut status timeout\n"
         "`.warn @user [alasan]` — Memberikan teguran resmi\n"
         "`.clear [jumlah]` — Membersihkan riwayat chat\n"
         "`.kick` / `.ban` — Tindakan tegas member pelanggar",
        inline=False,
    )

    embed.add_field(
        name="🛍️ Informasi Toko & Profil",
        value="`.akun` / `.userinfo` — Melihat detail data akun Discord\n"
         "`.serverinfo` — Informasi lengkap tentang server\n"
         "`.price` — Daftar harga produk & layanan\n"
         "`.payment` — Metode pembayaran yang tersedia\n"
         "`.ping` — Menguji kecepatan respons bot",
        inline=False,
    )

    embed.set_footer(text="TONGSOP Assistant • All Rights Reserved")
    await ctx.send(embed=embed)


@bot.command(name="role")
@commands.has_permissions(manage_roles=True)
async def give_or_create_role(ctx, member: discord.Member, *, role_name: str):
    role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)

    if not role:
        try:
            role = await ctx.guild.create_role(
                name=role_name,
                reason=f"Dibuat otomatis oleh {ctx.author.name} via perintah .role"
            )
            await ctx.send(f"✨ Role **{role_name}** belum tersedia, sistem berhasil membuatkannya baru!")
        except Exception as e:
            await ctx.send(f"❌ Gagal membuat role baru: {e}")
            return

    try:
        if role in member.roles:
            await ctx.send(f"⚠️ {member.mention} sudah memiliki role **{role.name}**!")
        else:
            await member.add_roles(role)
            await ctx.send(f"✅ Berhasil memasang role **{role.name}** kepada {member.mention}!")
    except Exception as e:
        await ctx.send(f"❌ Gagal memasang role: {e}\n*(Pastikan posisi role bot berada di atas role yang ingin dipasang)*")


@bot.command(name="nick", aliases=["setnick"])
@commands.has_permissions(manage_nicknames=True)
async def change_nickname(ctx, member: discord.Member, *, new_nick: str = None):
    try:
        await member.edit(nick=new_nick)
        if new_nick:
            await ctx.send(f"✅ Berhasil mengubah nickname {member.mention} menjadi **{new_nick}**.")
        else:
            await ctx.send(f"✅ Berhasil mereset nickname {member.mention} kembali normal.")
    except Exception as e:
        await ctx.send(f"❌ Gagal mengubah nickname: {e}\n*(Pastikan posisi role bot berada di atas target)*")


@bot.command(name="to", aliases=["timeout"])
@commands.has_permissions(moderate_members=True)
async def timeout_member(
    ctx,
    member: discord.Member,
    duration_str: str = "10m",
    *,
    reason: str = "Tidak ada alasan spesifik.",
):
    duration = parse_duration(duration_str)
    if duration is None:
        await ctx.send("⚠️ Format waktu salah! Contoh penggunaan benar: `.to @user 10m` atau `.to @user 1h`")
        return
    try:
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(
            title="🤐 TIMEOUT EKSEKUSI",
            description=f"Member **{member.name}** telah dibungkam selama **{duration_str}**.",
            color=0xE67E22,
        )
        embed.add_field(name="Alasan", value=reason, inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan timeout: {e}")


@bot.command(name="unto", aliases=["untimeout"])
@commands.has_permissions(moderate_members=True)
async def untimeout_member(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"🔊 Status timeout untuk **{member.name}** telah resmi dicabut!")
    except Exception as e:
        await ctx.send(f"❌ Gagal mencabut timeout: {e}")


@bot.command(name="warn")
@commands.has_permissions(moderate_members=True)
async def warn_member(
    ctx, member: discord.Member, *, reason: str = "Pelanggaran aturan server."
):
    embed = discord.Embed(
        title="⚠️ PERINGATAN RESMI (WARN)",
        description=f"Peringatan keras ditujukan kepada {member.mention}",
        color=0xE74C3C,
    )
    embed.add_field(name="Keterangan / Alasan", value=reason, inline=False)
    embed.set_footer(text=f"Ditegur oleh {ctx.author.name}")
    await ctx.send(embed=embed)


@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan."
):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 **{member.name}** telah dikeluarkan secara permanen (Banned) dari server.")
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan ban: {e}")


@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan."
):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"👞 **{member.name}** telah dikeluarkan dari server (Kicked).")
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan kick: {e}")


@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 5):
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Berhasil membersihkan `{len(deleted)-1}` pesan chat.")
    await asyncio.sleep(2)
    await msg.delete()


@bot.command(name="ping")
async def check_ping(ctx):
    latency_ms = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 PONG - SYSTEM LATENCY",
        description=f"Kecepatan respon server bot saat ini: `{latency_ms}ms`",
        color=0x2ECC71,
    )
    await ctx.send(embed=embed)


@bot.command(name="userinfo", aliases=["whois", "akun"])
async def user_info(ctx, member: discord.Member = None):
    member = member or ctx.author
    
    roles = [role.mention for role in reversed(member.roles) if role.name != "@everyone"]
    created_at = member.created_at.strftime("%d %B %Y (%H:%M)")
    joined_at = member.joined_at.strftime("%d %B %Y (%H:%M)") if member.joined_at else "Tidak diketahui"

    embed = discord.Embed(
        title=f"👤 Informasi Detail Akun — {member.name}", 
        color=0x3498DB,
        timestamp=datetime.datetime.now()
    )
    
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    
    embed.add_field(name="🆔 User ID", value=f"`{member.id}`", inline=True)
    embed.add_field(name="📌 Nama Panggilan", value=f"{member.display_name}", inline=True)
    embed.add_field(name="🤖 Status Bot", value="Iya (Bot)" if member.bot else "Tidak (Member)", inline=True)
    
    embed.add_field(name="📅 Akun Dibuat", value=created_at, inline=False)
    embed.add_field(name="📥 Bergabung di Server", value=joined_at, inline=False)
    
    embed.add_field(
        name=f"🏷️ Total Role ({len(roles)})",
        value=", ".join(roles) if roles else "Tidak ada role khusus",
        inline=False
    )
    
    embed.set_footer(text=f"Diminta oleh {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed)


@bot.command(name="serverinfo")
async def server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 Informasi Server: {guild.name}", color=0x2ECC71)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="👑 Pemilik Server", value=guild.owner.mention if guild.owner else "N/A", inline=True)
    embed.add_field(name="👥 Total Member", value=f"`{guild.member_count}`", inline=True)
    embed.add_field(name="🏷️ Total Role", value=f"`{len(guild.roles)}`", inline=True)
    embed.set_footer(text=f"Server ID: {guild.id}")
    await ctx.send(embed=embed)


@bot.command(name="price", aliases=["pricelist", "harga"])
async def show_price(ctx):
    embed = discord.Embed(
        title="🛒 LIST HARGA & LAYANAN PRENSTORE",
        description="Silakan buka tiket untuk detail pemesanan, ketersediaan stok, dan promo menarik:",
        color=0x9B59B6,
    )
    embed.add_field(
        name="📱 Layanan Redfinger & Cloud Phone",
        value="• Jasa Split Redfinger Profesional\n• Sewa Cloud Phone / Akun VIP Terpercaya",
        inline=False,
    )
    embed.add_field(
        name="🎫 Cara Pemesanan",
        value=f"Langsung menuju ke channel <#{TICKET_CHANNEL_ID}> untuk membuat tiket transaksi.",
        inline=False,
    )
    embed.set_footer(text="TONGSOP Store • Best Price & Guaranteed")
    await ctx.send(embed=embed)


@bot.command(name="payment", aliases=["pembayaran"])
async def show_payment(ctx):
    embed = discord.Embed(
        title="💳 SALURAN PEMBAYARAN RESMI",
        description="Pilih metode pembayaran yang paling nyaman untuk Anda:",
        color=0xF1C40F,
    )
    embed.add_field(
        name="Daftar Pembayaran",
        value="• **E-Wallet:** DANA / OVO / GoPay / LinkAja\n• **QRIS:** All Payment (Scan Satu untuk Semua)\n• **Transfer Bank:** BCA / Mandiri / SeaBank",
        inline=False,
    )
    embed.set_footer(text="Pastikan transfer hanya ke rekening/akun resmi toko!")
    await ctx.send(embed=embed)


# ==================== ERROR HANDLING ====================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Maaf, kamu tidak memiliki hak akses (permissions) untuk menjalankan perintah ini!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Format atau argumen perintah kurang lengkap! Ketik `.info` untuk melihat panduan penggunaan.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        raise error


# ==================== RUN BOT ====================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ERROR: BOT_TOKEN belum disetel di Environment Variables Railway / sistem kamu!")
else:
    bot.run(TOKEN)
