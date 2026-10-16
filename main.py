import os
import sys
import time
import random
import platform
import asyncio
import logging
import traceback
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
)
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
)

try:
    import psutil
except ImportError:
    psutil = None

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ═══════ CONFIGURATION ROYALE ═══════

TOKEN = os.environ.get("BOT_TOKEN")

BOT_NAME = "🌊ᬼ⃟ ⃪ₘᵣ ₖᵢₙG ₖₐYₛₑᵤᵣ ₜₕₑ GₗᵢₜCₕ Dₑᵥ ᡃ🛀⃝⤸𓆪⎯꯭᪳♔"
DEVELOPER_NAME = "@Mr_king_kayseur"
PREFIX = "/"

CHANNEL_URL = "https://t.me/PhenixGuy"
CHANNEL_ID = "4454958268"

# 🖼️ Image utilisée pour TOUTES les commandes
# Mets un lien DIRECT (fichier .jpg/.png), pas une page ibb.co
START_IMAGE = "https://pdftolink.io/file/r2_dXNlcnMva2luZ2theXNld"

WELCOME_IMAGE = START_IMAGE
GOODBYE_IMAGE = START_IMAGE
MODERATION_IMAGE = START_IMAGE

SPAM_MAX_MESSAGES = 5
SPAM_WINDOW_SECONDS = 8

FAKE_TASKS = [
    "Analyse des glitchs en cours...",
    "Compilation du noyau PHÉNIX...",
    "Synchronisation avec la matrice...",
    "Décryptage des bugs résiduels...",
]

RECENT_MESSAGES = defaultdict(deque)
SCORES = defaultdict(int)
NUMBER_GAMES = {}
START_TIME = time.time()


def configured_channel():
    return (
        CHANNEL_URL.startswith("https://t.me/PhenixGuy")
        and CHANNEL_ID != "4454958268"
        and bool(CHANNEL_ID)
    )


def royal_box(title, lines):
    return (
        "╭─〔 ✦ 𝐏𝐇É𝐍𝐈𝐗 𝐆𝐔𝐘 ✦ 〕─╮\n"
        f"│ 𓆩♛𓆪 {title}\n"
        + "".join(f"│ {line}\n" for line in lines)
        + "╰────────────────╯\n"
        f"✦ 𝐃𝐄𝐕 : {DEVELOPER_NAME}"
    )


def main_menu_text(user):
    return (
        "╭─〔 ♛ 𝐏𝐇𝐄́𝐍𝐈𝐗 𝐆𝐔𝐘 ♛ 〕─╮\n"
        "│ ✦ 𝐁𝐔𝐆 𝐁𝐎𝐓 ✦\n"
        "╰────────────────╯\n\n"
        "𓆩👑𓆪 𝐔𝐒𝐄𝐑 𝐈𝐍𝐅𝐎\n"
        f"✧ 𝐍𝐨𝐦 : {user.full_name}\n"
        f"✧ 𝐈𝐃 : {user.id}\n"
        f"✧ 𝐏𝐫𝐞́𝐟𝐢𝐱𝐞 : {PREFIX}\n\n"
        "╭─〔 ✦ 𝐆𝐄́𝐍𝐄́𝐑𝐀𝐋 ✦ 〕─╮\n"
        "│ /start • /menu • /help\n"
        "│ /id • /info • /rules\n"
        "╰────────────────╯\n\n"
        "╭─〔 🍓 𝐆𝐋𝐈𝐓𝐂𝐇 𝐋𝐀𝐁 〕─╮\n"
        "│ /bugmenu • /bug • /ping\n"
        "│ /glitch • /error • /load\n"
        "│ /matrix • /diagnostic • /stop\n"
        "╰────────────────╯\n\n"
        "╭─〔 🛡️ 𝐌𝐎𝐃𝐄́𝐑𝐀𝐓𝐈𝐎𝐍 〕─╮\n"
        "│ /ban • /unban\n"
        "│ /mute • /unmute\n"
        "╰────────────────╯\n\n"
        "╭─〔 🔎 𝐈𝐍𝐅𝐎𝐒 𝐑𝐄́𝐄𝐋𝐋𝐄𝐒 〕─╮\n"
        "│ /whois • /chatstats\n"
        "│ /uptime • /sysinfo\n"
        "│ /admins • /members\n"
        "╰────────────────╯\n\n"
        "╭─〔 🎮 𝐉𝐄𝐔𝐗 〕─╮\n"
        "│ /quiz • /devinette\n"
        "│ /nombre • /score\n"
        "╰────────────────╯\n\n"
        f"𓆩♛𓆪 𝐏𝐎𝐖𝐄𝐑𝐄𝐃 𝐁𝐘 {BOT_NAME}"
    )


