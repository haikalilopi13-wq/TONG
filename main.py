import discord
from discord.ext import commands
import os
import random
import datetime
import asyncio
import aiohttp

# ==================== CONFIG BOT ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Channel ID Target
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050

# Sistem Penyimpanan Level & XP di Memori
user_data = {}
xp_cooldowns = {}

def get_user_xp(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"xp": 0, "level": 0}
    return user_data[user_id]

# ==================== EVENTS BOT ====================
@bot.event
async def on_ready():
    print(f"✨ Bot Berhasil Terhubung as {bot.user}!")
    print("🚀 Bot siap dengan Leaderboard Webhook Avatar Asli (Style Gambar), .pp, Leveling, & Moderasi Lengkap!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. Sistem Level & XP Otomatis (Cooldown 60 Detik per User)
    now = datetime.datetime.now().timestamp()
    user_id = message.author.id

    if user_id not in xp_cooldowns or (now - xp_cooldowns[user_id]) > 60:
        xp_cooldowns[user_id] = now
        data = get_user_xp(user_id)
        
        gained_xp = random.randint(15, 25)
        data["xp"] += gained_xp
        
        xp_needed = (data["level"] + 1) * 100

        if data["xp"] >= xp_needed:
            data["level"] += 1
            data["xp"] = data["xp"] - xp_needed

            embed = discord.Embed(
                title="🎉 LEVEL UP EXCELLENT!",
                description=f"Hebat {message.author.mention}! Keaktifanmu membawamu naik ke **Level {data['level']}** 🚀",
                color=0x2ECC71
            )
            try:
                await message.channel.send(embed=embed)
            except Exception:
                pass

    # 2. Auto Response Tiket di Channel General
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

# ==================== KUMPULAN PERINTAH ====================

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
        name="🛡️ Moderasi & Admin",
        value="`.clear` / `.cls` — Menghapus pesan\n"
              "`.role @user [nama role]` — Memberikan/mencabut role\n"
              "`.ban @user [alasan]` — Memblokir member\n"
              "`.timeout` / `.mute` — Membisukan member\n"
              "`.untimeout` / `.unmute` — Batalkan timeout/mute",
        inline=False
    )
    embed.add_field(
        name="📊 Level & XP (Admin & Member)",
        value="`.rank` / `.lvl` — Cek kartu profil & XP kamu\n"
              "`.top` / `.lb` — Cek Top 10 Leaderboard dengan Avatar Asli\n"
              "`.addxp` / `.axp` — Menambah XP user (Admin)\n"
              "`.addlevel` / `.alvl` — Menambah Level user (Admin)",
        inline=False
    )
    embed.add_field(
        name="🛠️ Utility & Informasi",
        value="`.server` — Info lengkap server\n"
              "`.whois` / `.ui` — Detail profil & role member\n"
              "`.avatar` / `.pp` — Cek foto profil & role user",
        inline=False
    )
    embed.add_field(
        name="🎮 Fun, Games & Hiburan",
        value="`.roll` — Dadu | `.coinflip` — Koin | `.rps` — Suit | `.rate` — Nilai",
        inline=False
    )
    embed.set_footer(text="TONGSOP Store • All Rights Reserved")
    await ctx.send(embed=embed)

