import asyncio, base64, hashlib, html, io, json, logging, os, random
import re, secrets, string, tempfile, threading, time, unicodedata
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
import qrcode
from PIL import Image
from telegram import (BotCommand, ChatPermissions, InlineKeyboardButton,
                      InlineKeyboardMarkup, Update)
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import (Application, ApplicationHandlerStop, CallbackQueryHandler,
                          CommandHandler, ContextTypes, MessageHandler, TypeHandler, filters)

# ═══════════════════════ CONFIG (variables d'environnement) ═══════════════════════
TOKEN = os.environ["BOT_TOKEN"]
BOT_NAME = os.getenv("BOT_NAME", "KAYSEUR MDX")
OWNER_IDS = {int(x) for x in os.getenv("OWNER_IDS", "0").split(",") if x.strip()}
CHANNEL = os.getenv("CHANNEL_USERNAME", "").lstrip("@t.me/PhenixGuy")   # chaîne du développeur
GROUP = os.getenv("GROUP_USERNAME", "").lstrip("@t.me/phenixchat")       # groupe du développeur
FORCE_SUB = os.getenv("FORCE_SUB", "1") == "1"
MENU_MUSIC_QUERY = os.getenv("MENU_MUSIC_QUERY", "Tiki Tiki Tiki Tika")
RESTRICT_HOURS = int(os.getenv("LINK_RESTRICT_HOURS", "48"))
DATA_FILE = os.getenv("DATA_FILE", "data.json")
BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")
START = time.time()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bot")
esc = html.escape

# ═══════════════════════ POLICE STYLÉE (tout le texte du bot) ═══════════════════════
_SKIP = re.compile(r"(<code>.*?</code>|<[^>]+>|&[a-zA-Z#0-9]+;|https?://\S+|/\w+|@\w+)", re.S)

def _b(ch):
    o = ord(ch)
    if 65 <= o <= 90:  return chr(0x1D5D4 + o - 65)   # 𝗔-𝗭
    if 97 <= o <= 122: return chr(0x1D5EE + o - 97)   # 𝗮-𝘇
    if 48 <= o <= 57:  return chr(0x1D7EC + o - 48)   # 𝟬-𝟵
    return ch

def fx(text):
    parts = _SKIP.split(text)
    for i in range(0, len(parts), 2):  # les morceaux impairs (balises, /commandes, liens) restent intacts
        parts[i] = unicodedata.normalize(
            "NFC", "".join(_b(c) for c in unicodedata.normalize("NFD", parts[i])))
    return "".join(parts)

# ═══════════════════════ STOCKAGE JSON ═══════════════════════
class DB:
    def __init__(self):
        self.d = {"blocked": [], "warns": {}, "users": [], "chats": {}, "seen": {},
                  "welcome_off": [], "antilink_off": []}
        if os.path.exists(DATA_FILE):
            try:
                self.d.update(json.load(open(DATA_FILE)))
            except Exception:
                pass
    def save(self):
        try:
            json.dump(self.d, open(DATA_FILE, "w"))
        except Exception as e:
            log.warning("save: %s", e)
db = DB()

# ═══════════════════════ REGISTRE DE COMMANDES ═══════════════════════
REG = {}  # nom -> (fonction, catégorie, description)
def cmd(name, cat, desc, *aliases):
    def deco(fn):
        REG[name] = (fn, cat, desc)
        for a in aliases:
            REG[a] = (fn, cat, desc)
        return fn
    return deco

def say(update, text, **kw):
    return update.effective_message.reply_text(fx(text), parse_mode=ParseMode.HTML,
                                               disable_web_page_preview=True, **kw)

def box(title, *lines):
    body = "\n".join(f"┃ {l}" for l in lines)
    return f"╔═══ <b>{title}</b> ═══╗\n{body}\n╚═══════════════╝"

def args_text(ctx):
    return " ".join(ctx.args).strip()

FULL = ChatPermissions(can_send_messages=True, can_send_audios=True, can_send_documents=True,
                       can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
                       can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
                       can_add_web_page_previews=True, can_invite_users=True)
NONE = ChatPermissions(can_send_messages=False)

async def is_admin(chat, uid):
    if uid in OWNER_IDS:
        return True
    try:
        m = await chat.get_member(uid)
        return m.status in ("administrator", "creator")
    except TelegramError:
        return False

def group_admin(fn):
    async def w(update, ctx):
        chat, user = update.effective_chat, update.effective_user
        if chat.type == "private":
            return await say(update, "⚠️ Commande réservée aux groupes.")
        if not await is_admin(chat, user.id):
            return await say(update, "⛔ Réservé aux admins du groupe.")
        return await fn(update, ctx)
    return w

