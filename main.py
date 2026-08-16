import discord
from discord.ext import commands
import os
import random
import datetime
import asyncio

# ==================== CONFIG BOT ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Channel ID Target & Konfigurasi
TARGET_CATEGORY_OR_PARENT_ID = 1517625110536786050  # Kategori tempat tiket dibuat
TESTIMONI_CHANNEL_ID = 1517625158263898284         # Channel Testimoni Pembelian Umum
REDFINGER_TESTI_CHANNEL_ID = 1538673467442856059 # Channel Testimoni Khusus Redfinger
STAFF_ROLE_ID = 1517580561361928463              # ID Role Staff / Admin

# Sistem Penyimpanan Level, XP, & Cooldown di Memori
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
    print("🚀 Bot siap dengan Sistem Tiket, Testimoni Terpisah, Leaderboard, & Fitur Lengkap!")

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

    await bot.process_commands(message)

# ==================== MODAL ULASAN & TESTIMONI ====================
class ReviewModal(discord.ui.Modal, title="BERI ULASAN & TESTIMONI"):
    def __init__(self, ticket_opener: discord.Member, rating_bintang: str, claimed_by: discord.Member, ticket_type: str):
        super().__init__()
        self.ticket_opener = ticket_opener
        self.rating_bintang = rating_bintang
        self.claimed_by = claimed_by
        self.ticket_type = ticket_type

        self.ulasan_teks = discord.ui.TextInput(
            label="Ulasan / Pesan Anda",
            placeholder="Contoh: Proses cepat, aman, dan mantap!",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=300
        )
        self.add_item(self.ulasan_teks)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        buyer = interaction.user

        if "5" in self.rating_bintang:
            color_code = 0x2ECC71
        elif "3" in self.rating_bintang:
            color_code = 0x3498DB
        else:
            color_code = 0xE74C3C

        if self.ticket_type == "redfinger":
            target_channel = guild.get_channel(REDFINGER_TESTI_CHANNEL_ID)
            embed_title = "📱 ⭐ TESTIMONI JASA SPLIT REDFINGER"
        else:
            target_channel = guild.get_channel(TESTIMONI_CHANNEL_ID)
            embed_title = "🛒 ⭐ TESTIMONI PEMBELIAN PRODUK"

        testi_embed = discord.Embed(
            title=embed_title,
            description="Terima kasih atas kepercayaan Anda kepada **TONGSOP Store**!",
            color=color_code
        )
        testi_embed.add_field(name="👤 Pembeli / Klien", value=f"{buyer.mention} (`@{buyer.name}`)", inline=True)
        
        staff_display = self.claimed_by.mention if self.claimed_by else "Staf / Admin"
        testi_embed.add_field(name="🛠️ Ditangani Oleh", value=staff_display, inline=True)
        
        testi_embed.add_field(name="🏆 Penilaian", value=self.rating_bintang, inline=False)
        testi_embed.add_field(name="💬 Ulasan Klien", value=f"*{self.ulasan_teks.value}*", inline=False)
        testi_embed.set_footer(text=f"TONGSOP Store • {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")

        if target_channel:
            try:
                await target_channel.send(embed=testi_embed)
            except Exception:
                pass

        await interaction.response.send_message("✨ Terima kasih banyak atas ulasan dan ratingnya! Testimoni berhasil dikirim.", ephemeral=True)

class RatingChoiceView(discord.ui.View):
    def __init__(self, ticket_opener: discord.Member, claimed_by: discord.Member, ticket_type: str):
        super().__init__(timeout=60)
        self.ticket_opener = ticket_opener
        self.claimed_by = claimed_by
        self.ticket_type = ticket_type

    @discord.ui.button(label="⭐ 5 (Sangat Puas)", style=discord.ButtonStyle.green)
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReviewModal(self.ticket_opener, "⭐⭐⭐⭐⭐ (Sangat Puas)", self.claimed_by, self.ticket_type))

    @discord.ui.button(label="⭐ 3 (Cukup)", style=discord.ButtonStyle.blurple)
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReviewModal(self.ticket_opener, "⭐⭐⭐ (Cukup)", self.claimed_by, self.ticket_type))

    @discord.ui.button(label="⭐ 1 (Kurang)", style=discord.ButtonStyle.red)
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReviewModal(self.ticket_opener, "⭐ (Kurang)", self.claimed_by, self.ticket_type))

