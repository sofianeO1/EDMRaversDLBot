import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 EDM Ravers Bot è online!\n\n"
        "Inviami un link di Spotify e scaricherò l'audio per te! 🔥"
    )

# --- INIZIO FUNZIONE DI CALLBACK ADATTATA PER YT-DLP ---
def my_progress_hook(d):
    """Callback per il progresso del download nativa di yt-dlp."""
    if d['status'] == 'downloading':
        # Ottieni il blocco/chunk di dati corrente (convertito in stringa per il controllo)
        chunk_str = str(d.get('filename', '')) + str(d.get('tmpfilename', ''))
        
        # Il controllo personalizzato che hai richiesto per ignorare l'errore DRM
        if "ERROR: [DRM]" in chunk_str or "DRM" in chunk_str:
            print("Ignoring DRM error...")
            return
    
    if d['status'] == 'finished':
        print("Download completato sul server, inizio conversione...")
# --- FINE FUNZIONE DI CALLBACK ---

async def download_spotify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if "spotify.com" not in url:
        await update.message.reply_text("❌ Per favore, inviami un link valido di Spotify.")
        return

    status_message = await update.message.reply_text("🔄 Download in corso direttamente dal server cloud...")
    chat_id = update.message.chat_id

    # Configurazione con l'aggiunta del progress_hook richiesto
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"track_{chat_id}.%(ext)s",
        'noplaylist': True,
        'quiet': True,
        'default_search': 'scsearch',  # Forza la ricerca su SoundCloud
        'progress_hooks': [my_progress_hook],  # <--- Inserita la funzione di controllo qui
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Passiamo il link: yt-dlp cercherà il brano su SoundCloud
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            
            if 'entries' in info:
                filename = ydl.prepare_filename(info['entries'][0])
                title = info['entries'][0].get('title', 'EDM Track')
            else:
                filename = ydl.prepare_filename(info)
                title = info.get('title', 'EDM Track')

        if os.path.exists(filename):
            await status_message.edit_text("📤 File recuperato! Invio alla chat...")
            
            with open(filename, 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    title=title,
                    caption="Ecco la tua traccia EDM! 🔥🎧"
                )
            
            os.remove(filename)
            await status_message.delete()
        else:
            await status_message.edit_text("❌ Errore nel salvataggio del file sul server.")

    except Exception as e:
        print(f"Errore: {e}")
        await status_message.edit_text("💥 Il server ha rifiutato la richiesta. Prova con un'altra traccia.")
        for f in os.listdir('.'):
            if f.startswith(f"track_{chat_id}"):
                os.remove(f)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_spotify))

app.run_polling()
