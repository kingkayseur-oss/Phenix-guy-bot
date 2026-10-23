import os, time, requests, tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from PIL import Image
import yt_dlp

TOKEN=os.environ.get("BOT_TOKEN")
PAIR_SERVER=os.environ.get("PAIR_SERVER")
NAME="𝆭🍓𝂅‌𝐏̤𝐇ׄ͟𝐄ֵᩘ𝐍ֿ‌︬𝐈𝐗ֺ࡙ࣨ͟×͜×𝐆ִֵ𝐔⃪ֺ𐇽𝐘⃪⃪ׅ֩ 🛀˙𝂅‌‌"
TG="https://t.me/PhenixGuy"
WA="https://whatsapp.com/channel/0029Vb8cfQn8V0te5K0atc1s"

def dl(url,audio=False):
    tmp=tempfile.mkdtemp()
    opts={'outtmpl':f'{tmp}/%(title)s.%(ext)s','quiet':True,'format':'bestaudio/best' if audio else 'best[filesize<60M]'}
    if audio: opts['postprocessors']=[{'key':'FFmpegExtractAudio','preferredcodec':'mp3'}]
    with yt_dlp.YoutubeDL(opts) as ydl:
        info=ydl.extract_info(url,download=True)
        file=ydl.prepare_filename(info)
        if audio: file=file.rsplit('.',1)[0]+'.mp3'
        return file,info

def yt_search(q):
    with yt_dlp.YoutubeDL({'quiet':True,'default_search':'ytsearch1','skip_download':True}) as ydl:
        return ydl.extract_info(q,download=False)['entries'][0]

async def menu(update,context):
    kb=[[InlineKeyboardButton("🔗 Telegram",url=TG)],[InlineKeyboardButton("💬 WhatsApp",url=WA)]]
    await update.message.reply_photo(open("menu.jpg","rb"),caption=f"┏━『 KAYSEUR MDX - {NAME} 』━┓\n100 CMD ACTIVES",reply_markup=InlineKeyboardMarkup(kb))

async def allmenu(update,context):
    await update.message.reply_text(f"{NAME} - 100 CMD\n.play .yt .tiktok .apksearch .sticker .kick .ban .ping .pair etc")

async def play(update,context):
    q=" ".join(context.args); r=yt_search(q); f,_=dl(r['webpage_url'],True); await update.message.reply_audio(open(f,'rb'))

async def yt_cmd(update,context):
    f,i=dl(context.args[0],False); await update.message.reply_video(open(f,'rb'))

async def sticker_cmd(update,context):
    file=await update.message.reply_to_message.photo[-1].get_file(); p1=tempfile.mktemp(suffix=".jpg"); await file.download_to_drive(p1)
    im=Image.open(p1); im.thumbnail((512,512)); p2=tempfile.mktemp(suffix=".webp"); im.save(p2,"WEBP")
    await update.message.reply_sticker(open(p2,'rb'))

async def ping(update,context):
    s=time.time(); m=await update.message.reply_text("Ping..."); await m.edit_text(f"Pong {round((time.time()-s)*1000)}ms ⚡ {NAME}")

async def pair_cmd(update,context):
    num=context.args[0].replace("+",""); r=requests.get(f"{PAIR_SERVER}/pair?number={num}",timeout=25).json()
    await update.message.reply_text(f"CODE: *{r['code']}*",parse_mode="Markdown")

async def welcome_h(update,context):
    for m in update.message.new_chat_members:
        await update.message.reply_photo(open("welcome.jpg","rb"),caption=f"┏━ WELCOME {NAME} ━┓ Bienvenue {m.full_name} ✨")

async def goodbye_h(update,context):
    if update.message.left_chat_member:
        await update.message.reply_photo(open("goodbye.jpg","rb"),caption=f"┏━ GOODBYE {NAME} ━┓ Au revoir {update.message.left_chat_member.full_name} 👋")

if __name__=="__main__":
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler(["menu","start","chaine"],menu))
    app.add_handler(CommandHandler("allmenu",allmenu))
    app.add_handler(CommandHandler("play",play))
    app.add_handler(CommandHandler(["yt","tiktok","insta","fb"],yt_cmd))
    app.add_handler(CommandHandler("sticker",sticker_cmd))
    app.add_handler(CommandHandler("ping",ping))
    app.add_handler(CommandHandler("pair",pair_cmd))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS,welcome_h))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER,goodbye_h))
    app.run_polling()