# ═══════ ENVOI AVEC IMAGE (toutes les commandes) ═══════

async def send_royal(update, text, image=None, keyboard=None, parse_mode=None):
    """Envoie le texte avec une image. Fallback texte si l'image échoue."""
    image = image or START_IMAGE
    msg = update.effective_message
    if image:
        try:
            await msg.reply_photo(
                photo=image,
                caption=text,
                reply_markup=keyboard,
                parse_mode=parse_mode,
            )
            return
        except Exception:
            logging.exception("Envoi image impossible, fallback texte")
    await msg.reply_text(text, reply_markup=keyboard, parse_mode=parse_mode)


async def is_admin(update, context):
    if not update.effective_chat or not update.effective_user:
        return False
    if update.effective_chat.type == "private":
        return True
    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id, update.effective_user.id
        )
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


async def has_channel_access(user_id, context):
    if not configured_channel():
        return False
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        logging.exception("Vérification de l'abonnement impossible")
        return False


# ═══════ COMMANDES GÉNÉRALES ═══════

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = main_menu_text(user)
    keyboard = None
    if configured_channel():
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📢 Rejoindre la chaîne", url=CHANNEL_URL)]]
        )
    await send_royal(update, text, keyboard=keyboard)


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_royal(update, main_menu_text(update.effective_user))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_royal(
        update, royal_box("𝐀𝐈𝐃𝐄", ["Utilise /menu pour voir toutes les commandes."])
    )


async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    await send_royal(
        update,
        royal_box(
            "𝐈𝐃𝐄𝐍𝐓𝐈𝐅𝐈𝐀𝐍𝐓𝐒",
            [f"𝐔𝐬𝐞𝐫 𝐈𝐃 : {user.id}", f"𝐂𝐡𝐚𝐭 𝐈𝐃 : {chat.id}"],
        ),
    )


async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await send_royal(
        update,
        royal_box(
            "𝐈𝐍𝐅𝐎 𝐔𝐓𝐈𝐋𝐈𝐒𝐀𝐓𝐄𝐔𝐑",
            [
                f"𝐍𝐨𝐦 : {user.full_name}",
                f"𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞 : @{user.username or 'aucun'}",
                f"𝐈𝐃 : {user.id}",
            ],
        ),
    )


async def rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_royal(
        update,
        royal_box(
            "𝐑𝐄̀𝐆𝐋𝐄𝐒",
            [
                "1. Respect entre membres.",
                "2. Pas de spam.",
                "3. Pas de contenu illégal.",
                "4. Écoute les admins.",
            ],
        ),
    )


# ═══════ GLITCH LAB (réel) ═══════

async def bugmenu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_royal(
        update,
        royal_box(
            "𝐆𝐋𝐈𝐓𝐂𝐇 𝐋𝐀𝐁",
            [
                "/bug <id|@pseudo> • /ping",
                "/glitch • /error • /load",
                "/matrix • /diagnostic • /stop",
            ],
        ),
    )


async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t0 = time.perf_counter()
    msg = await update.effective_message.reply_text("🏓 ...")
    t1 = time.perf_counter()
    latency_ms = (t1 - t0) * 1000
    uptime = int(time.time() - START_TIME)
    await msg.edit_text(
        f"🏓 𝐏𝐎𝐍𝐆 !\n⚡ Latence : {latency_ms:.0f} ms\n⏱️ Uptime : {uptime}s"
    )


