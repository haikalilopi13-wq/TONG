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

# Channel ID Target (Ganti dengan ID channel server Anda)
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050
TESTIMONI_CHANNEL_ID = 000000000000000000  # <--- Ganti dengan ID Channel Testimoni Anda

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
    print("🚀 Bot siap dengan Sistem Form Modal, Testimoni, Tiket, & Leveling!")

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

    # 2. Auto Response Panel Order / Tiket di Channel General
    if message.channel.id == GENERAL_CHANNEL_ID:
        try:
            async for old_msg in message.channel.history(limit=15):
                if old_msg.author.id == bot.user.id and len(old_msg.embeds) > 0:
                    await old_msg.delete()
        except Exception:
            pass

        embed = discord.Embed(
            title="🛒 PRENSTORE OFFICIAL TICKET SYSTEM",
            description="Selamat datang! Ingin melakukan pemesanan produk? Silakan klik tombol di bawah untuk mengisi formulir pesanan.",
            color=0x3498DB,
        )
        embed.set_footer(text="TONGSOP Store • Secure & Trusted Service")

        await message.channel.send(content=f"{message.author.mention}", embed=embed, view=BuyButtonView())
        return

    await bot.process_commands(message)

# ==================== SISTEM FORM MODAL (BUY FORM) ====================
class BuyModal(discord.ui.Modal, title="BUY"):
    mau_beli = discord.ui.TextInput(
        label="Mau beli apa?",
        placeholder="Make a selection",
        style=discord.TextStyle.short,
        required=True
    )
    
    jumlah = discord.ui.TextInput(
        label="Jumlah",
        placeholder="semisal mau beli campur pakai koma contoh 10,10",
        style=discord.TextStyle.short,
        required=True
    )
    
    username_roblox = discord.ui.TextInput(
        label="User Name Roblox",
        placeholder="Masukkan username Roblox Anda",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        produk = self.mau_beli.value
        jml = self.jumlah.value
        roblox_name = self.username_roblox.value

        await interaction.response.send_message(
            f"✅ Formulir pesanan berhasil dikirim!\n"
            f"• **Mau beli:** {produk}\n"
            f"• **Jumlah:** {jml}\n"
            f"• **Roblox Name:** {roblox_name}",
            ephemeral=True
        )

class BuyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛒 Buka Form Pembelian", style=discord.ButtonStyle.green, custom_id="open_buy_modal_persistent")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BuyModal())

# ==================== SISTEM INTERAKTIF RATING & TESTIMONI ====================
class RatingView(discord.ui.View):
    def __init__(self, ticket_opener: discord.Member):
        super().__init__(timeout=60)
        self.ticket_opener = ticket_opener

    async def send_testimoni(self, interaction: discord.Interaction, rating_text: str, color_code: int):
        guild = interaction.guild
        testi_channel = guild.get_channel(TESTIMONI_CHANNEL_ID)

        testi_embed = discord.Embed(
            title="⭐ TESTIMONI & RATING PELANGGAN",
            description=f"Terima kasih atas kepercayaan Anda kepada **TONGSOP Store**!",
            color=color_code
        )
        testi_embed.add_field(name="👤 Pembeli / Klien", value=self.ticket_opener.mention, inline=True)
        testi_embed.add_field(name="🏆 Penilaian", value=rating_text, inline=True)
        testi_embed.add_field(name="🛠️ Ditutup Oleh", value=interaction.user.mention, inline=False)
        testi_embed.set_footer(text=f"TONGSOP Store • {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")

        if testi_channel:
            try:
                await testi_channel.send(embed=testi_embed)
            except Exception:
                pass

        await interaction.response.send_message("✨ Terima kasih atas ratingnya! Testimoni telah dikirim ke channel testi. Channel akan ditutup dalam 5 detik...", ephemeral=True)
        await self.disable_all_and_close(interaction.channel)

    @discord.ui.button(label="⭐ 5 (Sangat Puas)", style=discord.ButtonStyle.green)
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_testimoni(interaction, "⭐⭐⭐⭐⭐ (Sangat Puas)", 0x2ECC71)

    @discord.ui.button(label="⭐ 3 (Cukup)", style=discord.ButtonStyle.blurple)
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_testimoni(interaction, "⭐⭐⭐ (Cukup)", 0x3498DB)

    @discord.ui.button(label="⭐ 1 (Kurang)", style=discord.ButtonStyle.red)
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_testimoni(interaction, "⭐ (Kurang)", 0xE74C3C)

    async def disable_all_and_close(self, channel):
        for child in self.children:
            child.disabled = True
        try:
            await channel.edit(view=self)
        except Exception:
            pass
        
        await asyncio.sleep(5)
        try:
            await channel.delete(reason="Tiket selesai dan rating telah diberikan.")
        except Exception:
            pass

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
        name="🛡️ Moderasi, Admin & Tiket",
        value="`.panelorder` — Mengirim panel form pembelian\n"
              "`.clear` / `.cls` — Menghapus pesan\n"
              "`.closeticket` / `.done` — Menutup tiket & memunculkan tombol rating\n"
              "`.role @user [nama role]` — Memberikan/mencabut role\n"
              "`.ban @user [alasan]` — Memblokir member",
        inline=False
    )
    embed.add_field(
        name="📊 Level & XP",
        value="`.rank` — Cek kartu profil & XP\n"
              "`.top` / `.lb` — Cek Leaderboard server",
        inline=False
    )
    embed.add_field(
        name="🛠️ Utility & Hiburan",
        value="`.server` | `.whois` | `.avatar` | `.roll` | `.coinflip` | `.rps` | `.quote`",
        inline=False
    )
    embed.set_footer(text="TONGSOP Store • All Rights Reserved")
    await ctx.send(embed=embed)

