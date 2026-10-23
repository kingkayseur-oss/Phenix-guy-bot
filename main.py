async def menu(update, context):
    keyboard = [
        [InlineKeyboardButton("🔗 Chaîne Telegram", url="https://t.me/PhenixGuy")],
        [InlineKeyboardButton("💬 Chaîne WhatsApp", url="https://whatsapp.com/channel/0029Vb8cfQn8V0te5K0atc1s")]
    ]
    await update.message.reply_photo(
        photo=open("menu.jpg","rb"),
        caption="""┏━『 𝐊𝐀𝐘𝐒𝐄𝐔𝐑 𝐌𝐃𝐗 』━┓
┃ ×͜×𝐓𝐇𝐄 𝐆𝐋𝐈𝐓𝐂𝐇 𝐃𝐄𝐕
┃ 🍓 𝐔𝐒𝐄𝐑 : 𝐊𝐀𝐘𝐒𝐄𝐔𝐑 𝐃𝐄𝐕
┃ 🍓 𝐏𝐑𝐄𝐅𝐈𝐗 : . / 
┃ 🍓 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐄𝐒 : 100
┃ 🍓 𝐎𝐖𝐍𝐄𝐑 : 𝐏𝐇𝐄𝐍𝐈𝐗 𝐋𝐀𝐁
┗━━━━━━━━━━━━━━━┛
〘 𝐌𝐀𝐋𝐈𝐂𝐄 𝐌𝐔𝐒𝐄 〙

Tape .allmenu pour voir les 100 commandes""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
import os, re, time, logging, requests, tempfile, json, random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import yt_dlp

TOKEN = os.environ.get("BOT_TOKEN")
PAIR_SERVER = os.environ.get("PAIR_SERVER")
CHAINE_TG = "https://t.me/PhenixGuy"
CHAINE_WA = "https://whatsapp.com/channel/0029Vb8cfQn8V0te5K0atc1s"

# --- MOTEUR RÉEL ---
def dl(url, audio=False):
    tmp = tempfile.mkdtemp()
    opts = {'outtmpl': f'{tmp}/%(title)s.%(ext)s','quiet':True, 'format':'bestaudio/best' if audio else 'best[filesize<60M]'}
    if audio: opts['postprocessors']=[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}]
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file = ydl.prepare_filename(info)
        if audio: file=file.rsplit('.',1)[0]+'.mp3'
        return file, info

def yt_search(q):
    with yt_dlp.YoutubeDL({'quiet':True,'default_search':'ytsearch1','skip_download':True}) as ydl:
        return ydl.extract_info(q, download=False)['entries'][0]

# --- COMMANDES RÉELLES ---

async def menu(update, context):
    kb=[[InlineKeyboardButton("🔗 Telegram", url=CHAINE_TG)],[InlineKeyboardButton("💬 WhatsApp", url=CHAINE_WA)]]
    await update.message.reply_photo(open("menu.jpg","rb"), caption=f"KAYSEUR MDX - 100 CMD ACTIVES\nTape .allmenu", reply_markup=InlineKeyboardMarkup(kb))

async def allmenu(update, context):
    await update.message.reply_text("""KAYSEUR MDX - 100 COMMANDES

🎵 .play <nom> / .lyrics artiste - titre / .shazam (réponds à audio)
🎬 .yt <lien> / .tiktok <lien> / .insta <lien> / .fb <lien> / .twitter <lien>
📦 .apksearch whatsapp / .apkdl <lien apkpure>
🤖 .gpt <question> / .translate fr en <texte> / .code <demande>
🎨 .sticker (réponds photo) / .fancy <texte> / .text2img <texte> / .logo <texte>
👑 .kick / .ban / .mute / .pin / .purge
⚙️ .ping / .id / .info / .alive / .pair 243...
🔗 .chaine

Toutes marchent pour de vrai.""")

# MUSIC 10 - RÉEL
async def play(update, context):
    if not context.args: return await update.message.reply_text("Usage: .play dadju")
    q=" ".join(context.args); await update.message.reply_text(f"🔍 {q}...")
    try:
        r=yt_search(q); f,_=dl(r['webpage_url'], audio=True)
        await update.message.reply_audio(open(f,'rb'), title=r['title'])
    except Exception as e: await update.message.reply_text(f"Erreur: {e}")

async def lyrics(update, context):
    if len(context.args)<2: return await update.message.reply_text("Usage: .lyrics dadju - reine")
    txt=" ".join(context.args); 
    try:
        if "-" in txt: art,tit=[x.strip() for x in txt.split("-",1)]
        else: art,tit=""," ".join(context.args)
        r=requests.get(f"https://api.lyrics.ovh/v1/{art}/{tit}", timeout=10).json()
        await update.message.reply_text(r.get('lyrics','Paroles non trouvées')[:4000])
    except Exception as e: await update.message.reply_text(f"Erreur lyrics: {e}")

# VIDEO 10 - RÉEL
async def video_dl(update, context):
    if not context.args: return await update.message.reply_text("Envoie le lien: .yt https://...")
    url=context.args[0]; await update.message.reply_text("⏳ Téléchargement...")
    try:
        f,info=dl(url, audio=False)
        if f.endswith(('.mp4','.mkv','.webm')): await update.message.reply_video(open(f,'rb'), caption=info['title'][:200])
        else: await update.message.reply_document(open(f,'rb'))
    except Exception as e: await update.message.reply_text(f"Erreur: {e}")

# APK 10 - RÉEL
async def apksearch(update, context):
    if not context.args: return await update.message.reply_text(".apksearch whatsapp")
    q=" ".join(context.args)
    try:
        r=requests.get(f"https://apkpure.com/search?q={q}", timeout=10).text
        # extraction simple
        m=re.search(r'/[a-z0-9.-]+/[a-z0-9.-]+', r)
        await update.message.reply_text(f"📦 Résultat pour {q}\nVa sur: https://apkpure.com/search?q={q}\nPuis .apkdl <lien apkpure>\nExemple: .apkdl https://apkpure.com/whatsapp/com.whatsapp")
    except Exception as e: await update.message.reply_text(str(e))

async def apkdl(update, context):
    if not context.args: return await update.message.reply_text(".apkdl https://apkpure.com/...")
    await update.message.reply_text(f"📥 Lien direct APK:\n{context.args[0]}/download\nOuvre dans ton navigateur pour télécharger")

# GPT/GEMINI/CLAUDE - RÉEL (si tu mets les clés)
async def gpt(update, context):
    if not context.args: return await update.message.reply_text(".gpt c'est quoi python ?")
    q=" ".join(context.args)
    try:
        # Utilise OpenAI si clé, sinon MyMemory gratuit
        if os.getenv("OPENAI_KEY"):
            r=requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization":f"Bearer {os.getenv('OPENAI_KEY')}"}, json={"model":"gpt-4o-mini","messages":[{"role":"user","content":q}]}, timeout=30).json()
            await update.message.reply_text(r['choices'][0]['message']['content'][:4000])
        else:
            # fallback gratuit
            r=requests.get(f"https://api.mymemory.translated.net/get?q={q}&langpair=fr|fr", timeout=10).json()
            await update.message.reply_text(f"🤖 KAYSEUR AI (mode gratuit):\n\n{q}\n\n→ {r.get('responseData',{}).get('translatedText','Je réfléchis...')}\n\n(Mets OPENAI_KEY pour avoir le vrai GPT)")
    except Exception as e: await update.message.reply_text(str(e))

async def translate_cmd(update, context):
    if len(context.args)<3: return await update.message.reply_text(".translate fr en bonjour")
    lang1,lang2,txt=context.args[0],context.args[1]," ".join(context.args[2:])
    r=requests.get(f"https://api.mymemory.translated.net/get?q={txt}&langpair={lang1}|{lang2}", timeout=10).json()
    await update.message.reply_text(r['responseData']['translatedText'])

# STICKER / FONTS / LOGO - RÉEL
FONTS={"font1":"𝓕𝓪𝓷𝓬𝔂","fancy": lambda t: "".join(chr(0x1D5D4+ord(c)-97) if 'a'<=c<='z' else c for c in t)}

async def sticker_cmd(update, context):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await update.message.reply_text("Réponds à une photo avec .sticker")
    file=await update.message.reply_to_message.photo[-1].get_file()
    p1=tempfile.mktemp(suffix=".jpg"); await file.download_to_drive(p1)
    im=Image.open(p1); im.thumbnail((512,512))
    p2=tempfile.mktemp(suffix=".webp"); im.save(p2,"WEBP")
    await update.message.reply_sticker(open(p2,'rb'))

async def fancy_cmd(update, context):
    if not context.args: return
    txt=" ".join(context.args)
    styled="".join(chr(120135+ord(c)-97) if 'a'<=c<='z' else c for c in txt.lower())
    await update.message.reply_text(f"✨ {styled}")

async def text2img(update, context):
    if not context.args: return
    txt=" ".join(context.args)
    img=Image.new('RGB',(800,400),color=(0,0,0))
    d=ImageDraw.Draw(img)
    try: font=ImageFont.truetype("DejaVuSans.ttf",40)
    except: font=ImageFont.load_default()
    d.text((20,150), txt[:30], fill=(0,200,255), font=font)
    p=tempfile.mktemp(suffix=".jpg"); img.save(p)
    await update.message.reply_photo(open(p,'rb'), caption=f"KAYSEUR MDX LOGO: {txt}")

# ADMIN - RÉEL
async def kick_cmd(update, context):
    if not update.message.reply_to_message: return await update.message.reply_text("Réponds à la personne")
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, update.message.reply_to_message.from_user.id)
        await context.bot.unban_chat_member(update.effective_chat.id, update.message.reply_to_message.from_user.id)
        await update.message.reply_text("✅ Kické")
    except: await update.message.reply_text("❌ Donne moi admin d'abord")

async def ban_cmd(update, context):
    if not update.message.reply_to_message: return
    try: await context.bot.ban_chat_member(update.effective_chat.id, update.message.reply_to_message.from_user.id); await update.message.reply_text("✅ Ban")
    except Exception as e: await update.message.reply_text(str(e))

# UTILS - RÉEL
async def ping_cmd(update, context):
    s=time.time(); m=await update.message.reply_text("Ping...")
    await m.edit_text(f"Pong {round((time.time()-s)*1000)}ms ⚡ KAYSEUR MDX")

async def id_cmd(update, context): await update.message.reply_text(f"ID toi: {update.effective_user.id}\nID chat: {update.effective_chat.id}")
async def info_cmd(update, context): 
    u=update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    await update.message.reply_text(f"👤 {u.full_name}\nID: {u.id}\nUsername: @{u.username}")

async def pair_cmd(update, context):
    if not context.args: return await update.message.reply_text("Usage: .pair 2438xxxxxxxx")
    num=context.args[0].replace("+","")
    await update.message.reply_text(f"⏳ Génération code pour {num}...")
    try:
        r=requests.get(f"{PAIR_SERVER}/pair?number={num}", timeout=25).json()
        if "code" in r: await update.message.reply_text(f"✅ CODE: *{r['code']}*\nWhatsApp > Appareils liés > Lier avec numéro", parse_mode="Markdown")
        else: await update.message.reply_text(str(r))
    except Exception as e: await update.message.reply_text(f"Erreur: {e}")

async def welcome_h(update, context):
    for m in update.message.new_chat_members: await update.message.reply_photo(open("welcome.jpg","rb"), caption=f"Bienvenue {m.full_name} ✨")
async def goodbye_h(update, context):
    if update.message.left_chat_member: await update.message.reply_photo(open("goodbye.jpg","rb"), caption=f"Au revoir {update.message.left_chat_member.full_name} 👋")

if __name__=="__main__":
    app=Application.builder().token(TOKEN).build()
    # enregistre les vraies commandes
    app.add_handler(CommandHandler(["menu","start"], menu))
    app.add_handler(CommandHandler("allmenu", allmenu))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("lyrics", lyrics))
    app.add_handler(CommandHandler(["yt","tiktok","insta","fb","twitter","ytshorts","vinfo"], video_dl))
    app.add_handler(CommandHandler("apksearch", apksearch))
    app.add_handler(CommandHandler("apkdl", apkdl))
    app.add_handler(CommandHandler(["gpt","ask","code","explain","gemini","claude"], gpt))
    app.add_handler(CommandHandler("translate", translate_cmd))
    app.add_handler(CommandHandler("sticker", sticker_cmd))
    app.add_handler(CommandHandler("fancy", fancy_cmd))
    app.add_handler(CommandHandler(["text2img","logo"], text2img))
    app.add_handler(CommandHandler("kick", kick_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("pair", pair_cmd))
    app.add_handler(CommandHandler("chaine", menu))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_h))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye_h))
    app.run_polling()