def owner_only(fn):
    async def w(update, ctx):
        if update.effective_user.id not in OWNER_IDS:
            return await say(update, "⛔ Réservé au propriétaire du bot.")
        return await fn(update, ctx)
    return w

def target(update):
    r = update.effective_message.reply_to_message
    return r.from_user if r else None

def need_target(fn):
    async def w(update, ctx):
        t = target(update)
        if not t:
            return await say(update, "↩️ Réponds au message de la personne.")
        if await is_admin(update.effective_chat, t.id):
            return await say(update, "⛔ Impossible sur un admin.")
        return await fn(update, ctx, t)
    return w

def parse_dur(s):
    m = re.fullmatch(r"(\d+)([mhjd])", (s or "").lower())
    if not m:
        return None
    n, u = int(m.group(1)), m.group(2)
    return timedelta(minutes=n) if u == "m" else timedelta(hours=n) if u == "h" else timedelta(days=n)

def asset(name):
    p = os.path.join(ASSETS, name)
    return p if os.path.exists(p) else None

def channel_markup():
    if not CHANNEL:
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton("📢 Voir la chaîne", url=f"https://t.me/{CHANNEL}")]])

# ═══════════════════════ BIENVENUE / AU REVOIR (images fixes) ═══════════════════════
async def send_card(ctx, chat_id, image, caption):
    p = asset(image)
    kw = dict(caption=fx(caption), parse_mode=ParseMode.HTML, reply_markup=channel_markup())
    if p:
        with open(p, "rb") as f:
            return await ctx.bot.send_photo(chat_id, f, **kw)
    return await ctx.bot.send_message(chat_id, fx(caption), parse_mode=ParseMode.HTML,
                                      reply_markup=channel_markup())