async def bug_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🎯 Cible optionnelle : /bug <user_id> ou /bug @username ou réponse
    target_id = None
    target_label = "aucune cible"

    if context.args:
        arg = context.args[0].lstrip("@")
        if arg.isdigit():
            target_id = int(arg)
            target_label = f"ID {target_id}"
        else:
            try:
                chat = await context.bot.get_chat("@" + arg)
                target_id = chat.id
                target_label = f"@{arg}"
            except Exception:
                target_label = f"@{arg} (introuvable)"
    elif update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        target_id = u.id
        target_label = f"{u.full_name} (ID {u.id})"

    # 💥 bug : exception Python -> stacktrace
    try:
        _ = 1 / 0
    except Exception:
        tb = traceback.format_exc()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    sysinfo = (
        f"Python {platform.python_version()} | "
        f"{platform.system()} {platform.release()} | "
        f"uptime {int(time.time() - START_TIME)}s"
    )

    header = (
        "╭─〔 🐞 𝐁𝐔𝐆 𝐑𝐄́𝐄𝐋 〕─╮\n"
        f"│ 🎯 𝐂𝐢𝐛𝐥𝐞 : {target_label}\n"
        f"│ 🕐 {ts}\n"
        f"│ 🖥️ {sysinfo}\n"
        "╰────────────────╯"
    )
    text = f"{header}\n```\n{tb}\n```"

    # Mentionne la cible si valide dans le chat
    if target_id and update.effective_chat.type != "private":
        try:
            member = await context.bot.get_chat_member(
                update.effective_chat.id, target_id
            )
            text = f"🎯 {member.user.mention_html()}\n" + text
            await send_royal(update, text, parse_mode="HTML")
            return
        except Exception:
            pass

    await send_royal(update, text, parse_mode="Markdown")


async def glitch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base = " ".join(context.args) if context.args else "PHENIX GLITCH LAB"
    corrupted = "".join(
        random.choice("#@$%&/\\*01") if random.random() < 0.3 else c for c in base
    )
    await send_royal(update, f"⚡ GLITCH : {corrupted}")


async def ferror_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = f"0x{random.randint(0x1000, 0xFFFF):04X}"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    await send_royal(update, f"❌ FATAL ERROR {code}\n🕐 {ts}")


async def load_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.effective_message.reply_text("⏳ Chargement... 0%")
    for pct in (20, 40, 60, 80, 100):
        await asyncio.sleep(0.5)
        try:
            await msg.edit_text(f"⏳ Chargement... {pct}%")
        except Exception:
            break
    await msg.edit_text("✅ Chargement terminé.")


async def matrix_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.effective_message.reply_text(
        "```\n⏳\n```", parse_mode="Markdown"
    )
    for _ in range(6):
        frame = "\n".join(
            "".join(random.choice("01 ") for _ in range(24)) for _ in range(6)
        )
        await asyncio.sleep(0.4)
        try:
            await msg.edit_text(f"```\n{frame}\n```", parse_mode="Markdown")
        except Exception:
            break


async def diagnostic_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = int(time.time() - START_TIME)
    lines = [
        f"𝐏𝐲𝐭𝐡𝐨𝐧 : {platform.python_version()}",
        f"𝐎𝐒 : {platform.system()} {platform.release()}",
        f"𝐔𝐩𝐭𝐢𝐦𝐞 : {uptime}s",
    ]
    if psutil:
        cpu = psutil.cpu_percent(interval=0.3)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        lines += [
            f"𝐂𝐏𝐔 : {cpu}%",
            f"𝐑𝐀𝐌 : {ram.percent}% ({ram.used // (1024**2)} / {ram.total // (1024**2)} MB)",
            f"𝐃𝐢𝐬𝐪𝐮𝐞 : {disk.percent}%",
        ]
    else:
        lines.append("𝐒𝐲𝐬𝐭𝐞̀𝐦𝐞 : psutil non installé")
    await send_royal(update, royal_box("𝐃𝐈𝐀𝐆𝐍𝐎𝐒𝐓𝐈𝐂", lines))


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_royal(update, "🛑 Arrêt des processus simulés.")


