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
    print("🚀 Bot siap dengan Sistem Ganda & Tombol Terpisah (Close & Rating)!")

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

# ==================== VIEW PILIHAN BINTANG RATING ====================
class RatingChoiceView(discord.ui.View):
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
        testi_embed.add_field(name="🛠️ Dinilai Oleh", value=interaction.user.mention, inline=False)
        testi_embed.set_footer(text=f"TONGSOP Store • {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")

        if testi_channel:
            try:
                await testi_channel.send(embed=testi_embed)
            except Exception:
                pass

        await interaction.response.send_message("✨ Terima kasih atas ratingnya! Testimoni telah dikirim ke channel testi.", ephemeral=True)

    @discord.ui.button(label="⭐ 5 (Sangat Puas)", style=discord.ButtonStyle.green)
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_testimoni(interaction, "⭐⭐⭐⭐⭐ (Sangat Puas)", 0x2ECC71)

    @discord.ui.button(label="⭐ 3 (Cukup)", style=discord.ButtonStyle.blurple)
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_testimoni(interaction, "⭐⭐⭐ (Cukup)", 0x3498DB)

    @discord.ui.button(label="⭐ 1 (Kurang)", style=discord.ButtonStyle.red)
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_testimoni(interaction, "⭐ (Kurang)", 0xE74C3C)

# ==================== TOMBOL KONTROL TERPISAH (CLOSE & RATING) ====================
class TicketControlView(discord.ui.View):
    def __init__(self, ticket_opener: discord.Member):
        super().__init__(timeout=None)
        self.ticket_opener = ticket_opener

    # Tombol 1: Khusus Close Ticket (Bisa ditekan Pembuat Tiket atau Staf)
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn_only")
    async def close_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ticket_opener and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Hanya pembuat tiket atau staf yang dapat menutup tiket ini!", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Tiket ini akan ditutup dan dihapus dalam 5 detik...", ephemeral=False)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason="Tiket ditutup oleh user/staf.")
        except Exception:
            pass

    # Tombol 2: Khusus Memberi Rating
    @discord.ui.button(label="⭐ Beri Rating", style=discord.ButtonStyle.success, custom_id="rate_ticket_btn_only")
    async def rate_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ticket_opener and not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Hanya pembuat tiket yang dapat memberikan rating!", ephemeral=True)
            return

        embed = discord.Embed(
            title="⭐ PILIH RATING PELAYANAN",
            description="Silakan pilih tingkat kepuasan Anda di bawah ini:",
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

        guild = interaction.guild
        member = interaction.user

        category = guild.get_channel(TARGET_CATEGORY_OR_PARENT_ID)
        channel_name = f"ticket-{member.name}".lower()

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        try:
            if isinstance(category, discord.CategoryChannel):
                ticket_channel = await guild.create_text_channel(
                    name=channel_name, 
                    category=category, 
                    overwrites=overwrites
                )
            else:
                ticket_channel = await guild.create_text_channel(
                    name=channel_name, 
                    overwrites=overwrites
                )

            ticket_embed = discord.Embed(
                title="🎟️ TIKET PEMESANAN BARU",
                description=f"Halo {member.mention}, pesanan Anda telah diterima dan tiket berhasil dibuat!\n\nMohon tunggu sebentar, staf kami akan segera melayani Anda.",
                color=0x3498DB
            )
            ticket_embed.add_field(name="📦 Mau Beli", value=produk, inline=False)
            ticket_embed.add_field(name="🔢 Jumlah", value=jml, inline=False)
            ticket_embed.add_field(name="👤 Roblox Username", value=roblox_name, inline=False)
            ticket_embed.set_footer(text="Gunakan tombol di bawah untuk memberi rating atau menutup tiket.")

            await ticket_channel.send(
                content=f"{member.mention}", 
                embed=ticket_embed, 
                view=TicketControlView(member)
            )

            await interaction.response.send_message(
                f"✅ Formulir berhasil dikirim! Channel tiket Anda telah dibuat di: {ticket_channel.mention}",
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Terjadi kesalahan saat membuat channel tiket: {e}",
                ephemeral=True
            )

# ==================== FORMULIR REDFINGER (SPLIT MODAL) ====================
class RedfingerModal(discord.ui.Modal, title="SET UP REDFINGER"):
    paket = discord.ui.TextInput(
        label="Paket Redfinger",
        placeholder="Contoh: KVIP / VIP / Standard",
        style=discord.TextStyle.short,
        required=True
    )
    
    jumlah_split = discord.ui.TextInput(
        label="Berapa Slot Split?",
        placeholder="Contoh: 5 Slot / 10 Slot",
        style=discord.TextStyle.short,
        required=True
    )
    
    username_roblox = discord.ui.TextInput(
        label="User Name Roblox / Catatan",
        placeholder="Masukkan username atau catatan tambahan",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        pkt = self.paket.value
        jml = self.jumlah_split.value
        catatan = self.username_roblox.value

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
                ticket_channel = await guild.create_text_channel(
                    name=channel_name, 
                    category=category, 
                    overwrites=overwrites
                )
            else:
                ticket_channel = await guild.create_text_channel(
                    name=channel_name, 
                    overwrites=overwrites
                )

            ticket_embed = discord.Embed(
                title="📱 TIKET SET UP REDFINGER",
                description=f"Halo {member.mention}, pesanan jasa split Redfinger Anda telah diterima!",
                color=0xE67E22
            )
            ticket_embed.add_field(name="📦 Paket", value=pkt, inline=False)
            ticket_embed.add_field(name="🔢 Jumlah Slot Split", value=jml, inline=False)
            ticket_embed.add_field(name="📝 Catatan / User", value=catatan, inline=False)
            ticket_embed.set_footer(text="Gunakan tombol di bawah untuk memberi rating atau menutup tiket.")

            await ticket_channel.send(
                content=f"{member.mention}", 
                embed=ticket_embed, 
                view=TicketControlView(member)
            )

            await interaction.response.send_message(
                f"✅ Formulir Redfinger terkirim! Channel tiket Anda: {ticket_channel.mention}",
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Terjadi kesalahan: {e}",
                ephemeral=True
            )

# ==================== VIEW TOMBOL BERDAMPINGAN ====================
class BuyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛒 Buka Form Pembelian", style=discord.ButtonStyle.green, custom_id="open_buy_modal_persistent")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BuyModal())

    @discord.ui.button(label="📱 Set Up Redfinger", style=discord.ButtonStyle.blurple, custom_id="open_redfinger_modal_persistent")
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
        name="🛡️ Moderasi, Admin & Tiket",
        value="`.panelorder` — Mengirim panel form pembelian & redfinger\n"
              "`.clear` / `.cls` — Menghapus pesan\n"
              "`.closeticket` / `.done` — Menutup tiket\n"
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
async def close_ticket(ctx, member: discord.Member = None):
    target_member = member or ctx.author 

    embed = discord.Embed(
        title="🔒 TIKET SELESAI / DITUTUP",
        description=f"Terima kasih {target_member.mention} telah memesan di **TONGSOP Store**.",
        color=0xF1C40F
    )
    embed.set_footer(text="Tiket ini ditutup oleh staf.")
    await ctx.send(embed=embed)
    await asyncio.sleep(3)
    try:
        await ctx.channel.delete()
    except Exception:
        pass

@close_ticket.error
async def closeticket_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Kamu tidak memiliki izin untuk menutup tiket!")

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