async def on_join(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.id in db.d["welcome_off"]:
        return
    try:
        full = await ctx.bot.get_chat(chat.id)
        count = await chat.get_member_count()
    except TelegramError:
        full, count = chat, "?"
    desc = (full.description or "Pas de description.")[:300]
    for m in update.message.new_chat_members:
        if m.is_bot:
            continue
        cap = box("👋 BIENVENUE",
                  f"👤 <a href='tg://user?id={m.id}'>{esc(m.full_name)}</a>",
                  f"🏠 {esc(chat.title)}",
                  f"👥 Membres : <b>{count}</b>") + \
            f"\n\n📝 <i>{esc(desc)}</i>\n\n✨ Bienvenue parmi nous, profite bien !"
        await send_card(ctx, chat.id, "welcome.jpg", cap)

async def on_left(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat, m = update.effective_chat, update.message.left_chat_member
    if chat.id in db.d["welcome_off"] or m.is_bot:
        return
    cap = box("👋 GOODBYE", f"👤 {esc(m.full_name)}", f"🏠 {esc(chat.title)}") + \
        "\n\n💔 Merci pour ton passage, à bientôt peut-être !"
    await send_card(ctx, chat.id, "goodbye.jpg", cap)

# ═══════════════════════ ANTI-LIENS ═══════════════════════
LINK_RE = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/|wa\.me/|chat\.whatsapp\.com|discord\.gg/|"
    r"\b[a-z0-9-]{2,}\.(com|net|org|io|me|xyz|co|fr|info|ru|link|gg|ly|app|site|online|shop|club|top|cc)\b)", re.I)

def has_link(msg):
    for ents in (msg.entities, msg.caption_entities):
        for e in ents or []:
            if e.type in ("url", "text_link"):
                return True
    return bool(LINK_RE.search(msg.text or msg.caption or ""))

async def antilink(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg, chat, user = update.effective_message, update.effective_chat, update.effective_user
    if not msg or not user or user.is_bot or chat.type not in ("group", "supergroup"):
        return
    if chat.id in db.d["antilink_off"] or msg.sender_chat or not has_link(msg):
        return
    if await is_admin(chat, user.id):
        return
    try:
        await msg.delete()
    except TelegramError:
        return  # le bot n'est pas admin (droit de supprimer) : on ne fait rien
    restricted = True
    try:
        until = datetime.now(timezone.utc) + timedelta(hours=RESTRICT_HOURS)
        await chat.restrict_member(user.id, NONE, until_date=until)
    except TelegramError:
        restricted = False
    mention = f"<a href='tg://user?id={user.id}'>{esc(user.full_name)}</a>"
    text = box("🚫 LIEN INTERDIT 🚫",
               f"😤 Eh man {mention} !",
               "⛔ Les liens ne sont <b>pas autorisés</b> dans ce groupe.",
               "🗑 Ton message a été supprimé.",
               f"🔒 Tu es restreint pendant <b>{RESTRICT_HOURS} heures</b>." if restricted
               else "⚠️ Respecte les règles.") + "\n\n🛡 <i>Protection anti-liens activée</i>"
    await ctx.bot.send_message(chat.id, fx(text), parse_mode=ParseMode.HTML)
    raise ApplicationHandlerStop

@cmd("antilien", "Groupe", "Activer/désactiver l'anti-liens : /antilien on|off")
@group_admin
async def c_antilien(update, ctx):
    cid, on = update.effective_chat.id, args_text(ctx).lower() != "off"
    off = db.d["antilink_off"]
    if on and cid in off: off.remove(cid)
    if not on and cid not in off: off.append(cid)
    db.save()
    await say(update, "🛡 Anti-liens " + ("activé ✅" if on else "désactivé ❌"))

# ═══════════════════════ PORTE : abonnement obligatoire + blocage ═══════════════════════
async def gate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg, user = update.effective_message, update.effective_user
    if not msg or not user or not (msg.text or "").startswith("/"):
        return
    if user.id not in db.d["users"]:
        db.d["users"].append(user.id); db.save()
    if update.effective_chat.type != "private":
        db.d["chats"][str(update.effective_chat.id)] = update.effective_chat.title or ""
    if user.id in OWNER_IDS:
        return
    if user.id in db.d["blocked"]:
        raise ApplicationHandlerStop
    if not FORCE_SUB:
        return
    missing = []
    for kind, uname in (("la chaîne", CHANNEL), ("le groupe", GROUP)):
        if not uname:
            continue
        try:
            m = await ctx.bot.get_chat_member(f"@{uname}", user.id)
            ok = m.status in ("member", "administrator", "creator") or \
                (m.status == "restricted" and getattr(m, "is_member", True))
        except TelegramError:
            ok = True  # bot non admin du canal : on ne bloque pas par erreur
        if not ok:
            missing.append((kind, uname))
    if missing:
        rows = [[InlineKeyboardButton(f"➕ Rejoindre {k}", url=f"https://t.me/{u}")] for k, u in missing]
        rows.append([InlineKeyboardButton("✅ J'ai rejoint", callback_data="recheck")])
        await msg.reply_text(fx("🔒 <b>Accès verrouillé</b>\n\nAbonne-toi à la chaîne et au groupe "
                                "du développeur pour utiliser le bot, puis relance ta commande."),
                             parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows))
        raise ApplicationHandlerStop

async def recheck(update: Update, ctx):
    await update.callback_query.answer("Relance ta commande 😉")

async def track(update: Update, ctx):
    u, c = update.effective_user, update.effective_chat
    if u and c and c.type != "private" and not u.is_bot:
        db.d["seen"].setdefault(str(c.id), {})[str(u.id)] = u.first_name
        if random.random() < 0.05:
            db.save()

# ═══════════════════════ MENU (image + commandes + musique) ═══════════════════════
CAT_EMOJI = {"Général": "🧭", "Fun": "🎭", "Jeux": "🎮", "Quiz": "🧠", "Outils": "🛠",
             "Stickers": "🖼", "Musique": "🎵", "Groupe": "👮", "Propriétaire": "👑"}

def _dl(query, folder):
    import yt_dlp
    opts = {"format": "bestaudio[ext=m4a]/bestaudio", "outtmpl": f"{folder}/%(title).60s.%(ext)s",
            "noplaylist": True, "quiet": True, "default_search": "ytsearch1",
            "max_filesize": 48 * 1024 * 1024}
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(query, download=True)
        if "entries" in info:
            info = info["entries"][0]
        return y.prepare_filename(info), info.get("title", "Musique")

async def send_menu_music(chat_id, ctx):
    fid = db.d.get("menu_music_id")
    if fid:
        try:
            return await ctx.bot.send_audio(chat_id, fid)
        except TelegramError:
            db.d.pop("menu_music_id", None)
    try:
        local = asset("menu.mp3")
        if local:
            with open(local, "rb") as f:
                m = await ctx.bot.send_audio(chat_id, f, title=BOT_NAME)
        else:
            with tempfile.TemporaryDirectory() as tmp:
                path, title = await asyncio.to_thread(_dl, MENU_MUSIC_QUERY, tmp)
                with open(path, "rb") as f:
                    m = await ctx.bot.send_audio(chat_id, f, title=title)
        db.d["menu_music_id"] = m.audio.file_id
        db.save()
    except Exception as e:
        log.warning("menu music: %s", e)

@cmd("menu", "Général", "Menu complet avec toutes les commandes", "help", "aide")
async def c_menu(update, ctx):
    chat_id = update.effective_chat.id
    cats = {}
    for n, (_, c, _d) in REG.items():
        if n in ("help", "aide"):
            continue
        cats.setdefault(c, []).append(f"/{n}")
    total = sum(len(v) for v in cats.values())
    head = box(f"👑 {esc(BOT_NAME)} 👑",
               f"👋 Salut <b>{esc(update.effective_user.first_name)}</b> !",
               f"⚡ <b>{total}</b> commandes disponibles",
               "👇 Toutes les commandes ci-dessous")
    p = asset("menu.jpg")
    if p:
        with open(p, "rb") as f:
            await ctx.bot.send_photo(chat_id, f, caption=fx(head), parse_mode=ParseMode.HTML,
                                     reply_markup=channel_markup())
    else:
        await say(update, head, reply_markup=channel_markup())
    blocks = []
    for c, names in cats.items():
        e = CAT_EMOJI.get(c, "✨")
        blocks.append(f"╭──『 {e} <b>{c.upper()}</b> 』──╮\n" +
                      "\n".join(f"│ ➤ {n}" for n in names) + "\n╰─────────────────╯")
    chunk = ""
    for b in blocks:
        if len(chunk) + len(b) > 3500:
            await say(update, chunk); chunk = ""
        chunk += b + "\n\n"
    if chunk:
        await say(update, chunk + "💫 <i>Propulsé par " + esc(BOT_NAME) + "</i>")
    await send_menu_music(chat_id, ctx)

# ═══════════════════════ GÉNÉRAL ═══════════════════════
@cmd("start", "Général", "Démarrer le bot")
async def c_start(update, ctx):
    await say(update, box(f"🤖 {esc(BOT_NAME)}", "Bienvenue ! Tape /menu pour voir",
                          "toutes les commandes."), reply_markup=channel_markup())

@cmd("ping", "Général", "Latence")
async def c_ping(update, ctx):
    t = time.time(); m = await update.effective_message.reply_text(fx("🏓"))
    await m.edit_text(fx(f"🏓 Pong ! {int((time.time() - t) * 1000)} ms"))

@cmd("uptime", "Général", "Temps de fonctionnement")
async def c_uptime(update, ctx):
    s = int(time.time() - START)
    await say(update, f"⏱ En ligne depuis {s // 3600}h {s % 3600 // 60}m {s % 60}s")

@cmd("id", "Général", "Ton ID / ID du chat")
async def c_id(update, ctx):
    t = target(update) or update.effective_user
    await say(update, box("🆔 ID", f"Utilisateur : <code>{t.id}</code>",
                          f"Chat : <code>{update.effective_chat.id}</code>"))

@cmd("info", "Général", "Infos sur un utilisateur (réponds à son message)")
async def c_info(update, ctx):
    t = target(update) or update.effective_user
    await say(update, box("👤 INFO", f"Nom : {esc(t.full_name)}",
                          f"Pseudo : @{t.username or '—'}", f"ID : <code>{t.id}</code>",
                          f"Langue : {t.language_code or '—'}"))

@cmd("chatinfo", "Général", "Infos du groupe")
async def c_chatinfo(update, ctx):
    c = update.effective_chat
    n = await c.get_member_count()
    await say(update, box("🏠 GROUPE", esc(c.title or "Privé"), f"Membres : {n}",
                          f"ID : <code>{c.id}</code>"))

@cmd("about", "Général", "À propos")
async def c_about(update, ctx):
    await say(update, box("ℹ️ À PROPOS", esc(BOT_NAME), f"{len(REG)} commandes"),
              reply_markup=channel_markup())

# ═══════════════════════ FUN (ajoute tes propres textes ici) ═══════════════════════
TEXTS = {
    "blague": ("😂 Blague", ["Pourquoi les plongeurs plongent-ils en arrière ? Parce que sinon ils tombent dans le bateau.",
                             "Que dit un escargot sur le dos d'une tortue ? Youhou !",
                             "Quel est le comble pour un électricien ? De ne pas être au courant.",
                             "Pourquoi les poissons détestent l'ordinateur ? À cause du net."]),
    "fait": ("🧠 Le saviez-vous", ["Le miel ne périme jamais.", "Les pieuvres ont trois cœurs.",
                                   "Un jour sur Vénus dure plus longtemps qu'une année vénusienne.",
                                   "Les bananes sont légèrement radioactives."]),
    "citation": ("💬 Citation", ["Le succès, c'est tomber sept fois, se relever huit.",
                                 "Ce n'est pas la montagne qu'on conquiert, mais soi-même.",
                                 "Fais de ta vie un rêve, et d'un rêve une réalité."]),
    "compliment": ("🌸 Compliment", ["Tu illumines le groupe !", "Ton énergie est contagieuse.",
                                     "Tu es plus cool que tu ne le crois."]),
    "clash": ("🔥 Clash", ["Tu es la preuve que même le Wi-Fi peut être lent.",
                           "Ton niveau ? Même Google ne trouve pas.",
                           "Tu as autant de charisme qu'une chaise cassée."]),
    "defi": ("🎯 Défi", ["Envoie un vocal en chantant.", "Change ta photo de profil pendant 1h.",
                         "Écris ton prochain message sans voyelle 'e'."]),
    "verite": ("🕵️ Vérité", ["Quel est ton plus grand secret ?", "Ta pire honte ?", "Ton crush du groupe ?"]),
    "conseil": ("💡 Conseil", ["Bois de l'eau.", "Dors plus.", "Sauvegarde tes fichiers.", "Respire."]),
    "devinette": ("🧩 Devinette", ["Plus on en prend, plus on en laisse. Quoi ? → Les pas.",
                                   "Je suis à toi mais les autres m'utilisent plus que toi. → Ton prénom."]),
    "motivation": ("🚀 Motivation", ["Un petit pas chaque jour.", "Commence maintenant, parfait viendra après."]),
}
def mk_text_cmd(name, title, items):
    async def h(update, ctx):
        await say(update, box(title, esc(random.choice(items))))
    REG[name] = (h, "Fun", title)
for _n, (_t, _i) in TEXTS.items():
    mk_text_cmd(_n, _t, _i)

# ═══════════════════════ JEUX ═══════════════════════
def dice_cmd(name, emoji):
    async def h(update, ctx):
        await update.effective_message.reply_dice(emoji=emoji)
    REG[name] = (h, "Jeux", f"Animation {emoji}")
for _n, _e in (("de", "🎲"), ("fleche", "🎯"), ("basket", "🏀"), ("foot", "⚽"),
               ("bowling", "🎳"), ("slot", "🎰")):
    dice_cmd(_n, _e)

@cmd("pile", "Jeux", "Pile ou face")
async def c_pile(update, ctx):
    await say(update, f"🪙 {random.choice(['PILE', 'FACE'])}")

@cmd("boule8", "Jeux", "Boule magique")
async def c_8(update, ctx):
    await say(update, "🎱 " + random.choice(["Oui", "Non", "Peut-être", "Sûrement", "Jamais", "Repose la question"]))

@cmd("pfc", "Jeux", "Pierre-feuille-ciseaux : /pfc pierre")
async def c_pfc(update, ctx):
    opts = ["pierre", "feuille", "ciseaux"]
    me = args_text(ctx).lower()
    if me not in opts:
        return await say(update, "Utilise : /pfc pierre|feuille|ciseaux")
    bot = random.choice(opts)
    win = {("pierre", "ciseaux"), ("feuille", "pierre"), ("ciseaux", "feuille")}
    res = "🤝 Égalité" if me == bot else ("🏆 Tu gagnes !" if (me, bot) in win else "💀 Je gagne !")
    await say(update, box("✊ PFC", f"Toi : {me}", f"Moi : {bot}", res))

GUESS = {}
@cmd("devine", "Jeux", "Devine le nombre 1-100 : /devine 42")
async def c_devine(update, ctx):
    k = update.effective_chat.id
    if not ctx.args or not ctx.args[0].isdigit():
        GUESS[k] = random.randint(1, 100)
        return await say(update, "🔢 J'ai choisi un nombre entre 1 et 100. /devine <nombre>")
    if k not in GUESS:
        GUESS[k] = random.randint(1, 100)
    g = int(ctx.args[0])
    if g == GUESS[k]:
        del GUESS[k]
        return await say(update, f"🎉 Bravo {esc(update.effective_user.first_name)} !")
    await say(update, "⬆️ Plus grand" if g < GUESS[k] else "⬇️ Plus petit")

# ═══════════════════════ QUIZ (vrais quiz Telegram) ═══════════════════════
QUIZ = {  # catégorie -> [(question, [choix], index_bonne_réponse, explication)]
    "culture": [("Capitale de l'Australie ?", ["Sydney", "Canberra", "Melbourne"], 1, "Canberra."),
                ("Combien de joueurs dans une équipe de foot ?", ["9", "11", "13"], 1, "11.")],
    "science": [("Symbole chimique de l'or ?", ["Ag", "Au", "Fe"], 1, "Au."),
                ("Planète la plus proche du Soleil ?", ["Mercure", "Vénus", "Mars"], 0, "Mercure.")],
    "histoire": [("Année de la Révolution française ?", ["1789", "1815", "1914"], 0, "1789."),
                 ("Premier homme sur la Lune ?", ["Gagarine", "Armstrong", "Aldrin"], 1, "Neil Armstrong.")],
    "geo": [("Plus long fleuve d'Afrique ?", ["Congo", "Nil", "Niger"], 1, "Le Nil."),
            ("Plus grand océan ?", ["Atlantique", "Indien", "Pacifique"], 2, "Pacifique.")],
    "info": [("Que signifie HTML ?", ["HyperText Markup Language", "High Tech ML", "Home Tool ML"], 0, "HyperText Markup Language."),
             ("Créateur de Python ?", ["Guido van Rossum", "Linus Torvalds", "Elon Musk"], 0, "Guido van Rossum.")],
}
def quiz_cmd(name, items):
    async def h(update, ctx):
        q, opts, ans, exp = random.choice(items)
        await ctx.bot.send_poll(update.effective_chat.id, q, opts, type="quiz",
                                correct_option_id=ans, explanation=exp, is_anonymous=False)
    REG[name] = (h, "Quiz", f"Quiz {name}")
for _c, _it in QUIZ.items():
    quiz_cmd(f"quiz_{_c}", _it)
quiz_cmd("quiz", [x for v in QUIZ.values() for x in v])

# ═══════════════════════ OUTILS ═══════════════════════
@cmd("qr", "Outils", "Créer un QR code : /qr texte")
async def c_qr(update, ctx):
    t = args_text(ctx)
    if not t:
        return await say(update, "Utilise : /qr <texte ou lien>")
    bio = io.BytesIO(); qrcode.make(t).save(bio, "PNG"); bio.seek(0)
    await update.effective_message.reply_photo(bio, caption=fx("✅ QR code prêt"))

@cmd("calc", "Outils", "Calculatrice : /calc 2+2*3")
async def c_calc(update, ctx):
    e = args_text(ctx)
    if not re.fullmatch(r"[0-9+\-*/().,% ^]+", e or "x"):
        return await say(update, "Utilise : /calc 2+2*3")
    try:
        r = eval(e.replace("^", "**").replace(",", "."), {"__builtins__": {}}, {})
        await say(update, f"🧮 <code>{esc(e)}</code> = <b>{r}</b>")
    except Exception:
        await say(update, "❌ Calcul invalide")

@cmd("mdp", "Outils", "Mot de passe aléatoire : /mdp 16")
async def c_mdp(update, ctx):
    n = int(ctx.args[0]) if ctx.args and ctx.args[0].isdigit() else 14
    n = max(6, min(n, 64))
    al = string.ascii_letters + string.digits + "!@#$%&*"
    await say(update, f"🔐 <code>{esc(''.join(secrets.choice(al) for _ in range(n)))}</code>")

@cmd("b64", "Outils", "Encoder en base64")
async def c_b64(update, ctx):
    await say(update, f"<code>{base64.b64encode(args_text(ctx).encode()).decode()}</code>")

@cmd("unb64", "Outils", "Décoder base64")
async def c_unb64(update, ctx):
    try:
        await say(update, esc(base64.b64decode(args_text(ctx)).decode()))
    except Exception:
        await say(update, "❌ Base64 invalide")

@cmd("hash", "Outils", "SHA-256 d'un texte")
async def c_hash(update, ctx):
    await say(update, f"<code>{hashlib.sha256(args_text(ctx).encode()).hexdigest()}</code>")

@cmd("maj", "Outils", "MAJUSCULES")
async def c_maj(update, ctx): await say(update, esc(args_text(ctx).upper()) or "…")

@cmd("min", "Outils", "minuscules")
async def c_min(update, ctx): await say(update, esc(args_text(ctx).lower()) or "…")

@cmd("inverse", "Outils", "Inverser un texte")
async def c_inv(update, ctx): await say(update, esc(args_text(ctx)[::-1]) or "…")

@cmd("choisir", "Outils", "Choisir : /choisir a | b | c")
async def c_choisir(update, ctx):
    o = [x.strip() for x in args_text(ctx).split("|") if x.strip()]
    await say(update, f"🎲 {esc(random.choice(o))}" if o else "Utilise : /choisir a | b | c")

@cmd("heure", "Outils", "Date et heure (serveur)")
async def c_heure(update, ctx):
    await say(update, f"🕒 <code>{datetime.now(timezone.utc):%d/%m/%Y %H:%M:%S}</code> UTC")

@cmd("meteo", "Outils", "Météo : /meteo Paris")
async def c_meteo(update, ctx):
    v = args_text(ctx)
    if not v:
        return await say(update, "Utilise : /meteo <ville>")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"https://wttr.in/{v}", params={"format": "%l: %c %t, %w, humidité %h", "lang": "fr"})
    await say(update, esc(r.text.strip()))

