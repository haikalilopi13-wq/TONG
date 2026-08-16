import asyncio
import datetime
import os
import random
import re
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# ==================== CONFIG BOT ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)

# Channel ID Target (Sesuaikan dengan server Anda)
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050
LOG_CHANNEL_ID = 0  # Ganti dengan ID channel log jika ada, 0 untuk disable

xp_cooldowns = {}


# ==================== DATABASE SETUP (ADVANCED) ====================
def init_db():
    with sqlite3.connect("levels.db") as conn:
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


init_db()


def get_user_data(user_id):
    with sqlite3.connect("levels.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT xp, level FROM users WHERE user_id = ?", (user_id,)
        )
        data = cursor.fetchone()
        if not data:
            cursor.execute(
                "INSERT INTO users (user_id, xp, level) VALUES (?, ?, ?)",
                (user_id, 0, 0),
            )
            conn.commit()
            return (0, 0)
        return data


def update_user_data(user_id, xp, level):
    with sqlite3.connect("levels.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET xp = ?, level = ? WHERE user_id = ?",
            (xp, level, user_id),
        )
        conn.commit()


def get_top_users():
    with sqlite3.connect("levels.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, level, xp FROM users ORDER BY level DESC, xp DESC LIMIT 5"
        )
        return cursor.fetchall()


def get_xp_needed(level):
    return (level + 1) * 150  # Ditingkatkan sedikit agar lebih menantang


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


# ==================== INTERACTIVE UI VIEWS ====================
class TicketControlView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📦 Order Produk",
        style=discord.ButtonStyle.primary,
        custom_id="ticket_order",
    ):
        async def order_callback(
            interaction: discord.Interaction, button: discord.ui.Button
        ):
            await interaction.response.send_message(
                f"✨ Halo {interaction.user.mention}! Silakan buat tiket pesanan produk di <#{TICKET_CHANNEL_ID}>.",
                ephemeral=True,
            )

    @discord.ui.button(
        label="⚡ Jasa Split Redfinger",
        style=discord.ButtonStyle.success,
        custom_id="ticket_split",
    ):
        async def split_callback(
            interaction: discord.Interaction, button: discord.ui.Button
        ):
            await interaction.response.send_message(
                f"🚀 Halo {interaction.user.mention}! Untuk layanan Split Redfinger, silakan akses panel <#{TICKET_CHANNEL_ID}>.",
                ephemeral=True,
            )


# ==================== EVENTS BOT ====================
@bot.event
async def on_ready():
    print(f"✨ Tongsop AI Assistant Berhasil Terhubung as {bot.user}!")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Berhasil menyinkronkan {len(synced)} Slash Commands.")
    except Exception as e:
        print(f"❌ Gagal sinkronisasi slash commands: {e}")
    print("🚀 Status: Sistem canggih aktif sepenuhnya.")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Sistem Leveling & XP Otomatis (Cooldown 45 Detik)
    now = datetime.datetime.now().timestamp()
    user_id = message.author.id

    if user_id not in xp_cooldowns or now - xp_cooldowns[user_id] > 45:
        xp_cooldowns[user_id] = now
        current_xp, current_level = get_user_data(user_id)

        gained_xp = random.randint(20, 35)
        new_xp = current_xp + gained_xp
        xp_needed = get_xp_needed(current_level)

        if new_xp >= xp_needed:
            current_level += 1
            new_xp = new_xp - xp_needed
            update_user_data(user_id, new_xp, current_level)

            embed = discord.Embed(
                title="🎉 LEVEL UP EXCELLENT!",
                description=f"Luar biasa {message.author.mention}! Keaktifanmu membawamu naik ke **Level {current_level}** 🚀",
                color=0x2ECC71,
                timestamp=datetime.datetime.now(),
            )
            embed.set_thumbnail(
                url=message.author.avatar.url
                if message.author.avatar
                else message.author.default_avatar.url
            )
            try:
                await message.channel.send(embed=embed)
            except Exception:
                pass
        else:
            update_user_data(user_id, new_xp, current_level)

    # 2. Command Prefix (. .)
    if message.content.startswith("."):
        await bot.process_commands(message)
        return

    # 3. Auto Response Tiket Premium dengan Tombol Interaktif
    if message.channel.id == GENERAL_CHANNEL_ID:
        try:
            async for old_msg in message.channel.history(limit=15):
                if old_msg.author.id == bot.user.id and len(old_msg.embeds) > 0:
                    await old_msg.delete()
                    await asyncio.sleep(0.3)
        except Exception as e:
            print(f"Gagal membersihkan pesan lama: {e}")

        embed = discord.Embed(
            title="🛒 PRENSTORE OFFICIAL SECURE TICKET SYSTEM",
            description="Selamat datang! Butuh bantuan cepat atau ingin melakukan pemesanan produk & jasa? Silakan gunakan tombol interaktif di bawah.",
            color=0x3498DB,
            timestamp=datetime.datetime.now(),
        )
        embed.add_field(
            name="🛡️ Peraturan Transaksi",
            value="• **Dilarang keras** bertransaksi di luar sistem tiket resmi.\n• Staff kami siap melayani dengan cepat dan aman.",
            inline=False,
        )
        embed.set_footer(text="TONGSOP Store • AI Powered & Trusted Service")

        await message.channel.send(
            content=f"{message.author.mention}",
            embed=embed,
            view=TicketControlView(),
        )
        return

    await bot.process_commands(message)


