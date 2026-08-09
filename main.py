import asyncio
import os
import discord
from discord.ext import commands

# Konfigurasi Intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID Channel milik Anda (Format Angka Murni)
GENERAL_CHANNEL_ID = 1518084729122062488
TICKET_CHANNEL_ID = 1517625110536786050


@bot.event
async def on_ready():
    print(f"=== BOT ONLINE SEBAGAI {bot.user} ===")
    print("Bot siap melayani HANYA di channel general!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Kunci hanya berjalan di channel general
    if message.channel.id == GENERAL_CHANNEL_ID:

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

        # 1. Kirim embed ke channel general
        await message.channel.send(content=f"{message.author.mention}", embed=embed)

        # 2. Hapus pesan asli dari user setelah 2 detik
        try:
            await asyncio.sleep(2)
            await message.delete()
        except discord.errors.Forbidden:
            print("Bot butuh izin 'Manage Messages' untuk menghapus pesan user.")
        except discord.errors.NotFound:
            pass

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