# --- LEADERBOARD TOP 10 DENGAN AVATAR WEBHOOK (MENYERUPAI GAMBAR) ---
@bot.command(name="leaderboard", aliases=["lb", "top", "levels"])
async def show_leaderboard(ctx):
    if not user_data:
        await ctx.send("❌ Belum ada data level di server ini. Yuk mulai aktif chat!")
        return

    # Urutkan berdasarkan level (tertinggi), lalu XP (tertinggi)
    sorted_users = sorted(user_data.items(), key=lambda item: (item[1]['level'], item[1]['xp']), reverse=True)

    # Kirim judul leaderboard utama
    await ctx.send("🏆 **LEADERBOARD TOP SERVER**")

    # Cari atau buat webhook di channel ini untuk menampilkan avatar tiap user
    try:
        webhooks = await ctx.channel.webhooks()
        webhook = discord.utils.get(webhooks, name="TongsopLeaderboard")
        if not webhook:
            webhook = await ctx.channel.create_webhook(name="TongsopLeaderboard")
    except Exception:
        await ctx.send("⚠️ Bot memerlukan izin **Manage Webhooks** di channel ini untuk menampilkan foto profil.")
        return

    # Ambil hingga Top 10 member teratas
    for i, (user_id, data) in enumerate(sorted_users[:10]):
        member = ctx.guild.get_member(user_id)
        if not member:
            try:
                member = await bot.fetch_user(user_id)
            except Exception:
                member = None

        name = member.name if member else f"User {user_id}"
        display_name = member.display_name if hasattr(member, 'display_name') else name
        avatar_url = member.avatar.url if member and member.avatar else (member.default_avatar.url if member else bot.user.avatar.url)

        # Simbol peringkat
        if i == 0:
            rank_num = "🥇 #1"
        elif i == 1:
            rank_num = "🥈 #2"
        elif i == 2:
            rank_num = "🥉 #3"
        else:
            rank_num = f"#{i+1}"

        # Isi teks pesan per baris
        content_line = f"**{rank_num}** • `@{display_name}` • LVL: `+{data['level']}` XP: `+{data['xp']}`"

        try:
            await webhook.send(
                content=content_line,
                username=display_name,
                avatar_url=avatar_url,
                wait=True
            )
        except Exception:
            pass
        
        # Jeda singkat agar pengiriman webhook berurutan dengan rapi
        await asyncio.sleep(0.3)

# --- LEVEL & XP COMMAND ---
@bot.command(name="rank", aliases=["lvl", "level"])
async def check_rank(ctx, member: discord.Member = None):
    target = member or ctx.author
    data = get_user_xp(target.id)
    xp_needed = (data["level"] + 1) * 100

    embed = discord.Embed(title=f"📊 Status Kartu Profil — {target.display_name}", color=0x3498DB)
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.add_field(name="✨ Level", value=f"**{data['level']}**", inline=True)
    embed.add_field(name="⚡ XP Saat Ini", value=f"**{data['xp']} / {xp_needed}**", inline=True)
    await ctx.send(embed=embed)

# --- ADMIN: MENAMBAH XP & LEVEL ---
@bot.command(name="addxp", aliases=["axp"])
@commands.has_permissions(administrator=True)
async def add_xp(ctx, member: discord.Member, amount: int):
    data = get_user_xp(member.id)
    data["xp"] += amount
    await ctx.send(f"✨ Berhasil menambahkan **{amount} XP** kepada {member.mention}. Total XP sekarang: `{data['xp']}`")

@bot.command(name="addlevel", aliases=["alvl"])
@commands.has_permissions(administrator=True)
async def add_level(ctx, member: discord.Member, amount: int):
    data = get_user_xp(member.id)
    data["level"] += amount
    await ctx.send(f"🚀 Berhasil menambahkan **{amount} Level** kepada {member.mention}. Level sekarang: **Level {data['level']}**")

@add_xp.error
@add_level.error
async def level_admin_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu harus memiliki izin *Administrator*!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Format salah! Contoh: `.axp @User 50` atau `.alvl @User 2`")

# --- MODERASI: CLEAR PESAN ---
@bot.command(name="clear", aliases=["purge", "cls"])
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 5):
    if amount < 1:
        await ctx.send("⚠️ Minimal 1 pesan.")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Berhasil menghapus **{len(deleted) - 1}** pesan.")
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass

@clear_messages.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu tidak memiliki izin *Manage Messages*!")