# ═══════════════════════ STICKERS ═══════════════════════
@cmd("sticker", "Stickers", "Réponds à une photo pour créer un sticker")
async def c_sticker(update, ctx):
    r = update.effective_message.reply_to_message
    if not r or not r.photo:
        return await say(update, "↩️ Réponds à une <b>photo</b> avec /sticker")
    f = await (await r.photo[-1].get_file()).download_as_bytearray()
    im = Image.open(io.BytesIO(f)).convert("RGBA"); im.thumbnail((512, 512))
    bio = io.BytesIO(); im.save(bio, "WEBP"); bio.seek(0)
    await update.effective_message.reply_sticker(bio)

# ═══════════════════════ MUSIQUE (yt-dlp) ═══════════════════════
@cmd("musique", "Musique", "Télécharger une musique : /musique titre ou lien", "play", "mp3", "song")
async def c_music(update, ctx):
    q = args_text(ctx)
    if not q:
        return await say(update, "🎵 Utilise : /musique <titre ou lien>")
    wait = await update.effective_message.reply_text(fx("🎧 Recherche et téléchargement…"))
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path, title = await asyncio.to_thread(_dl, q, tmp)
            with open(path, "rb") as f:
                await update.effective_message.reply_audio(f, title=title, caption=fx(f"🎵 {title}"))
        await wait.delete()
    except Exception as e:
        log.warning("music: %s", e)
        await wait.edit_text(fx("❌ Impossible de télécharger (introuvable ou trop lourd)."))

