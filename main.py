import os, logging, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
PAIR_SERVER = os.environ.get("PAIR_SERVER")
CHAINE_TG = "https://t.me/PhenixGuy"
CHAINE_WA = "https://whatsapp.com/channel/0029Vb8cfQn8V0te5K0atc1s"
OWNER = "𝐆𝐋𝐈𝐓𝐂𝐇 𝐊𝐀𝐘𝐒E𝐔𝐑"
PREFIX = "."

COMMANDS = {
    "🎵 MUSIC": ["play","pause","skip","queue","lyrics","bass","volume","spotify","soundcloud","shazam"],
    "🎬 VIDEO": ["yt","tiktok","insta","fb","twitter","ytshorts","vinfo","compress","trim","convert"],
    "📦 APK": ["apksearch","apkdl","appinfo","apksafe","apkupdate","apkhistory","apklist","apkcheck","apkver","apksize"],
    "🤖 GPT": ["gpt","ask","code","fixcode","explain","translate","rewrite","summarize","idea","email"],
    "💎 GEMINI": ["gemini","gimg","gvision","gcode","gstory","gmath","gsearch","ganalyze","ghelp","gchat"],
    "🧠 CLAUDE": ["claude","cwrite","creview","canalyze","cidea","cemail","cstory","cfix","cexplain","csum"],
    "🎨 STICKER": ["sticker","kang","tosticker","fancy","font1","font2","font3","emojimix","text2img","logo"],
    "👑 ADMIN": ["kick","ban","unban","mute","unmute","pin","unpin","purge","warn","promote"],
    "⚙️ UTILS": ["ping","id","info","help","allmenu","alive","owner","botinfo","uptime","stats"],
    "🔗 PAIR": ["pair"]
}
FLAT = [c for v in COMMANDS.values() for c in v]

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = f"""┏━『 𝐊𝐀𝐘𝐒𝐄𝐔𝐑 𝐌𝐃𝐗 』━┓
┃ ♛ᴛʜᴇ ɢʟɪᴛᴄʜ ᴅᴇᴠ
┃ 🍓 ᴜsᴇʀ : {OWNER}
┃ 🍓 ᴘʀᴇғɪx : {PREFIX}
┃ 🍓 ᴄᴏᴍᴍᴀɴs : ❶⓿⓿
┃ 👨‍💻 ᴏᴡɴᴇʀ : ᴍʀ ᴋɪɴɢ ᴋᴀʏsᴇᴜʀ 
┗━━━━━━━━━━━━━━━┛
𓅂᭄ 𝐏𝐇𝐄𝐍𝐈𝐗 𝐋𝐀𝐁 𓄂᭄"""
    keyboard = [
        [InlineKeyboardButton("🔗 Chaîne Telegram", url=CHAINE_TG)],
        [InlineKeyboardButton("💬 Chaîne WhatsApp", url=CHAINE_WA)]
    ]
    await update.message.reply_photo(photo=open("menu.jpg","rb"), caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

async def allmenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "┏━『 KAYSEUR MDX - 100 COMMANDS 』━┓\n"
    for cat, lst in COMMANDS.items():
        txt += f"\n{cat}\n"
        for c in lst: txt += f"┃ {PREFIX}{c}\n"
    txt += f"\n┗━━━━━━━┛\nTG: {CHAINE_TG}\nWA: {CHAINE_WA}"
    await update.message.reply_text(txt)

async def pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Utilise: .pair 2438xxxxxxxx\nEx: .pair 243812345678")
        return
    number = context.args[0].replace("+","").replace(" ","")
    if not PAIR_SERVER:
        await update.message.reply_text("❌ PAIR_SERVER non configuré sur Deployka")
        return
    await update.message.reply_text(f"⏳ Génération code pour {number}...")
    try:
        r = requests.get(f"{PAIR_SERVER}/pair?number={number}", timeout=25)
        data = r.json()
        if "code" in data:
            await update.message.reply_text(
                f"✅ KAYSEUR MDX PAIR CODE\n\nNuméro: {number}\nCode: *{data['code']}*\n\nWhatsApp > Appareils liés > Lier avec numéro de téléphone > colle ce code\n\nExpire dans 60s",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"❌ {data}")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur serveur: {e}")

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for m in update.message.new_chat_members:
        await update.message.reply_photo(photo=open("welcome.jpg","rb"), caption=f"Bienvenue {m.full_name} dans le meilleur groupe 😇")

async def goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    left = update.message.left_chat_member
    if left:
        await update.message.reply_photo(photo=open("goodbye.jpg","rb"), caption=f"Au revoir {left.full_name} 👋")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler(["menu","start"], menu))
    app.add_handler(CommandHandler("allmenu", allmenu))
    app.add_handler(CommandHandler("pair", pair))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye))
    app.run_polling()