import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 EDM Ravers Bot è online!\n\n"
        "Inviami un link di Spotify e cercherò l'audio per te! 🔥"
    )

def my_progress_hook(d):
    """Callback per monitorare il download ed evitare blocchi DRM."""
    if d['status'] == 'downloading':
        chunk_str = str(d.get('filename', '')) + str(d.get('tmpfilename', ''))
        if "ERROR: [DRM]" in chunk_str or "DRM" in chunk_str:
            print("Ignoring DRM error...")
            return

async def download_spotify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    # CONTROLLO CORRETTO: Verifica che sia un link Spotify valido
    if "spotify.com" not in url:
        await update.message.reply_text("❌ Per favore, inviami un link valido di Spotify.")
        return

    status_message = await update.message.reply_text("🔄 Elaborazione e ricerca della traccia in corso...")
    chat_id = update.message.chat_id

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"track_{chat_id}.%(ext)s",
        'noplaylist': True,
        'quiet': True,
        'default_search': 'scsearch',  # Cerca su SoundCloud per evitare i DRM nativi
        'progress_hooks': [my_progress_hook],
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            
            if 'entries' in info:
                filename = ydl.prepare_filename(info['entries'][0])
                title = info['entries'][0].get('title', 'EDM Track')
            else:
                filename = ydl.prepare_filename(info)
                title = info.get('title', 'EDM Track')

        if os.path.exists(filename):
            await status_message.edit_text("📤 File recuperato! Invio in corso...")
            
            with open(filename, 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    title=title,
                    caption="Ecco la tua traccia! 🔥🎧"
                )
            
            os.remove(filename)
            await status_message.delete()
        else:
            await status_message.edit_text("❌ Errore nel salvataggio del file sul server.")

    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")
        await status_message.edit_text("💥 Il server ha rifiutato la richiesta o brano non trovato. Prova con un'altra traccia.")
        for f in os.listdir('.'):
            if f.startswith(f"track_{chat_id}"):
                os.remove(f)

# Inizializzazione dell'applicazione
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_spotify))

if __name__ == '__main__':
    app.run_polling()