# --- PERINTAH PANEL ORDER MANUAL (ADMIN) ---
@bot.command(name="panelorder")
@commands.has_permissions(administrator=True)
async def manual_panel_order(ctx):
    embed = discord.Embed(
        title="🛒 TONGSOP STORE ORDER PANEL",
        description="Silakan klik tombol di bawah ini untuk mengisi formulir pemesanan produk.",
        color=0x3498DB
    )
    embed.set_footer(text="TONGSOP Store • Secure Order System")
    await ctx.send(embed=embed, view=BuyButtonView())

@manual_panel_order.error
async def panel_order_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Hanya Administrator yang dapat memunculkan panel order!")

# --- PERINTAH MENUTUP TIKET & RATING (.done / .closeticket) [Hanya Staf/Mod] ---
@bot.command(name="closeticket", aliases=["done", "selesai"])
@commands.has_permissions(manage_channels=True)
async def close_ticket(ctx, member: discord.Member = None):
    target_member = member or ctx.author 

    embed = discord.Embed(
        title="🔒 TIKET SELESAI / DITUTUP",
        description=f"Terima kasih {target_member.mention} telah memesan di **TONGSOP Store**. \n\nSilakan berikan penilaian/rating pelayanan kami dengan menekan tombol di bawah ini (Opsional):",
        color=0xF1C40F
    )
    embed.set_footer(text="Pilih tombol rating di bawah untuk mengirim testimoni otomatis ke channel testi.")
    
    await ctx.send(embed=embed, view=RatingView(target_member))

@close_ticket.error
async def closeticket_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu tidak memiliki izin untuk menutup tiket!")

# --- LEADERBOARD TOP 10 ---
@bot.command(name="leaderboard", aliases=["lb", "top", "levels"])
async def show_leaderboard(ctx):
    if not user_data:
        await ctx.send("❌ Belum ada data level di server ini.")
        return

    sorted_users = sorted(user_data.items(), key=lambda item: (item[1]['level'], item[1]['xp']), reverse=True)

    embed = discord.Embed(
        title="🏆 LEADERBOARD TOP SERVER",
        description="Daftar peringkat member teraktif di server:",
        color=0xF1C40F
    )

    leaderboard_lines = []
    for i, (user_id, data) in enumerate(sorted_users[:10]):
        member = ctx.guild.get_member(user_id)
        if not member:
            try:
                member = await bot.fetch_user(user_id)
            except Exception:
                member = None

        if i == 0: rank_num = "🥇 #1"
        elif i == 1: rank_num = "🥈 #2"
        elif i == 2: rank_num = "🥉 #3"
        else: rank_num = f"#{i+1}"

        user_mention = member.mention if member else f"<@{user_id}>"
        line = f"**{rank_num}** • {user_mention} • LVL: `+{data['level']}` XP: `+{data['xp']}`"
        leaderboard_lines.append(line)

    embed.add_field(name="📊 Peringkat Teratas", value="\n".join(leaderboard_lines), inline=False)
    embed.set_footer(text=f"Diminta oleh {ctx.author.display_name} • TONGSOP Store")
    await ctx.send(embed=embed)

# --- RANK & XP ---
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

@bot.command(name="addxp", aliases=["axp"])
@commands.has_permissions(administrator=True)
async def add_xp(ctx, member: discord.Member, amount: int):
    data = get_user_xp(member.id)
    data["xp"] += amount
    await ctx.send(f"✨ Berhasil menambahkan **{amount} XP** kepada {member.mention}.")

# --- MODERASI (CLEAR, ROLE, BAN) ---
@bot.command(name="clear", aliases=["purge", "cls"])
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 5):
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Berhasil menghapus **{len(deleted) - 1}** pesan.")
    await asyncio.sleep(3)
    try: await msg.delete()
    except Exception: pass

@bot.command(name="role", aliases=["giverole"])
@commands.has_permissions(manage_roles=True)
async def manage_role(ctx, member: discord.Member, *, rolename: str):
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=rolename)
    if not role:
        role = await guild.create_role(name=rolename)
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"✅ Berhasil **mencabut** role `{role.name}` dari {member.mention}.")
    else:
        await member.add_roles(role)
        await ctx.send(f"✅ Berhasil **memberikan** role `{role.name}` kepada {member.mention}!")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_member(ctx, member: discord.Member, *, reason: str = "Tidak ada alasan"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Berhasil membanned {member.mention}. Alasan: `{reason}`")

# --- UTILITY & FUN ---
@bot.command(name="server", aliases=["serverinfo"])
async def server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 Informasi Server: {guild.name}", color=0x2ECC71)
    if guild.icon: embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="👑 Pemilik", value=guild.owner.mention if guild.owner else "N/A", inline=True)
    embed.add_field(name="👥 Total Member", value=f"`{guild.member_count}`", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="avatar", aliases=["pp"])
async def show_avatar(ctx, member: discord.Member = None):
    target = member or ctx.author
    embed = discord.Embed(title=f"🖼️ Avatar — {target.name}", color=0x9B59B6)
    embed.set_image(url=target.avatar.url if target.avatar else target.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="quote")
async def random_quote(ctx):
    url = "https://api.quotable.io/random"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    await ctx.send(f"💬 *“{data.get('content')}”* \n— **{data.get('author')}**")
                    return
    except Exception:
        pass
    await ctx.send("💬 *“Kesuksesan besar dimulai dari langkah kecil yang konsisten.”*")

# ==================== RUN BOT ====================
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token bot tidak ditemukan!")
