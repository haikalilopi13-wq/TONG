import discord
from discord.ext import commands
import os
import random
import datetime

# ==================== CONFIG BOT ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Channel ID Target
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050

# Sistem Penyimpanan Level & XP di Memori (Aman dari Crash Railway / SQLite Error)
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
    print("🚀 Siap melayani server dengan fitur Leveling, Admin Tambah XP/Level, Untimeout, dan Moderasi Lengkap!")

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
        value="`.clear [jumlah]` — Menghapus pesan chat\n"
              "`.role @user [nama role]` — Memberikan/mencabut role\n"
              "`.ban @user [alasan]` — Memblokir member\n"
              "`.timeout @user [menit] [alasan]` — Membisukan member\n"
              "`.untimeout @user` — Membatalkan timeout/mute",
        inline=False
    )
    embed.add_field(
        name="📊 Level & XP (Admin & Member)",
        value="`.rank` — Cek level dan progress XP kamu\n"
              "`.addxp @user [jumlah]` — Menambah XP user (Admin)\n"
              "`.addlevel @user [jumlah]` — Menambah Level user (Admin)",
        inline=False
    )
    embed.add_field(
        name="🛠️ Utility & Informasi",
        value="`.ping` — Cek kecepatan respon bot\n"
              "`.say [pesan]` — Mengulang pesan\n"
              "`.server` — Info lengkap server\n"
              "`.whois [@user]` — Detail profil member\n"
              "`.avatar [@user]` — Foto profil member",
        inline=False
    )
    embed.add_field(
        name="🎮 Fun, Games & Hiburan",
        value="`.roll` — Acak angka 1-100\n"
              "`.coinflip` — Lempar koin\n"
              "`.rps [batu/kertas/gunting]` — Main Suit\n"
              "`.rate [sesuatu]` — Nilai sesuatu 0-100\n"
              "`.quote` — Kata-kata bijak",
        inline=False
    )
    embed.set_footer(text="TONGSOP Store • All Rights Reserved")
    await ctx.send(embed=embed)

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
@bot.command(name="addxp")
@commands.has_permissions(administrator=True)
async def add_xp(ctx, member: discord.Member, amount: int):
    data = get_user_xp(member.id)
    data["xp"] += amount
    await ctx.send(f"✨ Berhasil menambahkan **{amount} XP** kepada {member.mention}. Total XP sekarang: `{data['xp']}`")

@bot.command(name="addlevel")
@commands.has_permissions(administrator=True)
async def add_level(ctx, member: discord.Member, amount: int):
    data = get_user_xp(member.id)
    data["level"] += amount
    await ctx.send(f"🚀 Berhasil menambahkan **{amount} Level** kepada {member.mention}. Level sekarang: **Level {data['level']}**")

@add_xp.error
@add_level.error
async def level_admin_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu harus memiliki izin *Administrator* untuk menggunakan perintah ini!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Format salah! Contoh: `.addxp @User 50` atau `.addlevel @User 2`")

# --- MODERASI: CLEAR PESAN ---
@bot.command(name="clear", aliases=["purge", "cls"])
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 5):
    if amount < 1:
        await ctx.send("⚠️ Masukkan jumlah pesan minimal 1.")
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
            await ctx.send(f"⚠️ Role `{rolename}` tidak ditemukan, tetapi berhasil dibuat otomatis!")
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
            await ctx.send("❌ Bot gagal memberikan role. Pastikan posisi Role Bot di pengaturan server berada di atas role tersebut!")

@manage_role.error
async def role_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu tidak memiliki izin *Manage Roles*!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Format salah! Contoh: `.role @NamaMember VIP`")

# --- MODERASI: BAN MEMBER ---
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_member(ctx, member: discord.Member, *, reason: str = "Tidak ada alasan yang diberikan"):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 Berhasil membanned {member.mention}. Alasan: `{reason}`")
    except Exception as e:
        await ctx.send(f"❌ Gagal membanned member: {e}")

@ban_member.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu tidak memiliki izin *Ban Members*!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Format salah! Contoh: `.ban @User Melanggar peraturan`")

# --- MODERASI: TIMEOUT MEMBER ---
@bot.command(name="timeout", aliases=["mute"])
@commands.has_permissions(moderate_members=True)
async def timeout_member(ctx, member: discord.Member, minutes: int, *, reason: str = "Tidak ada alasan"):
    try:
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(f"🔇 Berhasil melakukan timeout ke {member.mention} selama **{minutes} menit**. Alasan: `{reason}`")
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan timeout: {e}")

@timeout_member.error
async def timeout_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu tidak memiliki izin *Moderate Members*!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Format salah! Contoh: `.timeout @User 10 Spam chat`")

# --- MODERASI: BATALKAN TIMEOUT (UNTIMEOUT / UNMUTE) ---
@bot.command(name="untimeout", aliases=["unmute"])
@commands.has_permissions(moderate_members=True)
async def untimeout_member(ctx, member: discord.Member, *, reason: str = "Selesai masa hukuman"):
    try:
        await member.timeout(None, reason=reason)
        await ctx.send(f"🔊 Berhasil membatalkan timeout (unmute) untuk {member.mention}. Alasan: `{reason}`")
    except Exception as e:
        await ctx.send(f"❌ Gagal membatalkan timeout member: {e}")

@untimeout_member.error
async def untimeout_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu tidak memiliki izin *Moderate Members*!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Format salah! Contoh: `.untimeout @User`")

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

@bot.command(name="whois", aliases=["userinfo"])
async def whois_member(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 User Info — {member.name}", color=0x3498DB)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
    embed.add_field(name="Nama Panggilan", value=member.display_name, inline=True)
    embed.add_field(name="Bergabung Sejak", value=member.joined_at.strftime("%d %b %Y") if member.joined_at else "-", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="avatar", aliases=["pp"])
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

@bot.command(name="quote")
async def random_quote(ctx):
    quotes = [
        "“Kesuksesan besar dimulai dari langkah kecil yang konsisten.”",
        "“Jangan menunggu waktu yang tepat, karena waktu yang tepat adalah sekarang.”",
        "“Tetap semangat, hasil tidak akan mengkhianati usaha!”",
        "“Kegagalan adalah sukses yang tertunda, teruslah mencoba.”"
    ]
    await ctx.send(f"💬 *{random.choice(quotes)}*")

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
