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
GENERAL_CHANNEL_ID = 1538646829938516048  
TARGET_CATEGORY_OR_PARENT_ID = 1517625110536786050  
TESTIMONI_CHANNEL_ID = 1517625158263898284  

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
    print("🚀 Bot siap dengan Sistem Claim Ticket & Ulasan Kustom!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

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

# ==================== MODAL ULASAN TEKS PEMBELI ====================
class ReviewModal(discord.ui.Modal, title="BERI ULASAN & TESTIMONI"):
    def __init__(self, ticket_opener: discord.Member, rating_bintang: str):
        super().__init__()
        self.ticket_opener = ticket_opener
        self.rating_bintang = rating_bintang

        self.ulasan_teks = discord.ui.TextInput(
            label="Ulasan / Pesan Anda",
            placeholder="Contoh: Pelayanannya sangat cepat dan ramah sekali!",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=300
        )
        self.add_item(self.ulasan_teks)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        testi_channel = guild.get_channel(TESTIMONI_CHANNEL_ID)
        buyer = interaction.user

        if "5" in self.rating_bintang:
            color_code = 0x2ECC71
        elif "3" in self.rating_bintang:
            color_code = 0x3498DB
        else:
            color_code = 0xE74C3C

        testi_embed = discord.Embed(
            title="⭐ TESTIMONI & ULASAN PELANGGAN",
            description=f"Terima kasih atas kepercayaan Anda kepada **TONGSOP Store**!",
            color=color_code
        )
        testi_embed.add_field(
            name="👤 Pembeli / Klien", 
            value=f"{buyer.mention} (`@{buyer.name}`)", 
            inline=True
        )
        testi_embed.add_field(name="🏆 Penilaian", value=self.rating_bintang, inline=True)
        testi_embed.add_field(name="💬 Ulasan Pembeli", value=f"*{self.ulasan_teks.value}*", inline=False)
        testi_embed.set_footer(text=f"TONGSOP Store • {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")

        if testi_channel:
            try:
                await testi_channel.send(embed=testi_embed)
            except Exception:
                pass

        await interaction.response.send_message("✨ Terima kasih banyak atas ulasan dan ratingnya! Testimoni berhasil dikirim ke channel testi.", ephemeral=True)

class RatingChoiceView(discord.ui.View):
    def __init__(self, ticket_opener: discord.Member):
        super().__init__(timeout=60)
        self.ticket_opener = ticket_opener

    @discord.ui.button(label="⭐ 5 (Sangat Puas)", style=discord.ButtonStyle.green)
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReviewModal(self.ticket_opener, "⭐⭐⭐⭐⭐ (Sangat Puas)"))

    @discord.ui.button(label="⭐ 3 (Cukup)", style=discord.ButtonStyle.blurple)
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReviewModal(self.ticket_opener, "⭐⭐⭐ (Cukup)"))

    @discord.ui.button(label="⭐ 1 (Kurang)", style=discord.ButtonStyle.red)
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReviewModal(self.ticket_opener, "⭐ (Kurang)"))

