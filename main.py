import asyncio
import datetime
import os
import random
import re
import sqlite3
import discord
from discord.ext import commands
import yt_dlp

# Config Bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Channel ID
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050

xp_cooldowns = {}

# Config YT-DLP & FFmpeg (Dilengkapi cookiefile untuk bypass blokir YouTube)
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'cookiefile': 'cookies.txt',  # Wajib ada file cookies.txt di folder yang sama
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)


# ==================== DATABASE ====================
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

            embed = discord.Embed(
                title="🔥 LEVEL UP!",
                description=f"GG {message.author.mention}! Level kamu naik jadi **Level {current_level}** 🥳",
                color=0x2ECC71,
            )
            try:
                await message.channel.send(embed=embed)
            except Exception:
                pass
        else:
            update_user_data(user_id, new_xp, current_level)

    # 2. Cek Perintah Prefix
    if message.content.startswith("."):
        await bot.process_commands(message)
        return

    # 3. Auto Response Tiket di General
    if message.channel.id == GENERAL_CHANNEL_ID:
        try:
            async for old_msg in message.channel.history(limit=15):
                if old_msg.author.id == bot.user.id and len(old_msg.embeds) > 0:
                    await old_msg.delete()
                    await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Gagal hapus pesan lama: {e}")

        embed = discord.Embed(
            title="🛒 PRENSTORE OFFICIAL TICKET",
            description="Halo! Mau order atau butuh bantuan? Langsung klik channel tiket di bawah biar aman ya!",
            color=0x3498DB,
        )

        embed.add_field(
            name="📦 Order Produk",
            value=f"👉 <#{TICKET_CHANNEL_ID}> (Pilih ` open-ticket `)",
            inline=False,
        )
        embed.add_field(
            name="⚡ Jasa Split Redfinger",
            value=f"👉 <#{TICKET_CHANNEL_ID}> (Pilih ` jasa split `)",
            inline=False,
        )
        embed.add_field(
            name="⚠️ Notice",
            value="• Jangan transaksi di luar tiket demi keamanan bersama!\n• Admin pasti respon secepatnya.",
            inline=False,
        )
        embed.set_footer(text="TONGSOP Store • Safety First")

        await message.channel.send(content=f"{message.author.mention}", embed=embed)
        return

    await bot.process_commands(message)


# ==================== COMMANDS MUSIK ====================


@bot.command(name="play", aliases=["p"])
async def play_music(ctx, *, search: str):
    """Memutar lagu dari YouTube (Judul / Link)"""
    if not ctx.author.voice:
        await ctx.send("⚠️ Masuk ke Voice Channel dulu bro!")
        return

    channel = ctx.author.voice.channel

    try:
        if ctx.voice_client is None:
            await channel.connect()
        elif ctx.voice_client.channel != channel:
            await ctx.voice_client.move_to(channel)
    except Exception as e:
        await ctx.send(f"❌ Gagal masuk Voice Channel: `{e}`")
        return

    msg = await ctx.send("🔍 Lagi nyari lagunya...")

    try:
        player = await YTDLSource.from_url(search, loop=bot.loop, stream=True)

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        ctx.voice_client.play(
            player, after=lambda e: print(f"Player error: {e}") if e else None
        )

        embed = discord.Embed(
            title="🎶 Sedang Memutar",
            description=f"**[{player.title}]({player.url})**",
            color=0x2ECC71,
        )
        embed.set_footer(text=f"Diputar oleh {ctx.author.display_name}")
        await msg.edit(content=None, embed=embed)

    except Exception as e:
        await msg.edit(content=f"❌ Gagal memutar lagu: `{e}`")


@bot.command(name="skip", aliases=["s"])
async def skip_music(ctx):
    """Melewati lagu yang sedang diputar"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Lagu dilewati!")
    else:
        await ctx.send("Gak ada lagu yang lagi diputar buat di-skip.")


@bot.command(name="pause")
async def pause_music(ctx):
    """Jeda lagu"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Lagu dijeda.")
    else:
        await ctx.send("Gak ada lagu yang lagi diputar.")


@bot.command(name="resume")
async def resume_music(ctx):
    """Lanjutin lagu"""
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Lagu dilanjutin lagi!")
    else:
        await ctx.send("Lagu lagi gak dijeda.")


@bot.command(name="stop")
async def stop_music(ctx):
    """Stop pemutaran lagu"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏹️ Musik dihentikan.")
    else:
        await ctx.send("Gak ada lagu yang lagi diputar.")


@bot.command(name="leave", aliases=["dc"])
async def leave_vc(ctx):
    """Keluar dari Voice Channel"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bot keluar dari Voice Channel.")
    else:
        await ctx.send("Bot lagi gak ada di Voice Channel mana pun.")


