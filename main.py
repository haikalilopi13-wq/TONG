import asyncio
import os
import discord
from discord.ext import commands

# Konfigurasi Intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID Channel milik Anda
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050


@bot.event
async def on_ready():
    print(f"=== BOT ONLINE SEBAGAI {bot.user} ===")
    print("Bot siap melayani HANYA di channel general!")


@bot.event
async def on_message(message):
    # Abaikan jika pesan dikirim oleh bot
    if message.author.bot:
        return

    # Hanya berjalan jika pesan diketik di channel general
    if message.channel.id == GENERAL_CHANNEL_ID:

        # 1. CARI DAN HAPUS PESAN EMBED LAMA MILIK BOT INI SAJA
        try:
            async for old_msg in message.channel.history(limit=15):
                if old_msg.author.id == bot.user.id and len(old_msg.embeds) > 0:
                    await old_msg.delete()
                    await asyncio.sleep(0.5)  # Beri jeda kecil agar proses hapus selesai sempurna
        except Exception as e:
            print(f"Gagal menghapus pesan bot lama: {e}")

        # 2. BUAT EMBED TIKET BARU
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

        # 3. KIRIM EMBED BARU MENTION USER YANG SEDANG CHAT
        await message.channel.send(content=f"{message.author.mention}", embed=embed)

        return

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("ERROR: BOT_TOKEN tidak ditemukan di Environment Variables Railway!")
else:
    bot.run(TOKEN)
