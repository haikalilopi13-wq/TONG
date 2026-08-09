import asyncio
import datetime
import os
import discord
from discord.ext import commands

# Konfigurasi Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Wajib aktif untuk TO/Kick/Ban

bot = commands.Bot(command_prefix="!", intents=intents)

# ID Channel milik Anda
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050


@bot.event
async def on_ready():
    print(f"=== BOT ONLINE SEBAGAI {bot.user} ===")
    print("Bot siap melayani HANYA di channel general & menjalankan perintah Admin!")


@bot.event
async def on_message(message):
    # Abaikan jika pesan dikirim oleh bot
    if message.author.bot:
        return

    # 1. Jika pesan diawali dengan prefix perintah (contoh: !to, !ban, !kick, !clear)
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # 2. Respon otomatis tiket hanya jika obrolan biasa diketik di channel general
    if message.channel.id == GENERAL_CHANNEL_ID:

        # Cari dan hapus pesan embed lama milik bot ini
        try:
            async for old_msg in message.channel.history(limit=15):
                if old_msg.author.id == bot.user.id and len(old_msg.embeds) > 0:
                    await old_msg.delete()
                    await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Gagal menghapus pesan bot lama: {e}")

        # Buat Embed Tiket
        embed = discord.Embed(
            title="👋 TONGSOP DI SINI! 👋",
            description="Halo! Untuk keamanan dan kenyamanan bertransaksi, silakan gunakan jalur resmi yang telah kami sediakan untuk melayani Anda :",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="🛒 Pembelian Produk Prenstore",
            value=f"• <#{TICKET_CHANNEL_ID}> • ` open-ticket `",
            inline=False,
        )

        embed.add_field(
            name="👥 Layanan jasa split Redfinger",
            value=f"• <#{TICKET_CHANNEL_ID}> • ` jasa split `",
            inline=False,
        )

        embed.add_field(
            name="📄 Note",
            value="• Harap tidak melakukan transaksi di luar tiket resmi demi keamanan Anda.\n• Tim Admin Prenstore akan merespons tiket Anda sesegera mungkin.",
            inline=False,
        )

        embed.set_footer(text="TONGSOP Assistant • Klik channel tiket di atas")

        # Kirim Embed Baru
        await message.channel.send(content=f"{message.author.mention}", embed=embed)
        return

    await bot.process_commands(message)


# ==================== PERINTAH ADMIN (COMMANDS) ====================


# 1. Perintah TIMEOUT / TO
@bot.command(name="to", aliases=["timeout"])
@commands.has_permissions(moderate_members=True)
async def timeout_member(
    ctx,
    member: discord.Member,
    minutes: int = 10,
    *,
    reason: str = "Tidak ada alasan yang diberikan.",
):
    """Memberikan Timeout/Mute sementara ke member. Contoh: !to @user 10 Toxic"""
    try:
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(
            f"🤐 **{member.name}** berhasil di-timeout selama **{minutes} menit**. Alasan: {reason}"
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan timeout: {e}")


# 2. Perintah UNTIMEOUT / UNTO
@bot.command(name="unto", aliases=["untimeout"])
@commands.has_permissions(moderate_members=True)
async def untimeout_member(ctx, member: discord.Member):
    """Membatalkan Timeout/Mute member. Contoh: !unto @user"""
    try:
        await member.timeout(None)
        await ctx.send(
            f"🔊 Timeout untuk **{member.name}** telah dicabut!"
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal menghapus timeout: {e}")


# 3. Perintah BAN
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban_member(
    ctx,
    member: discord.Member,
    *,
    reason: str = "Tidak ada alasan yang diberikan.",
):
    """Memblokir member dari server. Contoh: !ban @user Spammer"""
    try:
        await member.ban(reason=reason)
        await ctx.send(
            f"✅ **{member.name}** berhasil di-ban dari server. Alasan: {reason}"
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan ban: {e}")


# 4. Perintah KICK
@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick_member(
    ctx,
    member: discord.Member,
    *,
    reason: str = "Tidak ada alasan yang diberikan.",
):
    """Mengeluarkan member dari server. Contoh: !kick @user Melanggar aturan"""
    try:
        await member.kick(reason=reason)
        await ctx.send(
            f"✅ **{member.name}** berhasil di-kick dari server. Alasan: {reason}"
        )
    except Exception as e:
        await ctx.send(f"❌ Gagal melakukan kick: {e}")


# 5. Perintah CLEAR (Hapus Pesan)
@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 5):
    """Menghapus sejumlah pesan. Contoh: !clear 10"""
    deleted = await ctx.channel.purge(
        limit=amount + 1
    )  # +1 untuk menghapus pesan !clear itu sendiri
    msg = await ctx.send(f"🧹 Berhasil menghapus {len(deleted)-1} pesan.")
    await asyncio.sleep(3)
    await msg.delete()


# Error Handling
@timeout_member.error
@untimeout_member.error
@ban_member.error
@kick_member.error
@clear_messages.error
async def command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Anda tidak memiliki izin untuk menggunakan perintah ini!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            "⚠️ Format salah! Gunakan perintah seperti contoh:\n`!to @user 10 Toxic` atau `!unto @user`"
        )


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("ERROR: BOT_TOKEN tidak ditemukan di Environment Variables Railway!")
else:
    bot.run(TOKEN)