# ==================== COMMANDS LEVELING ====================


@bot.command(name="rank", aliases=["level"])
async def check_rank(ctx, member: discord.Member = None):
    target = member or ctx.author
    xp, level = get_user_data(target.id)
    xp_needed = get_xp_needed(level)

    percent = int((xp / xp_needed) * 100) if xp_needed > 0 else 0
    filled = int(10 * (xp / xp_needed)) if xp_needed > 0 else 0
    bar = "🟩" * filled + "⬛" * (10 - filled)

    embed = discord.Embed(
        title=f"📊 Status Level — {target.display_name}", color=0x3498DB
    )
    embed.set_thumbnail(
        url=target.avatar.url if target.avatar else target.default_avatar.url
    )

    embed.add_field(name="Level", value=f"**{level}**", inline=True)
    embed.add_field(name="XP", value=f"**{xp} / {xp_needed}**", inline=True)
    embed.add_field(name="Progress", value=f"{bar} **{percent}%**", inline=False)

    await ctx.send(embed=embed)


@bot.command(name="leaderboard", aliases=["lb", "top"])
async def show_leaderboard(ctx):
    top_users = get_top_users()

    embed = discord.Embed(
        title="🏆 TOP 5 MEMBER TERAKTIF",
        description="Daftar member paling rajin nimbrung di server:",
        color=0xF1C40F,
    )

    if not top_users:
        embed.description = "Belum ada data member."
    else:
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, (u_id, lvl, xp) in enumerate(top_users):
            user = bot.get_user(u_id)
            name = user.name if user else f"User ID: {u_id}"
            embed.add_field(
                name=f"{medals[i]} {name}",
                value=f"Level **{lvl}** • `{xp} XP`",
                inline=False,
            )

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
        title="✨ XP Ditambahkan!",
        description=f"Nambah **+{amount} XP** ke {member.mention}.",
        color=0x2ECC71,
    )
    embed.add_field(
        name="Status Sekarang",
        value=f"• **Level:** {current_level}\n• **XP:** {new_xp}/{xp_needed}",
        inline=False,
    )
    await ctx.send(embed=embed)


@bot.command(name="setlevel")
@commands.has_permissions(administrator=True)
async def set_level(ctx, member: discord.Member, new_level: int):
    update_user_data(member.id, 0, new_level)
    await ctx.send(
        f"✅ Level {member.mention} berhasil di-set ke **Level {new_level}**."
    )


# ==================== COMMANDS HELPER & UTILITY ====================


@bot.command(name="info", aliases=["help"])
async def show_info(ctx):
    embed = discord.Embed(
        title="📌 MENU PERINTAH BOT",
        description="Pake prefix titik (`.`) buat jalanin perintah ya:",
        color=0x3498DB,
    )

    embed.add_field(
        name="🎵 Musik",
        value="`.p [judul/link]` — Putar lagu\n"
        "`.skip` / `.s` — Lewati lagu\n"
        "`.pause` — Jeda lagu\n"
        "`.resume` — Lanjut lagu\n"
        "`.stop` — Stop musik\n"
        "`.leave` — Keluar Voice Channel",
        inline=False,
    )

    embed.add_field(
        name="🎮 Leveling",
        value="`.rank` — Cek level & XP kamu\n"
        "`.lb` — Top 5 member paling aktif\n"
        "`.addxp @user [xp]` — Tambah XP (Admin)\n"
        "`.setlevel @user [lvl]` — Set level (Admin)",
        inline=False,
    )

    embed.add_field(
        name="🛡️ Moderasi & Role",
        value="`.role @user [nama_role]` — Pasang/buat role otomatis\n"
        "`.to @user [waktu] [alasan]` — Mute/Timeout\n"
        "`.unto @user` — Unmute\n"
        "`.warn @user [alasan]` — Kasih teguran\n"
        "`.clear [jumlah]` — Hapus chat\n"
        "`.kick` / `.ban` — Out-kan member",
        inline=False,
    )

    embed.set_footer(text="TONGSOP Assistant")
    await ctx.send(embed=embed)


@bot.command(name="role")
@commands.has_permissions(manage_roles=True)
async def give_or_create_role(ctx, member: discord.Member, *, role_name: str):
    role = discord.utils.find(
        lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles
    )

    if not role:
        try:
            role = await ctx.guild.create_role(
                name=role_name,
                reason=f"Dibuat otomatis oleh {ctx.author.name} via .role",
            )
            await ctx.send(
                f"✨ Role **{role_name}** belum ada, otomatis dibuatin baru!"
            )
        except Exception as e:
            await ctx.send(f"❌ Gagal buat role: {e}")
            return

    try:
        if role in member.roles:
            await ctx.send(f"⚠️ {member.mention} udah punya role **{role.name}**!")
        else:
            await member.add_roles(role)
            await ctx.send(
                f"✅ Role **{role.name}** berhasil dipasang ke {member.mention}!"
            )
    except Exception as e:
        await ctx.send(
            f"❌ Gagal masang role: {e}\n*(Pastikan posisi role bot ada di atas role yang mau dipasang)*"
        )