# ═══════════════════════ GROUPE / MODÉRATION ═══════════════════════
@cmd("admins", "Groupe", "Liste des admins")
async def c_admins(update, ctx):
    a = await update.effective_chat.get_administrators()
    await say(update, box("👮 ADMINS", *[f"<a href='tg://user?id={x.user.id}'>{esc(x.user.full_name)}</a>"
                                          for x in a if not x.user.is_bot]))

@cmd("tagall", "Groupe", "Taguer les membres vus récemment")
@group_admin
async def c_tagall(update, ctx):
    chat = update.effective_chat
    ids = dict(db.d["seen"].get(str(chat.id), {}))
    for a in await chat.get_administrators():
        ids[str(a.user.id)] = a.user.first_name
    items = [f"<a href='tg://user?id={i}'>{esc(n)}</a>" for i, n in ids.items()]
    msg = args_text(ctx) or "📢 Attention tout le monde !"
    for i in range(0, len(items), 5):
        await say(update, esc(msg) + "\n" + " ".join(items[i:i + 5]))
        await asyncio.sleep(1)

@cmd("ban", "Groupe", "Bannir (réponds au message)")
@group_admin
@need_target
async def c_ban(update, ctx, t):
    await update.effective_chat.ban_member(t.id)
    await say(update, box("🔨 BANNI", f"👤 {esc(t.full_name)}", "Retiré du groupe définitivement."))