# ═══════ COMMANDES RÉELLES (vraies données) ═══════

async def whois_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /whois <id|@pseudo> ou réponse à un message
    target = None
    if context.args:
        arg = context.args[0].lstrip("@")
        try:
            if arg.isdigit():
                target = await context.bot.get_chat(int(arg))
            else:
                target = await context.bot.get_chat("@" + arg)
        except Exception as e:
            await send_royal(update, f"❌ Introuvable : {e}")
            return
    elif update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    if not target:
        await send_royal(update, "Utilise /whois <id|@pseudo> ou réponds à un message.")
        return

    lines = [
        f"𝐍𝐨𝐦 : {target.full_name}",
        f"𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞 : @{target.username or 'aucun'}",
        f"𝐈𝐃 : {target.id}",
        f"𝐁𝐨𝐭 : {'oui' if target.is_bot else 'non'}",
    ]
    if update.effective_chat.type != "private":
        try:
            m = await context.bot.get_chat_member(update.effective_chat.id, target.id)
            lines.append(f"𝐒𝐭𝐚𝐭𝐮𝐭 : {m.status}")
        except Exception:
            pass
    await send_royal(update, royal_box("𝐖𝐇𝐎𝐈𝐒", lines))


async def chatstats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    try:
        full = await context.bot.get_chat(chat.id)
        count = await context.bot.get_chat_member_count(chat.id)
        lines = [
            f"𝐓𝐢𝐭𝐫𝐞 : {full.title or full.full_name}",
            f"𝐓𝐲𝐩𝐞 : {full.type}",
            f"𝐈𝐃 : {chat.id}",
            f"𝐌𝐞𝐦𝐛𝐫𝐞𝐬 : {count}",
        ]
        if full.description:
            lines.append(f"𝐃𝐞𝐬𝐜 : {full.description[:60]}")
        await send_royal(update, royal_box("𝐂𝐇𝐀𝐓 𝐒𝐓𝐀𝐓𝐒", lines))
    except Exception as e:
        await send_royal(update, f"❌ Erreur : {e}")


async def uptime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    up = int(time.time() - START_TIME)
    h, rem = divmod(up, 3600)
    m, s = divmod(rem, 60)
    await send_royal(
        update,
        royal_box("𝐔𝐏𝐓𝐈𝐌𝐄", [f"⏱️ {h}h {m}m {s}s", f"𝐒𝐞𝐜𝐨𝐧𝐝𝐞𝐬 : {up}"]),
    )


async def sysinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [
        f"𝐏𝐲𝐭𝐡𝐨𝐧 : {platform.python_version()}",
        f"𝐎𝐒 : {platform.system()} {platform.release()}",
        f"𝐀𝐫𝐜𝐡 : {platform.machine()}",
        f"𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐞𝐮𝐫 : {platform.processor() or 'n/a'}",
    ]
    if psutil:
        vm = psutil.virtual_memory()
        lines += [
            f"𝐂𝐏𝐔 : {psutil.cpu_count()} cœurs",
            f"𝐑𝐀𝐌 : {vm.used // (1024**2)} / {vm.total // (1024**2)} MB",
            f"𝐃𝐢𝐬𝐪𝐮𝐞 : {psutil.disk_usage('/').percent}%",
        ]
    await send_royal(update, royal_box("𝐒𝐘𝐒𝐈𝐍𝐅𝐎", lines))


async def admins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await send_royal(update, "Commande disponible en groupe uniquement.")
        return
    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        lines = [
            f"{'👑' if a.status == ChatMemberStatus.OWNER else '🛡️'} "
            f"{a.user.full_name} — {a.user.id}"
            for a in admins
        ]
        await send_royal(update, royal_box("𝐀𝐃𝐌𝐈𝐍𝐒", lines or ["aucun"]))
    except Exception as e:
        await send_royal(update, f"❌ Erreur : {e}")