@bot.command(name="to", aliases=["timeout"])
@commands.has_permissions(moderate_members=True)
async def timeout_member(
    ctx,
    member: discord.Member,
    duration_str: str = "10m",
    *,
    reason: str = "N/A",
):
    duration = parse_duration(duration_str)
    if duration is None:
        await ctx.send("⚠️ Format waktu salah! Contoh: `.to @user 10m`")
        return
    try:
        await member.timeout(duration, reason=reason)
        await ctx.send(
            f"🤐 **{member.name}** kena timeout selama **{duration_str}** | Alasan: {reason}"
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal: {e}")


@bot.command(name="unto", aliases=["untimeout"])
@commands.has_permissions(moderate_members=True)
async def untimeout_member(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"🔊 Timeout buat **{member.name}** udah dicabut!")
    except Exception as e:
        await ctx.send(f"❌ Gagal: {e}")


@bot.command(name="warn")
@commands.has_permissions(moderate_members=True)
async def warn_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan."
):
    embed = discord.Embed(
        title="⚠️ TEGURAN MODERASI",
        description=f"Peringatan buat {member.mention}",
        color=0xE67E22,
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
        await ctx.send(f"🔨 **{member.name}** berhasil di-ban.")
    except Exception as e:
        await ctx.send(f"❌ Gagal ban: {e}")


@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan."
):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"👞 **{member.name}** berhasil di-kick.")
    except Exception as e:
        await ctx.send(f"❌ Gagal kick: {e}")


@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 5):
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Berhasil hapus {len(deleted)-1} chat.")
    await asyncio.sleep(2)
    await msg.delete()


@bot.command(name="ping")
async def check_ping(ctx):
    await ctx.send(f"🏓 Pong! Speed bot: `{round(bot.latency * 1000)}ms`")


@bot.command(name="userinfo", aliases=["whois"])
async def user_info(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [role.mention for role in member.roles if role.name != "@everyone"]

    embed = discord.Embed(title=f"👤 Profile {member.name}", color=0x3498DB)
    embed.set_thumbnail(
        url=member.avatar.url if member.avatar else member.default_avatar.url
    )
    embed.add_field(name="User ID", value=f"`{member.id}`", inline=True)
    embed.add_field(
        name="Join Server",
        value=member.joined_at.strftime("%d-%m-%Y"),
        inline=True,
    )
    embed.add_field(
        name=f"Role ({len(roles)})",
        value=", ".join(roles) if roles else "Gak ada role",
        inline=False,
    )
    await ctx.send(embed=embed)


@bot.command(name="serverinfo")
async def server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 Info Server {guild.name}", color=0x2ECC71)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(
        name="Owner",
        value=guild.owner.mention if guild.owner else "N/A",
        inline=True,
    )
    embed.add_field(name="Total Member", value=f"`{guild.member_count}`", inline=True)
    embed.add_field(name="Total Role", value=f"`{len(guild.roles)}`", inline=True)
    await ctx.send(embed=embed)


@bot.command(name="price", aliases=["pricelist", "harga"])
async def show_price(ctx):
    embed = discord.Embed(
        title="🛒 LIST HARGA & LAYANAN PRENSTORE",
        description="Silakan buka tiket untuk detail order & info promo:",
        color=0x9B59B6,
    )
    embed.add_field(
        name="📱 Redfinger & Split",
        value="• Jasa Split Redfinger\n• Sewa Cloud Phone / VIP",
        inline=False,
    )
    embed.add_field(
        name="🎫 Order Sekarang",
        value=f"Langsung klik ke: <#{TICKET_CHANNEL_ID}>",
        inline=False,
    )
    embed.set_footer(text="TONGSOP Store")
    await ctx.send(embed=embed)


@bot.command(name="payment", aliases=["pembayaran"])
async def show_payment(ctx):
    embed = discord.Embed(
        title="💳 METODE PEMBAYARAN",
        description="Menerima pembayaran resmi via:",
        color=0xF1C40F,
    )
    embed.add_field(
        name="Pilihan Transfer",
        value="• DANA / OVO / GoPay\n• QRIS All Payment\n• Bank Transfer",
        inline=False,
    )
    await ctx.send(embed=embed)


# Error Handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu gak punya akses buat pake perintah ini!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Argumennya kurang tuh, cek `.info` deh.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        raise error


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("ERROR: BOT_TOKEN belum di-setting di Environment Variables Railway!")
else:
    bot.run(TOKEN)
