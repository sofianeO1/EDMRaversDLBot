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

    status_message = await update.message.reply_text("🔄 Elaborazione traccia in corso... Cerco l'audio migliore.")
    chat_id = update.message.chat_id
    
    # Usiamo un nome file standard senza estensioni forzate da ffmpeg
    output_filename = f"track_{chat_id}.webm" 

    # Configurazione LEGGERA per evitare l'uso di FFmpeg a tutti i costi
        # Configurazione PULITA per scaricare l'audio nativo senza FFmpeg
    ydl_opts = {
        'format': 'bestaudio/best',  # <--- Corretto qui!
        'outtmpl': f"track_{chat_id}.%(ext)s",
        'noplaylist': True,
        'quiet': True,
    }


    try:
        # Usiamo il link di Spotify come chiave di ricerca text-based su YouTube Music/YouTube
        # Questo evita che yt-dlp provi a usare plugin Spotify esterni che falliscono
        search_query = f"ytsearch:{url}"

        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=True))
            # Recuperiamo il nome esatto del file scaricato
            if 'entries' in info and len(info['entries']) > 0:
                filename = ydl.prepare_filename(info['entries'][0])
            else:
                filename = ydl.prepare_filename(info)

        if os.path.exists(filename):
            await status_message.edit_text("📤 File trovato! Invio in corso...")
            
            with open(filename, 'rb') as audio_file:
                # Spediamo come documento audio generico, Telegram lo leggerà come player musicale!
                await update.message.reply_audio(
                    audio=audio_file,
                    caption="Ecco la tua traccia EDM! 🔥🎧"
                )
            
            os.remove(filename)
            await status_message.delete()
        else:
            await status_message.edit_text("❌ Impossibile trovare un flusso audio compatibile.")

    except Exception as e:
        print(f"Errore: {e}")
        await status_message.edit_text("💥 Errore di estrazione. Prova con un'altra traccia.")
        # Pulizia file residui
        for f in os.listdir('.'):
            if f.startswith(f"track_{chat_id}"):
                os.remove(f)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_spotify))

app.run_polling()