async def members_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await send_royal(update, "Commande disponible en groupe uniquement.")
        return
    try:
        count = await context.bot.get_chat_member_count(update.effective_chat.id)
        await send_royal(update, royal_box("𝐌𝐄𝐌𝐁𝐑𝐄𝐒", [f"👥 Total : {count}"]))
    except Exception as e:
        await send_royal(update, f"❌ Erreur : {e}")


# ═══════ MODÉRATION (réelle) ═══════

async def _get_target_user(update):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user
    return None


async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await send_royal(update, "🚫 Réservé aux admins.")
        return
    target = await _get_target_user(update)
    if not target:
        await send_royal(update, "Réponds au message de la personne à bannir.")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await send_royal(update, f"🔨 {target.full_name} a été banni.")
    except Exception as e:
        await send_royal(update, f"Erreur : {e}")


async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await send_royal(update, "🚫 Réservé aux admins.")
        return
    if not context.args:
        await send_royal(update, "Utilise /unban <user_id>")
        return
    try:
        user_id = int(context.args[0])
        await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        await send_royal(update, "✅ Utilisateur débanni.")
    except Exception as e:
        await send_royal(update, f"Erreur : {e}")


async def mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await send_royal(update, "🚫 Réservé aux admins.")
        return
    target = await _get_target_user(update)
    if not target:
        await send_royal(update, "Réponds au message de la personne à mute.")
        return
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target.id,
            permissions=ChatPermissions(can_send_messages=False),
        )
        await send_royal(update, f"🔇 {target.full_name} a été mute.")
    except Exception as e:
        await send_royal(update, f"Erreur : {e}")


async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await send_royal(update, "🚫 Réservé aux admins.")
        return
    target = await _get_target_user(update)
    if not target:
        await send_royal(update, "Réponds au message de la personne à démute.")
        return
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await send_royal(update, f"🔊 {target.full_name} a été démute.")
    except Exception as e:
        await send_royal(update, f"Erreur : {e}")


# ═══════ JEUX (réels) ═══════

QUIZZES = [
    ("Quelle est la planète rouge ?", "mars"),
    ("Combien de jours dans une semaine ?", "7"),
    ("Quel animal est le roi des animaux ?", "lion"),
    ("Combien font 8 × 7 ?", "56"),
    ("Comment doro une purgeuse?", "être stylé"),
    ("Qui est le father du bot ?", "@Mr_king_kayseur"),
    ("La purge à été créé dans quel pays", "le gabon"),
    ("Lionel Messi à combien de balon d'or", "?"),
]

RIDDLES = [
    ("J'ai des aiguilles mais je ne couds pas.", "horloge"),
    ("Plus je sèche, plus je deviens mouillée.", "serviette"),
    ("Je monte et descends sans bouger.", "escalier"),
]


async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question, answer = random.choice(QUIZZES)
    context.chat_data["quiz_answer"] = answer.lower()
    await send_royal(update, f"🧠 QUIZ : {question}")


async def devinette_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question, answer = random.choice(RIDDLES)
    context.chat_data["quiz_answer"] = answer.lower()
    await send_royal(update, f"🔎 DEVINETTE : {question}")


async def nombre_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    NUMBER_GAMES[update.effective_chat.id] = random.randint(1, 100)
    await send_royal(update, "🔢 J'ai pensé à un nombre entre 1 et 100. Devine-le !")


async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pts = SCORES.get(user.id, 0)
    await send_royal(update, f"🏆 Ton score : {pts} point(s).")