@cmd("unban", "Groupe", "Débannir (réponds au message ou /unban id)")
@group_admin
async def c_unban(update, ctx):
    t = target(update)
    uid = t.id if t else (int(ctx.args[0]) if ctx.args and ctx.args[0].isdigit() else None)
    if not uid:
        return await say(update, "↩️ Réponds au message ou /unban <id>")
    await update.effective_chat.unban_member(uid, only_if_banned=True)
    await say(update, "✅ Débanni.")

@cmd("kick", "Groupe", "Supprimer/expulser une personne du groupe (réponds au message)", "retirer", "virer")
@group_admin
@need_target
async def c_kick(update, ctx, t):
    await update.effective_chat.ban_member(t.id); await update.effective_chat.unban_member(t.id)
    await say(update, box("👢 EXPULSÉ", f"👤 {esc(t.full_name)}", "Retiré du groupe (peut revenir)."))

@cmd("mute", "Groupe", "Muet : /mute (définitif) ou /mute 30m | 2h | 1d", "muet", "tmute")
@group_admin
@need_target
async def c_mute(update, ctx, t):
    d = parse_dur(ctx.args[0]) if ctx.args else None
    until = datetime.now(timezone.utc) + d if d else None
    await update.effective_chat.restrict_member(t.id, NONE, until_date=until)
    await say(update, box("🔇 MUET", f"👤 {esc(t.full_name)}",
                          f"⏳ Durée : <b>{ctx.args[0]}</b>" if d else "⏳ Durée : <b>illimitée</b>"))

