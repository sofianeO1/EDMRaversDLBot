import os
import asyncio
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

TOKEN = os.getenv("BOT_TOKEN")

# Inizializzazione Spotify Leggera (Usa credenziali anonime/pubbliche per i metadati)
auth_manager = SpotifyClientCredentials(
    client_id=os.getenv("SPOTIPY_CLIENT_ID", "3f17ef4b91014e77840130d2203254b1"), # Credenziale pubblica di fallback per i titoli
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET", "5cc6411be07246b9b3e10fa658d5162f")
)
sp = spotipy.Spotify(auth_manager=auth_manager)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 EDM Ravers Bot è online!\n\n"
        "Inviami un link di Spotify e scaricherò l'audio per te! 🔥"
    )

def get_spotify_track_name(url):
    try:
        # Estrae l'ID della traccia dal link
        track_id = re.search(r"track/([a-zA-Z0-9]+)", url).group(1)
        track = sp.track(track_id)
        # Unisce Artista + Titolo (es: "Basswell - Massive Attack")
        return f"{track['artists'][0]['name']} - {track['name']}"
    except Exception:
        return None

async def download_spotify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if "spotify.com" not in url:
        await update.message.reply_text("❌ Per favore, inviami un link valido di Spotify.")
        return

    status_message = await update.message.reply_text("🔄 Identificazione brano su Spotify...")
    
    # 1. Ottieni il titolo pulito della canzone
    loop = asyncio.get_event_loop()
    track_name = await loop.run_in_executor(None, get_spotify_track_name, url)
    
    if not track_name:
        await status_message.edit_text("❌ Impossibile leggere i dettagli da questo link Spotify.")
        return

    await status_message.edit_text(f"🔍 Cerco il flusso audio per:\n*_{track_name}_*...", parse_mode="Markdown")
    chat_id = update.message.chat_id

    # 2. Configurazione di download audio nativo (Zero FFmpeg richiesto)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"track_{chat_id}.%(ext)s",
        'noplaylist': True,
        'quiet': True,
    }

    try:
        # Cerca su YouTube usando il TITOLO PULITO, non il link!
        search_query = f"ytsearch:{track_name}"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_query, download=True))
            if 'entries' in info and len(info['entries']) > 0:
                filename = ydl.prepare_filename(info['entries'][0])
            else:
                filename = ydl.prepare_filename(info)

        if os.path.exists(filename):
            await status_message.edit_text("📤 Invio dell'audio in corso...")
            
            with open(filename, 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    title=track_name,
                    caption="Ecco la tua traccia EDM! 🔥🎧"
                )
            
            os.remove(filename)
            await status_message.delete()
        else:
            await status_message.edit_text("❌ Download fallito. Il flusso audio non è stato salvato.")

    except Exception as e:
        print(f"Errore: {e}")
        await status_message.edit_text("💥 Errore durante il download dal server cloud.")
        for f in os.listdir('.'):
            if f.startswith(f"track_{chat_id}"):
                os.remove(f)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_spotify))

app.run_polling()
