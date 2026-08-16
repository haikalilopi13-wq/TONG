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

# Channel ID Target
GENERAL_CHANNEL_ID = 1538646829938516048  
TARGET_CATEGORY_OR_PARENT_ID = 1517625110536786050  # Kategori tempat tiket dikelompokkan
TESTIMONI_CHANNEL_ID = 1517625158263898284        # Channel Testimoni Pembelian Umum
REDFINGER_TESTI_CHANNEL_ID = 1538673467442856059 # Channel Testimoni Khusus Redfinger
STAFF_ROLE_ID = 1517580561361928463  

# Sistem Penyimpanan Data di Memori
user_data = {} 

def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"xp": 0, "level": 0, "money": 0}
    return user_data[user_id]

# ==================== EVENTS BOT ====================
@bot.event
async def on_ready():
    print(f"✨ Bot Berhasil Terhubung as {bot.user}!")
    print("🚀 Bot siap dengan Sistem Tiket, Testimoni Terpisah, & Perintah Lengkap!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Sistem XP & Leveling Sederhana
    data = get_user_data(message.author.id)
    data["xp"] += random.randint(5, 10)
    
    xp_needed = (data["level"] + 1) * 100
    if data["xp"] >= xp_needed:
        data["level"] += 1
        data["xp"] = 0
        try:
            await message.channel.send(f"🎉 Selamat {message.author.mention}, kamu naik ke Level **{data['level']}**!")
        except Exception:
            pass
    
    await bot.process_commands(message)

# ==================== MODAL ULASAN TEKS PEMBELI ====================
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

        # Memisahkan Channel Testimoni Berdasarkan Jenis Layanan
        if self.ticket_type == "redfinger":
            target_channel = guild.get_channel(REDFINGER_TESTI_CHANNEL_ID)
            embed_title = "📱 ⭐ TESTIMONI JASA SPLIT REDFINGER"
        else:
            target_channel = guild.get_channel(TESTIMONI_CHANNEL_ID)
            embed_title = "🛒 ⭐ TESTIMONI PEMBELIAN PRODUK"

        testi_embed = discord.Embed(
            title=embed_title,
            description=f"Terima kasih atas kepercayaan Anda kepada **TONGSOP Store**!",
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

    @discord.ui.button(label="🤝 Claim Ticket", style=discord.ButtonStyle.success, custom_id="claim_ticket_btn")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
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
            
        ticket_embed.set_footer(text="Staf dapat mengaktifkan tombol rating atau menutup tiket di bawah.")

        await interaction.message.edit(embed=ticket_embed, view=TicketControlView(self.ticket_opener, self.claimed_by, self.ticket_type, rating_unlocked=False))
        await interaction.response.send_message(f"✅ Anda berhasil mengklaim tiket ini!", ephemeral=True)

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

    @discord.ui.button(label="✨ Buka Akses Rating", style=discord.ButtonStyle.primary, custom_id="unlock_rating_btn")
    async def unlock_rating_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Hanya Staf yang dapat membuka akses rating untuk pembeli!", ephemeral=True)
            return

        self.remove_item(button)
        new_view = TicketControlViewUnlocked(self.ticket_opener, self.claimed_by, self.ticket_type)
        
        await interaction.message.edit(view=new_view)
        await interaction.response.send_message("✅ Akses rating & ulasan telah dibuka untuk pembeli!", ephemeral=False)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn_only")
    async def close_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Hanya Admin atau Staf yang memiliki izin untuk menutup tiket ini!", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Tiket ini akan ditutup dan dihapus dalam 5 detik oleh staf...", ephemeral=False)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason="Tiket ditutup oleh staf.")
        except Exception:
            pass

    @discord.ui.button(label="🔒 Rating (Menunggu Staf)", style=discord.ButtonStyle.secondary, custom_id="rate_ticket_btn_only", disabled=True)
    async def rate_ticket_btn_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

class TicketControlViewUnlocked(discord.ui.View):
    def __init__(self, ticket_opener: discord.Member, claimed_by: discord.Member, ticket_type: str):
        super().__init__(timeout=None)
        self.ticket_opener = ticket_opener
        self.claimed_by = claimed_by
        self.ticket_type = ticket_type

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn_unlocked")
    async def close_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Hanya Admin atau Staf yang memiliki izin untuk menutup tiket ini!", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Tiket ini akan ditutup dan dihapus dalam 5 detik oleh staf...", ephemeral=False)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason="Tiket ditutup oleh staf.")
        except Exception:
            pass

    @discord.ui.button(label="⭐ Beri Rating & Ulasan", style=discord.ButtonStyle.success, custom_id="rate_ticket_btn_active")
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