@cmd("unmute", "Groupe", "Rendre la parole (réponds au message)", "parle")
@group_admin
async def c_unmute(update, ctx):
    t = target(update)
    if not t:
        return await say(update, "↩️ Réponds au message de la personne.")
    await update.effective_chat.restrict_member(t.id, FULL)
    await say(update, box("🔊 PARLE", f"👤 {esc(t.full_name)}", "Tu peux de nouveau écrire !"))

@cmd("warn", "Groupe", "Avertir (3 = ban)")
@group_admin
@need_target
async def c_warn(update, ctx, t):
    k = f"{update.effective_chat.id}:{t.id}"
    db.d["warns"][k] = db.d["warns"].get(k, 0) + 1; db.save()
    n = db.d["warns"][k]
    if n >= 3:
        await update.effective_chat.ban_member(t.id); db.d["warns"].pop(k); db.save()
        return await say(update, f"🔨 {esc(t.full_name)} banni (3/3).")
    await say(update, f"⚠️ {esc(t.full_name)} averti ({n}/3).")

@cmd("unwarn", "Groupe", "Retirer les avertissements")
@group_admin
async def c_unwarn(update, ctx):
    t = target(update)
    if t:
        db.d["warns"].pop(f"{update.effective_chat.id}:{t.id}", None); db.save()
        await say(update, "✅ Avertissements effacés.")