# ==================== VIEW KONTROL & CLAIM TIKET ====================
class ClaimTicketView(discord.ui.View):
    def __init__(self, ticket_opener: discord.Member, ticket_data: dict, ticket_type: str):
        super().__init__(timeout=None)
        self.ticket_opener = ticket_opener
        self.ticket_data = ticket_data
        self.ticket_type = ticket_type
        self.claimed_by = None

    @discord.ui.button(label="🤝 Claim Ticket", style=discord.ButtonStyle.success, custom_id="claim_ticket_btn_unique")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels and not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
            await interaction.response.send_message("❌ Hanya Staf/Admin yang dapat mengklaim tiket ini!", ephemeral=True)
            return

        if self.claimed_by is not None:
            await interaction.response.send_message(f"❌ Tiket ini sudah diklaim oleh {self.claimed_by.mention}!", ephemeral=True)
            return

        self.claimed_by = interaction.user
        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        button.style = discord.ButtonStyle.secondary

        await interaction.channel.set_permissions(interaction.user, view_channel=True, send_messages=True)

        ticket_embed = discord.Embed(
            title="🎟️ TIKET DIKLAIM & DIBUKA",
            description=f"Tiket ini telah diambil oleh staf {interaction.user.mention}.\n\nPembuat Tiket: {self.ticket_opener.mention} (`@{self.ticket_opener.name}`)",
            color=0x3498DB
        )
        for key, value in self.ticket_data.items():
            ticket_embed.add_field(name=key, value=value, inline=False)
            
        ticket_embed.set_footer(text="Staf dapat membuka akses rating atau menutup tiket di bawah.")

        await interaction.message.edit(embed=ticket_embed, view=TicketControlView(self.ticket_opener, self.claimed_by, self.ticket_type, rating_unlocked=False))
        await interaction.response.send_message("✅ Anda berhasil mengklaim tiket ini!", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self, ticket_opener: discord.Member, claimed_by: discord.Member, ticket_type: str, rating_unlocked: bool = False):
        super().__init__(timeout=None)
        self.ticket_opener = ticket_opener
        self.claimed_by = claimed_by
        self.ticket_type = ticket_type
        
        self.rate_ticket_btn_only.disabled = not rating_unlocked
        if rating_unlocked:
            self.rate_ticket_btn_only.label = "⭐ Beri Rating & Ulasan (Dibuka)"
            self.rate_ticket_btn_only.style = discord.ButtonStyle.success
        else:
            self.rate_ticket_btn_only.label = "🔒 Rating (Menunggu Staf)"
            self.rate_ticket_btn_only.style = discord.ButtonStyle.secondary

    @discord.ui.button(label="✨ Buka Akses Rating", style=discord.ButtonStyle.primary, custom_id="unlock_rating_btn_unique")
    async def unlock_rating_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels and not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
            await interaction.response.send_message("❌ Hanya Staf yang dapat membuka akses rating untuk pembeli!", ephemeral=True)
            return

        self.remove_item(button)
        new_view = TicketControlViewUnlocked(self.ticket_opener, self.claimed_by, self.ticket_type)
        await interaction.message.edit(view=new_view)
        await interaction.response.send_message("✅ Akses rating & ulasan telah dibuka untuk pembeli!", ephemeral=False)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn_only_unique")
    async def close_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels and not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
            await interaction.response.send_message("❌ Hanya Staf yang memiliki izin untuk menutup tiket ini!", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Tiket ini akan ditutup dan dihapus dalam 5 detik...", ephemeral=False)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason="Tiket ditutup oleh staf.")
        except Exception:
            pass

    @discord.ui.button(label="🔒 Rating (Menunggu Staf)", style=discord.ButtonStyle.secondary, custom_id="rate_ticket_btn_only_unique", disabled=True)
    async def rate_ticket_btn_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

class TicketControlViewUnlocked(discord.ui.View):
    def __init__(self, ticket_opener: discord.Member, claimed_by: discord.Member, ticket_type: str):
        super().__init__(timeout=None)
        self.ticket_opener = ticket_opener
        self.claimed_by = claimed_by
        self.ticket_type = ticket_type

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_unlocked_unique")
    async def close_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels and not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
            await interaction.response.send_message("❌ Hanya Staf yang memiliki izin untuk menutup tiket ini!", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Tiket ini akan ditutup dan dihapus dalam 5 detik...", ephemeral=False)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason="Tiket ditutup oleh staf.")
        except Exception:
            pass

    @discord.ui.button(label="⭐ Beri Rating & Ulasan", style=discord.ButtonStyle.success, custom_id="rate_ticket_active_unique")
    async def rate_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ticket_opener and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Hanya pembuat tiket yang dapat memberikan ulasan!", ephemeral=True)
            return

        embed = discord.Embed(
            title="⭐ PILIH RATING PELAYANAN",
            description="Silakan pilih tingkat kepuasan Anda terlebih dahulu:",
            color=0xF1C40F
        )
        await interaction.response.send_message(embed=embed, view=RatingChoiceView(self.ticket_opener, self.claimed_by, self.ticket_type), ephemeral=True)

# ==================== MODAL FORMULIR (BUY & REDFINGER) ====================
class BuyModal(discord.ui.Modal, title="BUY PRODUK"):
    mau_beli = discord.ui.TextInput(label="Mau beli apa?", placeholder="Make a selection", style=discord.TextStyle.short, required=True)
    jumlah = discord.ui.TextInput(label="Jumlah", placeholder="Jumlah", style=discord.TextStyle.short, required=True)
    username_roblox = discord.ui.TextInput(label="User Name Roblox", placeholder="Masukkan username Roblox Anda", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        data_pesanan = {
            "📦 Mau Beli": self.mau_beli.value,
            "🔢 Jumlah": self.jumlah.value,
            "👤 Roblox Username": self.username_roblox.value
        }
        guild = interaction.guild
        member = interaction.user
        category = guild.get_channel(TARGET_CATEGORY_OR_PARENT_ID)
        channel_name = f"buy-{member.name}".lower()

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        try:
            if isinstance(category, discord.CategoryChannel):
                ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
            else:
                ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)

            initial_embed = discord.Embed(
                title="🔒 TIKET BARU (MENUNGGU KLAIM STAF)",
                description=f"Halo {member.mention}, tiket Anda telah dibuat.\n\nStaf kami belum melihat detail pesanan hingga menekan tombol **Claim Ticket** di bawah.",
                color=0xE67E22
            )
            staff_role = guild.get_role(STAFF_ROLE_ID)
            ping_text = f"{staff_role.mention} {member.mention}" if staff_role else f"{member.mention}"

            await ticket_channel.send(content=ping_text, embed=initial_embed, view=ClaimTicketView(member, data_pesanan, ticket_type="buy"))
            await interaction.response.send_message(f"✅ Formulir berhasil dikirim! Channel tiket: {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Terjadi kesalahan: {e}", ephemeral=True)

class RedfingerModal(discord.ui.Modal, title="SET UP REDFINGER"):
    paket = discord.ui.TextInput(label="Split Redfinger", placeholder="SPLIT TERGANTUNG DEVICE", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        data_pesanan = {"📱 Split Redfinger": self.paket.value}
        guild = interaction.guild
        member = interaction.user
        category = guild.get_channel(TARGET_CATEGORY_OR_PARENT_ID)
        channel_name = f"redfinger-{member.name}".lower()

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        try:
            if isinstance(category, discord.CategoryChannel):
                ticket_channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
            else:
                ticket_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)

            initial_embed = discord.Embed(
                title="🔒 TIKET REDFINGER (MENUNGGU KLAIM STAF)",
                description=f"Halo {member.mention}, pesanan jasa split Redfinger Anda telah dibuat.\n\nDetail akan terbuka setelah staf menekan tombol **Claim Ticket**.",
                color=0xE67E22
            )
            staff_role = guild.get_role(STAFF_ROLE_ID)
            ping_text = f"{staff_role.mention} {member.mention}" if staff_role else f"{member.mention}"

            await ticket_channel.send(content=ping_text, embed=initial_embed, view=ClaimTicketView(member, data_pesanan, ticket_type="redfinger"))
            await interaction.response.send_message(f"✅ Formulir Redfinger terkirim! Channel tiket: {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Terjadi kesalahan: {e}", ephemeral=True)

class BuyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛒 Buka Form Pembelian", style=discord.ButtonStyle.green, custom_id="open_buy_modal_persistent_v2")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BuyModal())

    @discord.ui.button(label="📱 Set Up Redfinger", style=discord.ButtonStyle.blurple, custom_id="open_redfinger_modal_persistent_v2")
    async def open_redfinger(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RedfingerModal())

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
              "`.top` / `.lb` — Cek Top 10 Leaderboard dalam Kotak Embed\n"
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
        value="`.roll` — Dadu | `.coinflip` — Koin | `.rps` — Suit | `.rate` — Nilai | `.quote` — Katabijak",
        inline=False
    )
    embed.set_footer(text="TONGSOP Store • All Rights Reserved")
    await ctx.send(embed=embed)

@bot.command(name="panelorder")
@commands.has_permissions(manage_channels=True)
async def panelorder_cmd(ctx):
    embed = discord.Embed(
        title="🛒 TONGSOP OFFICIAL TICKET SYSTEM",
        description="Silakan klik tombol di bawah ini untuk mengisi formulir pemesanan produk atau set up jasa split Redfinger.",
        color=0x3498DB
    )
    embed.set_footer(text="TONGSOP Store • Secure Order System")
    
    # Kirim panel langsung ke channel tempat perintah .panelorder diketik (misal: ID 1538646829938516048)
    await ctx.send(embed=embed, view=BuyButtonView())

# --- LEADERBOARD TOP 10 ---
@bot.command(name="leaderboard", aliases=["lb", "top", "levels"])
async def show_leaderboard(ctx):
    if not user_data:
        await ctx.send("❌ Belum ada data level di server ini. Yuk mulai aktif chat!")
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

        if i == 0:
            rank_num = "🥇 #1"
        elif i == 1:
            rank_num = "🥈 #2"
        elif i == 2:
            rank_num = "🥉 #3"
        else:
            rank_num = f"#{i+1}"

        user_mention = member.mention if member else f"<@{user_id}>"
        line = f"**{rank_num}** • {user_mention} • LVL: `+{data['level']}` XP: `+{data['xp']}`"
        leaderboard_lines.append(line)

    embed.add_field(name="📊 Peringkat Teratas", value="\n".join(leaderboard_lines), inline=False)
    footer_text = f"Diminta oleh {ctx.author.display_name} • TONGSOP Store"
    footer_icon = ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    embed.set_footer(text=footer_text, icon_url=footer_icon)
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

# --- MODERASI: BAN ---
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_member(ctx, member: discord.Member, *, reason: str = "Tidak ada alasan"):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 Berhasil membanned {member.mention}. Alasan: `{reason}`")
    except Exception as e:
        await ctx.send(f"❌ Gagal ban member: {e}")

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

# --- MODERASI: UNTIMEOUT ---
@bot.command(name="untimeout", aliases=["unmute", "unt"])
@commands.has_permissions(moderate_members=True)
async def untimeout_member(ctx, member: discord.Member, *, reason: str = "Selesai masa hukuman"):
    try:
        await member.timeout(None, reason=reason)
        await ctx.send(f"🔊 Berhasil membatalkan timeout untuk {member.mention}. Alasan: `{reason}`")
    except Exception as e:
        await ctx.send(f"❌ Gagal membatalkan timeout: {e}")

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
         (pilihan == "gunthting" and bot_choice == "kertas"): # typo fix aman
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
    print("❌ Token bot tidak ditemukan di Environment Variables!")