# --- MODERASI: MANAJEMEN ROLE ---
@bot.command(name="role", aliases=["giverole"])
@commands.has_permissions(manage_roles=True)
async def manage_role(ctx, member: discord.Member, *, rolename: str):
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=rolename)
    if not role:
        try:
            role = await guild.create_role(name=rolename)
            await ctx.send(f"⚠️ Role `{rolename}` dibuat otomatis!")
        except Exception as e:
            await ctx.send(f"❌ Gagal membuat role: {e}")
            return

    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"✅ Berhasil **mencabut** role `{role.name}` dari {member.mention}.")
    else:
        try:
            await member.add_roles(role)
            await ctx.send(f"✅ Berhasil **memberikan** role `{role.name}` kepada {member.mention}!")
        except Exception:
            await ctx.send("❌ Gagal memberikan role. Cek posisi role bot di pengaturan server!")

@manage_role.error
async def role_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu tidak memiliki izin *Manage Roles*!")

# --- MODERASI: BAN ---
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_member(ctx, member: discord.Member, *, reason: str = "Tidak ada alasan"):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 Berhasil membanned {member.mention}. Alasan: `{reason}`")
    except Exception as e:
        await ctx.send(f"❌ Gagal ban member: {e}")

@ban_member.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu tidak memiliki izin *Ban Members*!")

# --- MODERASI: TIMEOUT ---
@bot.command(name="timeout", aliases=["mute"])
@commands.has_permissions(moderate_members=True)
async def timeout_member(ctx, member: discord.Member, minutes: int, *, reason: str = "Tidak ada alasan"):
    try:
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(f"🔇 Berhasil timeout {member.mention} selama **{minutes} menit**. Alasan: `{reason}`")
    except Exception as e:
        await ctx.send(f"❌ Gagal timeout: {e}")

@timeout_member.error
async def timeout_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu tidak memiliki izin *Moderate Members*!")

# --- MODERASI: UNTIMEOUT / UNMUTE ---
@bot.command(name="untimeout", aliases=["unmute", "unt"])
@commands.has_permissions(moderate_members=True)
async def untimeout_member(ctx, member: discord.Member, *, reason: str = "Selesai masa hukuman"):
    try:
        await member.timeout(None, reason=reason)
        await ctx.send(f"🔊 Berhasil membatalkan timeout untuk {member.mention}. Alasan: `{reason}`")
    except Exception as e:
        await ctx.send(f"❌ Gagal membatalkan timeout: {e}")

@untimeout_member.error
async def untimeout_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu tidak memiliki izin *Moderate Members*!")

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

@bot.command(name="whois", aliases=["userinfo", "ui"])
async def whois_member(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 User Info — {member.name}", color=0x3498DB)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
    embed.add_field(name="Nama Panggilan", value=member.display_name, inline=True)
    embed.add_field(name="Bergabung Sejak", value=member.joined_at.strftime("%d %b %Y") if member.joined_at else "-", inline=False)
    await ctx.send(embed=embed)

# --- PERINTAH CEK FOTO PROFIL & AVATAR (.pp / .avatar) ---
@bot.command(name="avatar", aliases=["pp"])
async def show_avatar(ctx, member: discord.Member = None):
    target = member or ctx.author
    roles = [role.mention for role in target.roles if role != ctx.guild.default_role]
    role_list = ", ".join(roles) if roles else "Tidak ada role"
    if len(role_list) > 1024:
        role_list = "Terlalu banyak role untuk ditampilkan"

    embed = discord.Embed(title=f"🖼️ Profil & Avatar — {target.name}", color=0x9B59B6)
    embed.set_image(url=target.avatar.url if target.avatar else target.default_avatar.url)
    embed.add_field(name="🆔 User ID", value=f"`{target.id}`", inline=True)
    embed.add_field(name="🏷️ Nama Panggilan", value=target.display_name, inline=True)
    embed.add_field(name="📅 Bergabung Server", value=target.joined_at.strftime("%d %b %Y") if target.joined_at else "-", inline=False)
    embed.add_field(name=f"🛡️ Role ({len(roles)})", value=role_list, inline=False)
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

# ==================== RUN BOT ====================
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token bot tidak ditemukan!")