# ==================== VIEW KONTROL & CLAIM TIKET ====================
class ClaimTicketView(discord.ui.View):
    def __init__(self, ticket_opener: discord.Member, ticket_data: dict):
        super().__init__(timeout=None)
        self.ticket_opener = ticket_opener
        self.ticket_data = ticket_data
        self.claimed_by = None

    @discord.ui.button(label="🤝 Claim Ticket", style=discord.ButtonStyle.success, custom_id="claim_ticket_btn")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Cek apakah yang klik punya izin manage_channels / staf
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

        # Berikan akses penuh ke staf yang mengklaim
        await interaction.channel.set_permissions(interaction.user, view_channel=True, send_messages=True)

        # Buat embed data pesanan yang sebelumnya disembunyikan
        ticket_embed = discord.Embed(
            title="🎟️ TIKET DIKLAIM & DIBUKA",
            description=f"Tiket ini telah diambil oleh staf {interaction.user.mention}.\n\nPembuat Tiket: {self.ticket_opener.mention} (`@{self.ticket_opener.name}`)",
            color=0x3498DB
        )
        
        for key, value in self.ticket_data.items():
            ticket_embed.add_field(name=key, value=value, inline=False)
            
        ticket_embed.set_footer(text="Gunakan tombol di bawah untuk menutup tiket.")

        # Update pesan dengan menampilkan data lengkap & tombol kontrol biasa (Close & Rating)
        await interaction.message.edit(embed=ticket_embed, view=TicketControlView(self.ticket_opener))
        await interaction.response.send_message(f"✅ Anda berhasil mengklaim tiket ini!", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self, ticket_opener: discord.Member):
        super().__init__(timeout=None)
        self.ticket_opener = ticket_opener

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn_only")
    async def close_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ticket_opener and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Hanya pembuat tiket atau staf yang dapat menutup tiket ini!", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Tiket ini akan ditutup dan dihapus dalam 5 detik...", ephemeral=False)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason="Tiket ditutup.")
        except Exception:
            pass

    @discord.ui.button(label="⭐ Beri Rating & Ulasan", style=discord.ButtonStyle.success, custom_id="rate_ticket_btn_only")
    async def rate_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ticket_opener and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Hanya pembuat tiket yang dapat memberikan ulasan!", ephemeral=True)
            return

        embed = discord.Embed(
            title="⭐ PILIH RATING PELAYANAN",
            description="Silakan pilih tingkat kepuasan Anda terlebih dahulu:",
            color=0xF1C40F
        )
        await interaction.response.send_message(embed=embed, view=RatingChoiceView(self.ticket_opener), ephemeral=True)

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
        channel_name = f"ticket-{member.name}".lower()

        # Konfigurasi agar channel awalnya tersembunyi dari staf umum (hanya bot & pembuat)
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

            # Pesan awal sebelum diklaim staf (detail pesanan disembunyikan sampai diklaim)
            initial_embed = discord.Embed(
                title="🔒 TIKET BARU (MENUNGGU KLAIM STAF)",
                description=f"Halo {member.mention}, tiket Anda telah dibuat.\n\nStaf kami belum mengetahui detail pesanan Anda hingga ada staf yang menekan tombol **Claim Ticket** di bawah ini.",
                color=0xE67E22
            )
            initial_embed.set_footer(text="Menunggu staf mengambil alih tiket...")

            await ticket_channel.send(
                content=f"{member.mention}", 
                embed=initial_embed, 
                view=ClaimTicketView(member, data_pesanan)
            )

            await interaction.response.send_message(
                f"✅ Formulir berhasil dikirim! Channel tiket Anda: {ticket_channel.mention}",
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(f"❌ Terjadi kesalahan: {e}", ephemeral=True)

# ==================== FORMULIR REDFINGER (1 KOLOM) ====================
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

            await ticket_channel.send(
                content=f"{member.mention}", 
                embed=initial_embed, 
                view=ClaimTicketView(member, data_pesanan)
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

# ==================== PERINTAH BOT ====================

@bot.command(name="ping")
async def check_ping(ctx):
    latency_ms = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: `{latency_ms}ms`")

@bot.command(name="info", aliases=["help"])
async def show_info(ctx):
    embed = discord.Embed(title="📌 PUSAT BANTUAN & DAFTAR PERINTAH", description="Gunakan awalan titik (`.`)", color=0x3498DB)
    embed.add_field(name="Perintah Utama", value="`.panelorder` — Kirim panel\n`.closeticket` — Tutup tiket", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="panelorder")
@commands.has_permissions(administrator=True)
async def manual_panel_order(ctx):
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

@manual_panel_order.error
async def panel_order_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Hanya Administrator yang dapat memunculkan panel order!")

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
    print("❌ Token bot tidak ditemukan!")
