import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 EDM Ravers Bot è online!\n\n"
        "Inviami un link di Spotify e cercherò di scaricare l'MP3 per te! 🔥"
    )

async def download_spotify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if "spotify.com" not in url:
        await update.message.reply_text("❌ Per favore, inviami un link valido di Spotify.")
        return

    status_message = await update.message.reply_text("🔄 Elaborazione traccia in corso... Un attimo di pazienza.")
    chat_id = update.message.chat_id
    output_filename = f"track_{chat_id}"
    final_mp3 = f"{output_filename}.mp3"

    # Configurazione di yt-dlp per scaricare solo l'audio in MP3
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_filename,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        # Questo forza l'uso di ffprobe/ffmpeg integrato se presente o salta errori di sistema
        'quiet': True,
    }

    try:
        if os.path.exists(final_mp3):
            os.remove(final_mp3)

        # Utilizziamo yt-dlp per cercare ed estrarre l'audio usando il link spotify come ricerca testuale o diretta
        # Nota: yt-dlp cercherà in automatico l'equivalente audio migliore
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Eseguiamo il download in modo non bloccante
            await loop.run_in_executor(None, lambda: ydl.download([url]))

        if os.path.exists(final_mp3):
            await status_message.edit_text("📤 Download completato! Invio l'MP3...")
            
            with open(final_mp3, 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    caption="Ecco la tua traccia EDM! 🔥🎧"
                )
            
            os.remove(final_mp3)
            await status_message.delete()
        else:
            await status_message.edit_text("❌ Impossibile convertire il brano. Riprova tra un attimo.")

    except Exception as e:
        print(f"Errore: {e}")
        await status_message.edit_text("💥 Errore durante l'estrazione audio su Railway.")
        if os.path.exists(final_mp3):
            os.remove(final_mp3)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_spotify))

app.run_polling()
