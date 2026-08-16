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

# Menggunakan prefix titik (.) sesuai permintaan agar tidak nabrak dengan bot lain
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Konfigurasi Channel ID (Sesuaikan dengan ID server Anda)
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CATEGORY_ID = 1517625110536786050  # ID Kategori untuk membuat private channel tiket

xp_cooldowns = {}


# ==================== DATABASE SETUP ====================
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
        cursor.execute("SELECT xp, level FROM users WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        if not data:
            cursor.execute(
                "INSERT INTO users (user_id, xp, level) VALUES (?, ?, ?)",
                (user_id, 0, 0),
            )
            conn.commit()
            data = (0, 0)
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


# ==================== INTERACTIVE VIEWS (UI BUTTONS) ====================


class TicketControlView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Tutup Tiket",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket_btn",
        emoji="🔒",
    )
    async def close_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "🔒 Tiket ini akan ditutup dalam 5 detik...", ephemeral=False
        )
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(
                reason=f"Ditutup oleh {interaction.user.name}"
            )
        except Exception:
            pass


class TicketSystemView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Order Produk",
        style=discord.ButtonStyle.primary,
        custom_id="order_product",
        emoji="📦",
    )
    async def order_product(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.create_ticket_channel(interaction, "order")

    @discord.ui.button(
        label="Jasa Split Redfinger",
        style=discord.ButtonStyle.success,
        custom_id="jasa_split",
        emoji="⚡",
    )
    async def jasa_split(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.create_ticket_channel(interaction, "split-redfinger")

    async def create_ticket_channel(
        self, interaction: discord.Interaction, ticket_type: str
    ):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)

        existing_channel = discord.utils.get(
            guild.text_channels,
            name=f"ticket-{ticket_type}-{interaction.user.name.lower()}",
        )
        if existing_channel:
            await interaction.response.send_message(
                f"⚠️ Kamu sudah memiliki tiket aktif di {existing_channel.mention}!",
                ephemeral=True,
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_channels=True
            ),
        }

        try:
            channel = await guild.create_text_channel(
                name=f"ticket-{ticket_type}-{interaction.user.name}",
                category=category if isinstance(category, discord.CategoryChannel) else None,
                overwrites=overwrites,
                reason=f"Tiket dibuat oleh {interaction.user}",
            )

            embed = discord.Embed(
                title=f"🎫 TIKET RESMI — {ticket_type.upper()}",
                description=f"Halo {interaction.user.mention}!\nSilakan sampaikan detail kebutuhan/pesanan Anda di sini. Staff kami akan segera merespon.",
                color=0x3498DB,
            )
            embed.set_footer(text="Tekan tombol di bawah untuk menutup tiket.")

            await channel.send(
                content=f"{interaction.user.mention} | @here",
                embed=embed,
                view=TicketControlView(),
            )
            await interaction.response.send_message(
                f"✅ Tiket berhasil dibuat! Silakan buka: {channel.mention}",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Gagal membuat tiket otomatis: {e}", ephemeral=True
            )


# ==================== EVENTS BOT ====================


@bot.event
async def on_ready():
    print(f"✨ Tongsop Assistant Berhasil Terhubung as {bot.user}!")
    print("🚀 Status: Siap melayani server menggunakan prefix titik (.)")


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

    # 2. Panel Tiket Interaktif Otomatis di Channel General
    if message.channel.id == GENERAL_CHANNEL_ID:
        try:
            async for old_msg in message.channel.history(limit=10):
                if old_msg.author.id == bot.user.id and len(old_msg.embeds) > 0:
                    await old_msg.delete()
                    await asyncio.sleep(0.3)
        except Exception:
            pass

        embed = discord.Embed(
            title="🛒 PRENSTORE OFFICIAL TICKET SYSTEM",
            description="Selamat datang! Silakan klik tombol di bawah ini untuk membuka tiket transaksi secara instan.",
            color=0x3498DB,
        )
        embed.add_field(
            name="📦 Layanan Tersedia",
            value="• Order Produk Toko\n• Jasa Split Redfinger Profesional",
            inline=False,
        )
        embed.set_footer(text="TONGSOP Store • Fast, Secure & Trusted")

        await message.channel.send(
            content=f"{message.author.mention}",
            embed=embed,
            view=TicketSystemView(),
        )
        return

    # 3. Eksekusi Command Berbasis Prefix (.)
    if message.content.startswith("."):
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
    embed.set_footer(
        text=f"Diminta oleh {ctx.author.name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
    )

    await ctx.send(embed=embed)


@bot.command(name="leaderboard", aliases=["lb", "top"])
async def show_leaderboard(ctx):
    top_users = get_top_users()
    if not top_users:
        await ctx.send("❌ Belum ada data peringkat member yang tercatat.")
        return

    embed = discord.Embed(color=0x2B2D31)
    if ctx.guild.icon:
        embed.set_author(
            name=f"{ctx.guild.name} server Leaderboard", icon_url=ctx.guild.icon.url
        )
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
        bar = "█" * progress + "░" * (12 - progress)

        description_text += f"{rank_icon} **{name}**\n└ `LVL {lvl}` • `{xp}/{xp_needed} XP`\n`{bar}`\n\n"

    embed.description = description_text
    embed.set_footer(text="Overall XP • Sistem Peringkat Resmi Tongsop")
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


# ==================== ERROR HANDLING ====================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ Maaf, kamu tidak memiliki hak akses (permissions) untuk menjalankan perintah ini!"
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "⚠️ Format atau argumen perintah kurang lengkap! Ketik `.info` untuk melihat panduan."
        )
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        raise error


# ==================== RUN BOT ====================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print(
        "❌ ERROR: BOT_TOKEN belum disetel di Environment Variables Railway / sistem kamu!"
    )
else:
    bot.run(TOKEN)