@cmd("pin", "Groupe", "Épingler (réponds au message)")
@group_admin
async def c_pin(update, ctx):
    r = update.effective_message.reply_to_message
    if r: await r.pin()

@cmd("unpin", "Groupe", "Désépingler")
@group_admin
async def c_unpin(update, ctx):
    await update.effective_chat.unpin_all_messages()

@cmd("del", "Groupe", "Supprimer le message ciblé")
@group_admin
async def c_del(update, ctx):
    r = update.effective_message.reply_to_message
    if r: await r.delete()
    await update.effective_message.delete()

@cmd("bienvenue", "Groupe", "Activer/désactiver bienvenue : /bienvenue on|off")
@group_admin
async def c_bv(update, ctx):
    cid, on = update.effective_chat.id, args_text(ctx).lower() != "off"
    off = db.d["welcome_off"]
    if on and cid in off: off.remove(cid)
    if not on and cid not in off: off.append(cid)
    db.save(); await say(update, "✅ Bienvenue/Goodbye " + ("activés" if on else "désactivés"))

# ═══════════════════════ PROPRIÉTAIRE ═══════════════════════
def _uid(update, ctx):
    t = target(update)
    if t:
        return t.id
    return int(ctx.args[0]) if ctx.args and ctx.args[0].lstrip("-").isdigit() else None

@cmd("block", "Propriétaire", "Bloquer un utilisateur du bot (reply ou id)")
@owner_only
async def c_block(update, ctx):
    uid = _uid(update, ctx)
    if uid and uid not in db.d["blocked"]:
        db.d["blocked"].append(uid); db.save()
    await say(update, f"🚫 {uid} bloqué.")

@cmd("unblock", "Propriétaire", "Débloquer un utilisateur du bot")
@owner_only
async def c_unblock(update, ctx):
    uid = _uid(update, ctx)
    if uid in db.d["blocked"]:
        db.d["blocked"].remove(uid); db.save()
    await say(update, f"✅ {uid} débloqué.")

@cmd("stats", "Propriétaire", "Statistiques du bot")
@owner_only
async def c_stats(update, ctx):
    await say(update, box("📊 STATS", f"Utilisateurs : {len(db.d['users'])}",
                          f"Groupes : {len(db.d['chats'])}", f"Bloqués : {len(db.d['blocked'])}"))

@cmd("diffusion", "Propriétaire", "Message à tous : /diffusion texte")
@owner_only
async def c_bc(update, ctx):
    t, ok = fx(args_text(ctx)), 0
    for cid in list(db.d["users"]) + [int(x) for x in db.d["chats"]]:
        try:
            await ctx.bot.send_message(cid, t); ok += 1
        except TelegramError:
            pass
        await asyncio.sleep(0.05)
    await say(update, f"📨 Envoyé à {ok} chats.")

# ═══════════════════════ LANCEMENT ═══════════════════════
async def post_init(app):
    seen, menu = set(), []
    for n, (fn, _, d) in REG.items():
        if fn in seen:      # on n'affiche pas les alias dans le menu Telegram
            continue
        seen.add(fn)
        menu.append(BotCommand(n, (d or n)[:250]))
    await app.bot.set_my_commands(menu[:100])  # limite Telegram : 100 (les autres marchent quand même)

def health_server():
    port = os.getenv("PORT")
    if not port:
        return
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        def log_message(self, *a): pass
    threading.Thread(target=HTTPServer(("0.0.0.0", int(port)), H).serve_forever, daemon=True).start()

def main():
    health_server()
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    group_msgs = filters.ChatType.GROUPS & (filters.TEXT | filters.CAPTION) & ~filters.StatusUpdate.ALL
    app.add_handler(MessageHandler(group_msgs, antilink), group=-2)
    app.add_handler(TypeHandler(Update, gate), group=-1)
    app.add_handler(CallbackQueryHandler(recheck, pattern="^recheck$"))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_join))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, on_left))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track), group=1)
    for name, (fn, _, _) in REG.items():
        app.add_handler(CommandHandler(name, fn))
    log.info("%s démarré avec %d commandes", BOT_NAME, len(REG))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
