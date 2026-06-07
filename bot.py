import os
import asyncio
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 EDM Ravers Bot è online!\n\n"
        "Inviami un link di Spotify (traccia singola) e proverò a scaricarlo in MP3 per te! 🔥"
    )

async def download_spotify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if "spotify.com" not in url:
        await update.message.reply_text("❌ Per favore, inviami un link valido di Spotify.")
        return

    status_message = await update.message.reply_text("🔄 Sto scaricando la traccia... Un attimo di pazienza.")
    
    chat_id = update.message.chat_id
    output_filename = f"track_{chat_id}.mp3"

    try:
        if os.path.exists(output_filename):
            os.remove(output_filename)

        # Avviamo il processo di spotdl
        process = await asyncio.create_subprocess_exec(
            'spotdl', 'download', url, '--output', output_filename,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        await process.communicate()

        if os.path.exists(output_filename):
            await status_message.edit_text("📤 Download completato! Invio l'MP3...")
            
            with open(output_filename, 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    caption="Ecco la tua traccia! 🎧"
                )
            
            os.remove(output_filename)
            await status_message.delete()
        else:
            await status_message.edit_text("❌ Impossibile scaricare il brano. Verifica che sia una traccia singola.")

    except Exception as e:
        print(f"Errore: {e}")
        await status_message.edit_text("💥 Si è verificato un errore durante il download.")
        if os.path.exists(output_filename):
            os.remove(output_filename)

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_spotify))

app.run_polling()