# ==================== COMMANDS LEVELING & LEADERBOARD ====================
@bot.hybrid_command(name="rank", description="Melihat level dan progress XP Anda")
@app_commands.describe(member="Member yang ingin dicek (Opsional)")
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
    embed.add_field(
        name="📈 Progress Level", value=f"{bar} **{percent}%**", inline=False
    )
    embed.set_footer(
        text=f"Diminta oleh {ctx.author.name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
    )

    await ctx.send(embed=embed)


@bot.hybrid_command(
    name="leaderboard", description="Menampilkan top 5 peringkat server"
)
async def show_leaderboard(ctx):
    top_users = get_top_users()
    if not top_users:
        await ctx.send("❌ Belum ada data peringkat member yang tercatat.")
        return

    embed = discord.Embed(
        title=f"🏆 Server Leaderboard — {ctx.guild.name}", color=0x2B2D31
    )
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)

    description_text = ""
    medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]

    for i, (u_id, lvl, xp) in enumerate(top_users):
        user = bot.get_user(u_id) or await bot.fetch_user(u_id)
        name = user.name if user else f"User_{u_id}"
        rank_icon = medals[i] if i < len(medals) else "🔹"

        xp_needed = get_xp_needed(lvl)
        progress = int((xp / xp_needed) * 10) if xp_needed > 0 else 0
        bar = "█" * progress + "░" * (10 - progress)

        description_text += f"{rank_icon} **{name}**\n"
        description_text += f"└ `LVL {lvl}` • `{xp}/{xp_needed} XP` | `{bar}`\n\n"

    embed.description = description_text
    embed.set_footer(text="Sistem Peringkat Otomatis Tongsop Assistant")
    await ctx.send(embed=embed)


@bot.command(name="ping")
async def check_ping(ctx):
    latency_ms = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 PONG - SYSTEM LATENCY",
        description=f"Kecepatan respon server bot saat ini: `{latency_ms}ms`",
        color=0x2ECC71,
    )
    await ctx.send(embed=embed)


# ==================== UTILITY & SHOP COMMANDS ====================
@bot.command(name="info", aliases=["help"])
async def show_info(ctx):
    embed = discord.Embed(
        title="📌 PUSAT INFORMASI & MENU PERINTAH CANGGIH",
        description="Gunakan awalan titik (`.`) atau Slash Command (`/`) untuk menjalankan perintah:",
        color=0x3498DB,
    )
    embed.add_field(
        name="🎮 Sistem Leveling & Statistik",
        value="`.rank` — Cek level & XP\n`.leaderboard` — Lihat top rank\n`.ping` — Cek latensi bot",
        inline=False,
    )
    embed.add_field(
        name="🛡️ Moderasi & Admin",
        value="`.role` | `.nick` | `.to` (Timeout) | `.warn` | `.clear` | `.ban` | `.kick`",
        inline=False,
    )
    embed.add_field(
        name="🛍️ Informasi Toko",
        value="`.akun` — Info akun Discord\n`.serverinfo` — Info server\n`.price` — List harga\n`.payment` — Metode pembayaran",
        inline=False,
    )
    embed.set_footer(text="Tongsop Assistant • Next-Gen Discord Bot")
    await ctx.send(embed=embed)


@bot.command(name="price", aliases=["pricelist", "harga"])
async def show_price(ctx):
    embed = discord.Embed(
        title="🛒 LIST HARGA & LAYANAN PRENSTORE",
        description="Pilihan layanan terbaik dan bergaransi:",
        color=0x9B59B6,
    )
    embed.add_field(
        name="📱 Layanan Redfinger & Cloud Phone",
        value="• Jasa Split Redfinger Profesional\n• Sewa Cloud Phone / Akun VIP Terpercaya",
        inline=False,
    )
    embed.add_field(
        name="🎫 Cara Pemesanan",
        value=f"Kunjungi <#{TICKET_CHANNEL_ID}> untuk membuat tiket transaksi instan.",
        inline=False,
    )
    embed.set_footer(text="TONGSOP Store • Best Price & Guaranteed")
    await ctx.send(embed=embed)


@bot.command(name="payment", aliases=["pembayaran"])
async def show_payment(ctx):
    embed = discord.Embed(
        title="💳 SALURAN PEMBAYARAN RESMI",
        description="Pilih metode pembayaran aman berikut:",
        color=0xF1C40F,
    )
    embed.add_field(
        name="Daftar Pembayaran",
        value="• **E-Wallet:** DANA / OVO / GoPay / LinkAja\n• **QRIS:** All Payment (Scan Satu untuk Semua)\n• **Transfer Bank:** BCA / Mandiri / SeaBank",
        inline=False,
    )
    embed.set_footer(text="Pastikan transfer hanya ke rekening/akun resmi toko!")
    await ctx.send(embed=embed)


# ==================== MODERATION COMMANDS ====================
@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 5):
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(
        f"🧹 Berhasil membersihkan `{len(deleted)-1}` pesan chat."
    )
    await asyncio.sleep(2)
    await msg.delete()


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
        await ctx.send(
            "⚠️ Format waktu salah! Contoh: `.to @user 10m` atau `.to @user 1h`"
        )
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


@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_member(
    ctx, member: discord.Member, *, reason: str = "Tidak ada alasan."
):
    try:
        await member.ban(reason=reason)
        await ctx.send(
            f"🔨 **{member.name}** telah dibanned permanen dari server."
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan ban: {e}")


# ==================== ERROR HANDLING ====================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ Maaf, kamu tidak memiliki hak akses untuk menjalankan perintah ini!"
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "⚠️ Argumen kurang lengkap! Ketik `.info` untuk panduan."
        )
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        raise error


# ==================== RUN BOT ====================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print(
        "❌ ERROR: BOT_TOKEN belum disetel di Environment Variables Railway/Sistem!"
    )
else:
    bot.run(TOKEN)
