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

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Konfigurasi Channel ID (Sesuaikan dengan ID server Anda)
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CATEGORY_ID = (
    1517625110536786050  # ID Kategori untuk membuat private channel tiket
)
LOG_CHANNEL_ID = 1518084729122062489  # ID Channel untuk log moderasi (opsional)

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


# ==================== INTERACTIVE VIEWS (UI COMPONENTS) ====================


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

        # Cek apakah user sudah punya tiket terbuka di kategori yang sama
        existing_channel = discord.utils.get(
            guild.text_channels, name=f"ticket-{ticket_type}-{interaction.user.name.lower()}"
        )
        if existing_channel:
            await interaction.response.send_message(
                f"⚠️ Kamu sudah memiliki tiket aktif di {existing_channel.mention}!",
                ephemeral=True,
            )
            return

        # Atur permission agar hanya user ybs dan admin yang bisa melihat channel privat ini
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
    # Sinkronisasi Slash Commands secara otomatis ke Discord
    try:
        synced = await bot.tree.sync()
        print(f"✨ Berhasil menyinkronkan {len(synced)} Slash Commands (/urs).")
    except Exception as e:
        print(f"Gagal sinkronisasi command: {e}")

    print(f"🚀 Tongsop Assistant (Advanced Edition) aktif sebagai {bot.user}!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Sistem Leveling & XP Otomatis (Cooldown 60 Detik)
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

    # Auto Response Panel Tiket interaktif dengan tombol di General Channel
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

    await bot.process_commands(message)


# ==================== SLASH COMMANDS (MODERN /) ====================


@bot.tree.command(
    name="rank", description="Mengecek kartu profil level dan progress XP Anda"
)
@app_commands.describe(member="Member yang ingin dicek (opsional)")
async def slash_rank(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
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
        text=f"Diminta oleh {interaction.user.name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None,
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="leaderboard", description="Menampilkan top 5 member paling aktif"
)
async def slash_leaderboard(interaction: discord.Interaction):
    top_users = get_top_users()
    if not top_users:
        await interaction.response.send_message(
            "❌ Belum ada data peringkat member.", ephemeral=True
        )
        return

    embed = discord.Embed(color=0x2B2D31)
    embed.set_author(name=f"{interaction.guild.name} Server Leaderboard")

    description_text = ""
    medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]

    for i, (u_id, lvl, xp) in enumerate(top_users):
        user = bot.get_user(u_id) or await bot.fetch_user(u_id)
        name = user.name if user else f"User_{u_id}"
        rank_icon = medals[i] if i < len(medals) else "🔹"
        xp_needed = get_xp_needed(lvl)
        progress = int((xp / xp_needed) * 12) if xp_needed > 0 else 0
        bar = "█" * progress + "░" * (12 - progress)

        description_text += f"{rank_icon} **{name}**\n└ `LVL {lvl}` • `{xp}/{xp_needed} XP`\n`{bar}`\n\n"

    embed.description = description_text
    embed.set_footer(text="Sistem Peringkat Resmi Tongsop")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ping", description="Menguji kecepatan respon bot")
async def slash_ping(interaction: discord.Interaction):
    latency_ms = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 PONG!",
        description=f"Latensi server bot saat ini: `{latency_ms}ms`",
        color=0x2ECC71,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== RUN BOT ====================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print(
        "❌ ERROR: BOT_TOKEN belum disetel di Environment Variables Railway / sistem kamu!"
    )
else:
    bot.run(TOKEN)