# ═══════ MESSAGES TEXTE (jeux + anti-spam) ═══════

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text.strip()

    now = datetime.now(timezone.utc)
    queue = RECENT_MESSAGES[(chat_id, user.id)]
    queue.append(now)
    while queue and (now - queue[0]) > timedelta(seconds=SPAM_WINDOW_SECONDS):
        queue.popleft()
    if len(queue) > SPAM_MAX_MESSAGES:
        try:
            await update.message.delete()
        except Exception:
            pass
        return

    expected = context.chat_data.get("quiz_answer")
    if expected and text.lower() == expected:
        SCORES[user.id] += 1
        context.chat_data["quiz_answer"] = None
        await update.message.reply_text(f"✅ Bonne réponse {user.first_name} ! +1 point.")
        return

    if chat_id in NUMBER_GAMES and text.lstrip("-").isdigit():
        guess = int(text)
        target = NUMBER_GAMES[chat_id]
        if guess == target:
            SCORES[user.id] += 2
            del NUMBER_GAMES[chat_id]
            await update.message.reply_text(f"🎉 Gagné ! C'était {target}. +2 points.")
        elif guess < target:
            await update.message.reply_text("📈 Plus grand !")
        else:
            await update.message.reply_text("📉 Plus petit !")


# ═══════ BIENVENUE / AU REVOIR ═══════

async def greet_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if not result:
        return

    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    user = result.new_chat_member.user

    joined_statuses = (ChatMemberStatus.MEMBER,)
    left_statuses = (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED)

    if old_status not in joined_statuses and new_status in joined_statuses:
        text = f"👑 Bienvenue {user.mention_html()} dans le royaume ! soit heureux d'être parmi les puissants 💫"
        try:
            if WELCOME_IMAGE:
                await context.bot.send_photo(
                    result.chat.id, photo=WELCOME_IMAGE, caption=text, parse_mode="HTML"
                )
            else:
                await context.bot.send_message(result.chat.id, text, parse_mode="HTML")
        except Exception:
            await context.bot.send_message(result.chat.id, text, parse_mode="HTML")

    elif new_status in left_statuses and old_status not in left_statuses:
        text = f"👋 {user.full_name} a quitté le royaume parce-que c'est un con 🕷️."
        try:
            if GOODBYE_IMAGE:
                await context.bot.send_photo(result.chat.id, photo=GOODBYE_IMAGE, caption=text)
            else:
                await context.bot.send_message(result.chat.id, text)
        except Exception:
            await context.bot.send_message(result.chat.id, text)


# ═══════ MAIN ═══════

def main():
    if not TOKEN:
        raise RuntimeError("La variable d'environnement BOT_TOKEN est manquante.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("rules", rules_cmd))

    app.add_handler(CommandHandler("bugmenu", bugmenu_cmd))
    app.add_handler(CommandHandler("bug", bug_cmd))
    app.add_handler(CommandHandler("ping", ping_cmd))
    app.add_handler(CommandHandler("glitch", glitch_cmd))
    app.add_handler(CommandHandler("ferror", ferror_cmd))
    app.add_handler(CommandHandler("load", load_cmd))
    app.add_handler(CommandHandler("matrix", matrix_cmd))
    app.add_handler(CommandHandler("diagnostic", diagnostic_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))

    app.add_handler(CommandHandler("whois", whois_cmd))
    app.add_handler(CommandHandler("chatstats", chatstats_cmd))
    app.add_handler(CommandHandler("uptime", uptime_cmd))
    app.add_handler(CommandHandler("sysinfo", sysinfo_cmd))
    app.add_handler(CommandHandler("admins", admins_cmd))
    app.add_handler(CommandHandler("members", members_cmd))

    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("mute", mute_cmd))
    app.add_handler(CommandHandler("unmute", unmute_cmd))

    app.add_handler(CommandHandler("quiz", quiz_cmd))
    app.add_handler(CommandHandler("devinette", devinette_cmd))
    app.add_handler(CommandHandler("nombre", nombre_cmd))
    app.add_handler(CommandHandler("score", score_cmd))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(ChatMemberHandler(greet_member, ChatMemberHandler.CHAT_MEMBER))

    logging.info("Bot %s démarré.", BOT_NAME)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