# ==================== FORMULIR PEMBELIAN (BUY MODAL) ====================
class BuyModal(discord.ui.Modal, title="BUY"):
    mau_beli = discord.ui.TextInput(
        label="Mau beli apa?",
        placeholder="Make a selection",
        style=discord.TextStyle.short,
        required=True
    )
    jumlah = discord.ui.TextInput(
        label="Jumlah",
        placeholder="Jumlah",
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
                description=f"Halo {member.mention}, tiket Anda telah dibuat.\n\nStaf kami belum mengetahui detail pesanan Anda hingga ada staf yang menekan tombol **Claim Ticket** di bawah ini.",
                color=0xE67E22
            )
            initial_embed.set_footer(text="Menunggu staf mengambil alih tiket...")

            staff_role = guild.get_role(STAFF_ROLE_ID)
            ping_text = f"{staff_role.mention} {member.mention}" if staff_role else f"{member.mention}"

            await ticket_channel.send(
                content=ping_text, 
                embed=initial_embed, 
                view=ClaimTicketView(member, data_pesanan, ticket_type="buy")
            )

            await interaction.response.send_message(
                f"✅ Formulir berhasil dikirim! Channel tiket Anda: {ticket_channel.mention}",
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(f"❌ Terjadi kesalahan: {e}", ephemeral=True)

# ==================== FORMULIR REDFINGER ====================
class RedfingerModal(discord.ui.Modal, title="SET UP REDFINGER"):
    paket = discord.ui.TextInput(
        label="Split Redfinger",
        placeholder="SPLIT TERGANTUNG DEVICE",
        style=discord.TextStyle.short,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        data_pesanan = {
            "📱 Split Redfinger": self.paket.value
        }

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
                description=f"Halo {member.mention}, pesanan jasa split Redfinger Anda telah dibuat.\n\nDetail pesanan akan terbuka setelah staf menekan tombol **Claim Ticket**.",
                color=0xE67E22
            )
            initial_embed.set_footer(text="Menunggu staf mengambil alih tiket...")

            staff_role = guild.get_role(STAFF_ROLE_ID)
            ping_text = f"{staff_role.mention} {member.mention}" if staff_role else f"{member.mention}"

            await ticket_channel.send(
                content=ping_text, 
                embed=initial_embed, 
                view=ClaimTicketView(member, data_pesanan, ticket_type="redfinger")
            )

            await interaction.response.send_message(
                f"✅ Formulir Redfinger terkirim! Channel tiket Anda: {ticket_channel.mention}",
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(f"❌ Terjadi kesalahan: {e}", ephemeral=True)

# ==================== VIEW TOMBOL UTAMA PANEL ====================
class BuyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛒 Buka Form Pembelian", style=discord.ButtonStyle.green, custom_id="open_buy_modal_persistent")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BuyModal())

    @discord.ui.button(label="📱 Set Up Redfinger", style=discord.ButtonStyle.blurple, custom_id="open_redfinger_modal_persistent")
    async def open_redfinger(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RedfingerModal())

# ==================== PERINTAH-PERINTAH BOT ====================

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Latency: `{round(bot.latency * 1000)}ms`")

@bot.command(name="profile", aliases=["rank", "level"])
async def profile(ctx):
    data = get_user_data(ctx.author.id)
    embed = discord.Embed(title=f"Profil {ctx.author.name}", color=0x3498DB)
    embed.add_field(name="Level", value=data["level"], inline=True)
    embed.add_field(name="XP", value=data["xp"], inline=True)
    embed.add_field(name="Money", value=f"${data['money']}", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="addmoney")
@commands.has_permissions(administrator=True)
async def addmoney(ctx, member: discord.Member, amount: int):
    data = get_user_data(member.id)
    data["money"] += amount
    await ctx.send(f"✅ Ditambahkan ${amount} ke {member.name}. Total: ${data['money']}")

@bot.command(name="info", aliases=["help"])
async def info_command(ctx):
    embed = discord.Embed(
        title="📌 PUSAT BANTUAN & DAFTAR PERINTAH", 
        description="Gunakan awalan titik (`.`)", 
        color=0x3498DB
    )
    embed.add_field(
        name="Perintah Utama", 
        value="`.panelorder` — Kirim panel\n`.closeticket` — Tutup tiket\n`.profile` — Cek level/uang\n`.ping` — Cek latensi bot", 
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name="panelorder")
async def panelorder(ctx):
    # Cek akses staff (bisa pakai Manage Channels, Administrator, atau punya Role Staff)
    is_staff = ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_channels
    if not is_staff and STAFF_ROLE_ID:
        staff_role_obj = ctx.guild.get_role(STAFF_ROLE_ID)
        if staff_role_obj and staff_role_obj in ctx.author.roles:
            is_staff = True

    if not is_staff:
        await ctx.send("❌ Hanya Staff atau Administrator yang dapat memunculkan panel order!")
        return

    embed = discord.Embed(
        title="🛒 TONGSOP OFFICIAL TICKET SYSTEM",
        description="Silakan klik tombol di bawah ini untuk mengisi formulir pemesanan produk atau set up jasa split Redfinger.",
        color=0x3498DB
    )
    embed.set_footer(text="TONGSOP Store • Secure Order System")
    
    target_channel = bot.get_channel(GENERAL_CHANNEL_ID)
    if target_channel:
        await target_channel.send(embed=embed, view=BuyButtonView())
        await ctx.send(f"✅ Panel order berhasil dikirim ke channel <#{GENERAL_CHANNEL_ID}>!")
    else:
        await ctx.send(embed=embed, view=BuyButtonView())

@bot.command(name="closeticket", aliases=["done", "selesai"])
@commands.has_permissions(manage_channels=True)
async def close_ticket(ctx):
    embed = discord.Embed(title="🔒 TIKET DITUTUP", description="Tiket ini akan dihapus...", color=0xF1C40F)
    await ctx.send(embed=embed)
    await asyncio.sleep(3)
    try:
        await ctx.channel.delete()
    except Exception:
        pass

# ==================== RUN BOT ====================
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Token bot tidak ditemukan di Environment Variables!")
