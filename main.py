import os
import random
import asyncio
import logging
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
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ═══════ CONFIGURATION ROYALE ═══════

TOKEN = os.environ.get("BOT_TOKEN")

BOT_NAME = "PHÉNI"
DEVELOPER_NAME = "@Mr_king_kayseur"
PREFIX = "/"

# Remplace ces deux valeurs par les informations de ta chaîne.
CHANNEL_URL = "https://t.me/Glitch_Dev_Fenix667"
CHANNEL_ID = "4454958268"

# Mets ici le lien direct de ton image.
# Laisse vide si tu ne veux pas encore ajouter d'image.
START_IMAGE = "https://ibb.co/ycWd72ZM"

WELCOME_IMAGE = START_IMAGE
GOODBYE_IMAGE = START_IMAGE
MODERATION_IMAGE = START_IMAGE

SPAM_MAX_MESSAGES = 5
SPAM_WINDOW_SECONDS = 8

FAKE_TASKS == {}
RECENT_MESSAGES = defaultdict(deque)

QUIZZES = [
    ("Quelle est la planète rouge ?", "mars"),
    ("Combien de jours dans une semaine ?", "7"),
    ("Quel animal est le roi des animaux ?", "lion"),
    ("Combien font 8 × 7 ?", "56"),
     ("Comment doro une purgeuse?", "être stylé"),
      ("Qui est le father du bot ?", "@Mr_king_kayseur"),
]

RIDDLES = [
    ("J'ai des aiguilles mais je ne couds pas.", "horloge"),
    ("Plus je sèche, plus je deviens mouillée.", "serviette"),
    ("Je monte et descends sans bouger.", "escalier"),
]


def configured_channel():
    return (
        CHANNEL_URL.startswith("https://t.me/")
        and CHANNEL_ID != "4454958268"
        and bool(CHANNEL_ID)
    )


def royal_box(title, lines):
    return (
        f"╭─〔 ✦ 𝐏𝐇É𝐍𝐈𝐗 𝐆𝐔𝐘 ✦ 〕─╮\n"
        f"│ 𓆩♛𓆪 {title}\n"
        + "".join(f"│ {line}\n" for line in lines)
        + "╰────────────────╯\n"
        f"✦ 𝐃𝐄𝐕 : {DEVELOPER_NAME}"
    )


def main_menu_text(user):
    return (
        "╭─〔 ♛ 𝐏𝐇É𝐍𝐈𝐗 𝐆𝐔𝐘 ♛ 〕─╮\n"
        "│ ✦ 𝐁𝐔𝐆 𝐁𝐎𝐓 ✦\n"
        "╰────────────────╯\n\n"
        "𓆩👑𓆪 𝐔𝐒𝐄𝐑 𝐈𝐍𝐅𝐎\n"
        f"✧ 𝐍𝐨𝐦 : {user.full_name}\n"
        f"✧ 𝐈𝐃 : {user.id}\n"
        f"✧ 𝐏𝐫𝐞́𝐟𝐢𝐱𝐞 : {PREFIX}\n\n"
        "╭─〔 ✦ 𝐆É𝐍É𝐑𝐀𝐋 ✦ 〕─╮\n"
        "│ /start • /menu • /help\n"
        "│ /id • /info • /rules\n"
        "╰────────────────╯\n\n"
        "╭─〔 🍓 𝐆𝐋𝐈𝐓𝐂𝐇 𝐋𝐀𝐁 〕─╮\n"
        "│ /bugmenu • /bug\n"
        "│ /glitch • /ferror\n"
        "│ /load • /matrix\n"
        "│ /diagnostic • /stop\n"
        "╰────────────────╯\n\n"
        "╭─〔 🛡️ 𝐌𝐎𝐃É𝐑𝐀𝐓𝐈𝐎𝐍 〕─╮\n"
        "│ /ban • /unban\n"
        "│ /mute • /unmute\n"
        "╰────────────────╯\n\n"
        "╭─〔 🎮 𝐉𝐄𝐔𝐗 〕─╮\n"
        "│ /quiz • /devinette\n"
        "│ /nombre • /score\n"
        "╰────────────────╯\n\n"
        f"𓆩♛𓆪 𝐏𝐎𝐖𝐄𝐑𝐄𝐃 𝐁𝐘 {BOT_NAME}"
    )


async def is_admin(update, context):
    if not update.effective_chat or not update.effective_user:
        return False

    if update.effective_chat.type == "private":
        return True

    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id,
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
        member = await context.bot.get_chat_member(
            CHANNEL_ID, user_id
        )
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        logging.exception("Vérification de l'abonnement impossible")
        return False


async def send_styled(context, chat_id, text, image=""):
    try:
        if image:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=image,
                caption=text,
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
            )
    except Exception:
        logging.exception("Envoi illustré impossible")
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
        )


async def require_channel(update, context):
    user = update.effective_user

    if not user:
        return False

    if await has_channel_access(user.id, context):
        return True

    if not configured_channel():
        await update.effective_message.reply_text(
            "🔧 L'accès aux bugs n'est pas configuré.\n"
            "Complète CHANNEL_URL et CHANNEL_ID dans main.py."
        )
        return False

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 𝐑𝐄𝐉𝐎𝐈𝐍 𝐋𝐀 𝐂𝐇𝐀𝐈𝐍𝐄",
                url=CHANNEL_URL,
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Vérifier mon abonnement",
                callback_data="check_channel",
            )
        ],
    ])

    await update.effective_message.reply_text(
        royal_box(
            "🔐 𝐀𝐂𝐂È𝐒 𝐑𝐄𝐒𝐓𝐑𝐄𝐈𝐍𝐓",
            [
                "Abonne-toi à la chaîne du développeur.",
                "Puis appuie sur Vérifier mon abonnement.",
            ],
        ),
        reply_markup=keyboard,
    )
    return False
    # ═══════════════════════════════════
# COMMANDES PRINCIPALES
# ═══════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 OUVRIR LE MENU", callback_data="open_menu")],
        [InlineKeyboardButton("🍓 GLITCH LAB", callback_data="open_bugmenu")],
    ])

    text = royal_box(
        "𝐁𝐈𝐄𝐍𝐕𝐄𝐍𝐔𝐄",
        [
            f"×͜× 𝗦𝗮𝗹𝘂𝘁 {user.first_name} !",
            "𝗝𝗲 𝘀𝘂𝗶𝘀 🅿🅷🅴🅽🅸🆇 🅶🆄🆈",
            "𝗕𝗼𝘁 𝗿𝗼𝘆𝗮𝗹 𝗰𝗿𝗲𝗲 𝗽𝗼𝘂𝗿 𝘁'𝗮 𝗰𝗼𝗺𝗺𝘂𝗻𝗮𝘂𝘁é 𝗲𝘁 𝘀𝗲𝗻𝗱 𝗱𝗲𝘀 𝗯𝘂𝗴𝘀 𝗲𝘁𝗰 𓅂.",
            f"🆔 Ton ID : {user.id}",
            "Choisis une option ci-dessous.",
        ],
    )

    await send_styled(
        context,
        update.effective_chat.id,
        text,
        START_IMAGE,
    )

    await update.effective_message.reply_text(
        "╭─〔 ♛ 𝐌𝐄𝐍𝐔 𝐑𝐀𝐏𝐈𝐃𝐄 ♛ 〕─╮\n"
        "│ Sélectionne une option :\n"
        "╰────────────────╯",
        reply_markup=keyboard,
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_styled(
        context,
        update.effective_chat.id,
        main_menu_text(update.effective_user),
        START_IMAGE,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        royal_box(
            "🆘 𝐀𝐈𝐃𝐄",
            [
                "/start — Démarrer le bot",
                "/menu — Afficher le menu",
                "/id — Ton identifiant Telegram",
                "/info — Informations du chat",
                "/rules — Règles du groupe",
                "/bugmenu",
            ],
        )
    )


async def user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    await update.effective_message.reply_text(
        royal_box(
            "🆔 𝐓𝐎𝐍 𝐈𝐃",
            [
                f"Nom : {user.full_name}",
                f"Identifiant : {user.id}",
            ],
        )
    )


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    await update.effective_message.reply_text(
        royal_box(
            "ℹ️ 𝐈𝐍𝐅𝐎𝐒",
            [
                f"Nom : {chat.title or 'Discussion privée'}",
                f"ID : {chat.id}",
                f"Type : {chat.type}",
            ],
        )
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        royal_box(
            "♻️ 𝐑È𝐆𝐋𝐄𝐒",
            [
                "Respecte les membres.",
                "Évite le spam.",
                "Pas de liens publicitaires interdits.",
                "Respecte les administrateurs.",
            ],
        )
    )


# ═══════════════════════════════════
# BOUTONS DU MENU
# ═══════════════════════════════════

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    if query.data == "open_menu":
        await query.message.reply_text(
            main_menu_text(query.from_user)
        )

    elif query.data == "open_bugmenu":
        if await has_channel_access(query.from_user.id, context):
            await query.message.reply_text(
                royal_box(
                    "🍓 𝐏𝐇𝐄𝐍𝐈𝐗 𝐋𝐀𝐁",
                    [
                        "/bugmenu — Ouvrir le laboratoire",
                        "/bug — anomalie",
                        "/glitch — Glitch",
                        "/error — Erreur",
                        "/load — Chargement",
                        "/matrix — Matrix",
                        "/diagnostic — Diagnostic",
                        "/stopfake — Arrêter",
                    ],
                )
            )
        else:
            await query.message.reply_text(
                "🔐 Abonne-toi à la chaîne du développeur "
                "pour accéder au laboratoire."
            )

    elif query.data == "check_channel":
        if await has_channel_access(query.from_user.id, context):
            await query.message.reply_text(
                "✅ Abonnement vérifié ! Accès autorisé."
            )
        else:
            await query.message.reply_text(
                "❌ Je ne peux pas confirmer ton abonnement. "
                "Rejoins la chaîne puis réessaie."
            )


# ═══════════════════════════════════
# GLITCH LAB — SIMULATIONS VISUELLES
# ═══════════════════════════════════

async def bugmenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_channel(update, context):
        return

    await update.effective_message.reply_text(
        royal_box(
            "🍓 𝐏𝐇𝐄𝐍𝐈𝐗 𝐋𝐀𝐁",
            [
                "/bug — anomalie",
                "/glitch — Texte glitch",
                "/error — Erreur",
                "/load — Chargement",
                "/matrix — Matrix",
                "/diagnostic — Diagnostic",
                "/stop — Arrêter",
            ],
        )
    )


async def real(update, context, title, steps):
    if not await require_channel(update, context):
        return

    message = await update.effective_message.reply_text(
        f"╭─〔 🍓 {title} 〕─╮\n"
        "│ Initialisation...\n"
        "╰────────────────╯"
    )

    task_key = (update.effective_chat.id, update.effective_user.id)

    async def run_animation():
        try:
            for step in steps:
                await asyncio.sleep(2)

                await message.edit_text(
                    f"╭─〔 🍓 {title} 〕─╮\n"
                    f"│ {step}\n"
                    "│ il vas etre off putain.\n"
                    "╰────────────────╯"
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logging.exception("Erreur pendant la l'anomalie")
        finally:
            FAKE_TASKS.pop(task_key, None)

    old_task = FAKE_TASKS.get(task_key)

    if old_task and not old_task.done():
        old_task.cancel()

    FAKE_TASKS[task_key] = asyncio.create_task(run_animation())


async def bugfake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await simulate(
        update,
        context,
        "BUG REPORTING IN PROGRESS",
        [
            "Analyse fictive en cours...",
            "Anomalie détectée...",
            "Correction...",
            "Terminé",
        ],
    )


async def glitch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await simulate(
        update,
        context,
        "GLITCH EFFECT",
        [
            "G̷l̷i̷t̷c̷h̷ ̷s̷y̷s̷t̷e̷m̷...",
            "Signal visuel instable...",
            "transmission terminé.",
        ],
    )


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await simulate(
        update,
        context,
        "ERREUR",
        [
            "ERREUR DEMO-001...",
            "Diagnostic fictif en cours...",
            "Aucune erreur détectée.",
        ],
    )


async def load(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await simulate(
        update,
        context,
        "CHARGEMENT",
        [
            "Chargement : 25 %...",
            "Chargement : 50 %...",
            "Chargement : 75 %...",
            "Chargement : 100 % — Terminé !",
        ],
    )


async def matrix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await simulate(
        update,
        context,
        "MATRIX DEMO",
        [
            "010101 110010 001101",
            "101010 001110 111000",
            "terminée.",
        ],
    )


async def diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await simulate(
        update,
        context,
        "DIAGNOSTIC FICTIF",
        [
            "Vérification visuelle...",
            "Connexion : simulation uniquement.",
            "Résultat : démonstration terminée.",
        ],
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = (update.effective_chat.id, update.effective_user.id)
    task = FAKE_TASKS.get(key)

    if task and not task.done():
        task.cancel()
        await update.effective_message.reply_text(
            "╭─〔 🍓 TRANSMISSION ARRÊTÉE 〕─╮\n"
            "│ La transmission est terminée.\n"
            "╰────────────────╯"
        )
    else:
        await update.effective_message.reply_text(
            "Aucune bug active."
        )
        # ═══════════════════════════════════════
# PARTIE 3 — JEUX ET MODÉRATION
# ═══════════════════════════════════════

import re
import time
from collections import defaultdict, deque
from datetime import timedelta

# Mémoire des jeux et détection du spam
GAME_DATA = {}
USER_MESSAGES = defaultdict(deque)
SPAM_COOLDOWN = {}

QUIZZES = [
    {
        "question": "Quelle planète est surnommée la planète rouge ?",
        "answer": "mars",
    },
    {
        "question": "Combien font 7 × 8 ?",
        "answer": "56",
    },
    {
        "question": "Quel est le satellite naturel de la Terre ?",
        "answer": "la lune",
    },
]

RIDDLES = [
    {
        "question": "Qu'est-ce qui a des dents mais ne mange pas ?",
        "answer": "un peigne",
    },
    {
        "question": "Qu'est-ce qui monte mais ne redescend jamais ?",
        "answer": "l'âge",
    },
]

# ═══════════════════════════════════════
# JEUX
# ═══════════════════════════════════════

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    item = random.choice(QUIZZES)
    chat_id = update.effective_chat.id

    GAME_DATA[chat_id] = {
        "type": "quiz",
        "answer": item["answer"].lower(),
    }

    await update.effective_message.reply_text(
        royal_box(
            "🎮 QUIZ ROYAL",
            [
                item["question"],
                "Réponds directement dans la discussion.",
                "Commande : /score",
            ],
        )
    )


async def devinette(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    item = random.choice(RIDDLES)
    chat_id = update.effective_chat.id

    GAME_DATA[chat_id] = {
        "type": "riddle",
        "answer": item["answer"].lower(),
    }

    await update.effective_message.reply_text(
        royal_box(
            "🧩 DEVINETTE",
            [
                item["question"],
                "Écris ta réponse dans la discussion.",
            ],
        )
    )


async def nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    number_to_guess = random.randint(1, 20)

    GAME_DATA[chat_id] = {
        "type": "number",
        "answer": str(number_to_guess),
    }

    await update.effective_message.reply_text(
        "🎲 J'ai choisi un nombre entre 1 et 20.\n"
        "Essaie de le deviner !"
    )


async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    points = context.user_data.get("score", 0)

    await update.effective_message.reply_text(
        royal_box(
            "🏆 TON SCORE",
            [
                f"Joueur : {update.effective_user.first_name}",
                f"Points : {points}",
            ],
        )
    )


async def game_answers(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message

    if not message or not message.text:
        return

    if message.text.startswith("/"):
        return

    chat_id = update.effective_chat.id
    game = GAME_DATA.get(chat_id)

    if not game:
        return

    answer = message.text.strip().lower()
    correct = game["answer"]

    if answer == correct:
        GAME_DATA.pop(chat_id, None)

        context.user_data["score"] = (
            context.user_data.get("score", 0) + 1
        )

        await message.reply_text(
            f"👑 Bravo {update.effective_user.first_name} !\n"
            "✅ Bonne réponse ! +1 point."
        )

    elif game["type"] == "number" and answer.isdigit():
        target = int(correct)
        guess = int(answer)

        if guess < target:
            await message.reply_text("⬆️ Essaie un nombre plus grand.")
        elif guess > target:
            await message.reply_text("⬇️ Essaie un nombre plus petit.")


# ═══════════════════════════════════════
# VÉRIFICATION DES ADMINISTRATEURS
# ═══════════════════════════════════════

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user or chat.type == "private":
        return False

    try:
        member = await context.bot.get_chat_member(
            chat.id,
            user.id,
        )

        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )

    except Exception:
        return False


# ═══════════════════════════════════════
# MUTE / UNMUTE
# ═══════════════════════════════════════

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.effective_message.reply_text(
            "⛔ Réservé aux administrateurs du groupe."
        )
        return

    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text(
            "Utilisation : réponds au message du membre avec /mute"
        )
        return

    target = message.reply_to_message.from_user

    if target.is_bot:
        await message.reply_text("Je ne peux pas appliquer cette action à un bot.")
        return

    minutes = 60

    if context.args:
        try:
            minutes = int(context.args[0])
        except ValueError:
            await message.reply_text("Indique une durée en minutes.")
            return

    minutes = max(1, min(minutes, 2880))

    try:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target.id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            ),
            until_date=timedelta(minutes=minutes),
        )

        await message.reply_text(
            f"🔇 {target.first_name} est en sourdine "
            f"pendant {minutes} minute(s)."
        )

    except Exception as error:
        logging.warning("Mute impossible : %s", error)
        await message.reply_text(
            "❌ Action impossible. Vérifie que le bot est administrateur "
            "et possède les permissions nécessaires."
        )


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.effective_message.reply_text(
            "⛔ Réservé aux administrateurs."
        )
        return

    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text(
            "Réponds au message du membre avec /unmute."
        )
        return

    target = message.reply_to_message.from_user

    try:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )

        await message.reply_text(
            f"🔊 {target.first_name} peut de nouveau écrire."
        )

    except Exception as error:
        logging.warning("Unmute impossible : %s", error)
        await message.reply_text(
            "❌ Impossible de retirer la restriction. "
            "Vérifie les permissions du bot."
        )


# ═══════════════════════════════════════
# BAN / UNBAN
# ═══════════════════════════════════════

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.effective_message.reply_text(
            "⛔ Réservé aux administrateurs."
        )
        return

    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text(
            "Réponds au message du membre avec /ban."
        )
        return

    target = message.reply_to_message.from_user

    if target.is_bot:
        await message.reply_text("Impossible de bannir un bot avec cette commande.")
        return

    try:
        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target.id,
        )

        await message.reply_text(
            f"🚫 {target.first_name} a été banni du groupe."
        )

    except Exception as error:
        logging.warning("Ban impossible : %s", error)
        await message.reply_text(
            "❌ Bannissement impossible. Vérifie les permissions."
        )


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.effective_message.reply_text(
            "⛔ Réservé aux administrateurs."
        )
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Utilisation : /unban ID_UTILISATEUR"
        )
        return

    try:
        target_id = int(context.args[0])

        await context.bot.unban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=target_id,
            only_if_banned=True,
        )

        await update.effective_message.reply_text(
            "✅ Vérification de débannissement effectuée."
        )

    except ValueError:
        await update.effective_message.reply_text(
            "❌ L'identifiant doit être numérique."
        )

    except Exception as error:
        logging.warning("Unban impossible : %s", error)
        await update.effective_message.reply_text(
            "❌ Impossible de débannir cet utilisateur."
        )


# ═══════════════════════════════════════
# ANTI-LIEN ET ANTI-SPAM
# ═══════════════════════════════════════

LINK_PATTERN = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/)",
    re.IGNORECASE,
)


async def moderate_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message or not user or not chat:
        return

    if chat.type == "private" or user.is_bot:
        return

    if await is_admin(update, context):
        return

    text = message.text or message.caption or ""

    # Anti-liens
    if LINK_PATTERN.search(text):
        try:
            await message.delete()

            await context.bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_audios=False,
                    can_send_documents=False,
                    can_send_photos=False,
                    can_send_videos=False,
                    can_send_video_notes=False,
                    can_send_voice_notes=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                ),
                until_date=timedelta(hours=48),
            )

            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    "╭─〔 ⚠️ 𝐀𝐍𝐓𝐈-𝐋𝐈𝐍𝐊 〕─╮\n"
                    f"│ 𝗠𝗲𝗺𝗯𝗿𝗲 : {user.first_name}\n"
                    "│ 𝗣𝗲𝘁𝗶𝘁 𝗰𝗼𝗻 𝗹𝗲𝘀 𝗹𝗶𝗲𝗻 𝘀𝗼𝗻 𝗽𝗮𝘀 𝗮𝘂𝘁𝗼𝗿𝗶𝘀é 𝗶𝗰𝗶 𝗹𝗶𝗲𝗻 𝘀𝘂𝗽𝗽𝗿𝗶𝗺é .\n"
                    "│ 𝗥𝗲𝘀𝘁𝗿𝗶𝗰𝘁𝗶𝗼𝗻 𝗮𝗽𝗽𝗹𝗶𝗾𝘂é𝗲 𝗽𝗼𝘂𝗿 48𝗵 𝗵𝗲𝘂𝗿 𝘀𝗶 𝘁'𝗲𝘀 𝗳𝗮𝗰𝗵é 𝗱𝗺 𝗺𝗲 𝗽𝗲𝘁𝗶𝘁 ✈.\n"
                    "╰────────────────╯"
                ),
            )

        except Exception as error:
            logging.warning("Modération des liens impossible : %s", error)

        return

    # Anti-spam : maximum 6 messages sur une fenêtre de 8 secondes
    now = time.time()
    key = (chat.id, user.id)
    history = USER_MESSAGES[key]

    while history and now - history[0] > 8:
        history.popleft()

    history.append(now)

    if len(history) > 6:
        last_restriction = SPAM_COOLDOWN.get(key, 0)

        if now - last_restriction > 60:
            SPAM_COOLDOWN[key] = now
            history.clear()

            try:
                await context.bot.restrict_chat_member(
                    chat_id=chat.id,
                    user_id=user.id,
                    permissions=ChatPermissions(
                        can_send_messages=False,
                        can_send_audios=False,
                        can_send_documents=False,
                        can_send_photos=False,
                        can_send_videos=False,
                        can_send_video_notes=False,
                        can_send_voice_notes=False,
                        can_send_polls=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                    ),
                    until_date=timedelta(minutes=1),
                )

                await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        "╭─〔 🛡️𝐀𝐍𝐓𝐈-𝐒𝐏𝐀𝐌 〕─╮\n"
                        f"│ {user.first_name}\n"
                        "│ 𝗧𝗿𝗼𝗽 𝗱𝗲 𝗺𝗲𝘀𝘀𝗮𝗴𝗲𝘀 𝗲𝗻 𝗽𝗲𝘂 𝗱é 𝘁𝗲𝗺𝗽𝘀 𝗳𝗮𝘂𝘁 𝗽𝗮𝘀 é𝘁𝗿𝗲 𝗰𝗼𝗻 𝗶𝗰𝗶 𝗰 𝗹𝗲 𝗴𝗿𝗼𝘂𝗽𝗲 𝗱𝗲 𝘁𝗼𝗻 𝗽𝗲𝗿𝗲 ?〄.\n"
                        "│ 𝗥𝗲𝘀𝘁𝗿𝗶𝗰𝘁𝗶𝗼𝗻 : 5 𝗺𝗶𝗻𝘂𝘁𝗲.\n"
                        "╰────────────────╯"
                    ),
                )

            except Exception as error:
                logging.warning("Anti-spam impossible : %s", error)

        return

    await game_answers(update, context)


# ═══════════════════════════════════════
# BIENVENUE / DÉPART
# ═══════════════════════════════════════

async def welcome(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    event = update.chat_member

    if not event:
        return

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    member_statuses = {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    }

    old_member = old_status in member_statuses
    new_member = new_status in member_statuses

    user = event.new_chat_member.user
    chat_id = update.effective_chat.id

    if user.is_bot:
        return

    if not old_member and new_member:
        text = royal_box(
            "👑 🅑🅘🅔🅝🅥🅔🅝🅤🅔",
            [
                f"𝗕𝗶𝗲𝗻𝘃𝗲𝗻𝘂𝗲 {user.first_name} !",
                "𝗦𝗼𝗶𝘀 𝗵𝗲𝘂𝗿𝗲𝘂𝘅 𝗱'𝗲𝘁𝗿𝗲𝘀 𝗽𝗮𝗿𝗺𝗶 𝗹𝗲𝘀 𝗽𝘂𝗶𝘀𝘀𝗮𝗻𝘁 𝗿𝗲𝘀𝗽𝗲𝗰𝘁𝗲 𝗹𝗲𝘀 𝗺𝗲𝗺𝗲𝗯𝗿𝗲𝘀 𝗲𝘁 𝗹𝗲𝘀 𝗿𝗲𝗴𝗹𝗲𝘀 𝘀𝗮𝗻𝘀 𝗼𝘂𝗯𝗹𝗶é 𝗹𝗲 𝗿𝗼𝗶 @Mr_king_kayseur 卍.",
                "Utilise /rules pour consulter les règles.",
            ],
        )

        await send_styled(context, chat_id, text, START_IMAGE)

    elif old_member and not new_member:
        text = royal_box(
            "🌙 🅓🅔🅟🅐🅡🅣",
            [
                f"{user.first_name} 𝗮 𝗾𝘂𝗶𝘁𝘁é 𝗹𝗲 𝗴𝗿𝗼𝘂𝗽𝗲 𝘁𝘂 𝗾𝘂𝗶𝘁𝘁𝗲 𝗹𝗲 𝗴𝗿𝗼𝘂𝗽𝗲 𝘀𝗹𝗺 𝗰𝗼𝗺𝗺𝗲 ç𝗮 𝘁'𝗲𝘀 𝘂𝗻 𝘃𝗿𝗮𝗶 𝗰𝗼𝗻 𝘄𝗲𝘀𝗵.",
                "🍾 𝗕𝗿𝗲𝗳 𝗯𝘆𝗲 𝗻𝗲 𝗿𝗲𝘃𝗶𝗲𝗻𝘁 𝗽𝗹𝘂𝘀 𝗯𝗼𝗻𝗻𝗲 𝗰𝗼𝗻𝘁𝗶𝗻𝘂𝗮𝘁𝗶𝗼𝗻 ! 🖕",
            ],
        )

        await send_styled(context, chat_id, text, START_IMAGE)


# ═══════════════════════════════════════
# LANCEMENT DU BOT
# ═══════════════════════════════════════

def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "BOT_TOKEN absent. Ajoute le token dans les variables "
            "d'environnement de ton hébergeur."
        )

    application = Application.builder().token(token).build()

    # Commandes générales
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", user_id))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("rules", rules))

    # Jeux
    application.add_handler(CommandHandler("quiz", quiz))
    application.add_handler(CommandHandler("devinette", devinette))
    application.add_handler(CommandHandler("nombre", nombre))
    application.add_handler(CommandHandler("score", score))

    # Laboratoire de simulations
    application.add_handler(CommandHandler("bugmenu", bugmenu))
    application.add_handler(CommandHandler("bugfake", bugfake))
    application.add_handler(CommandHandler("glitch", glitch))
    application.add_handler(CommandHandler("fakeerror", fakeerror))
    application.add_handler(CommandHandler("fakeload", fakeload))
    application.add_handler(CommandHandler("matrix", matrix))
    application.add_handler(CommandHandler("diagnostic", diagnostic))
    application.add_handler(CommandHandler("stopfake", stopfake))

    # Modération
    application.add_handler(CommandHandler("mute", mute))
    application.add_handler(CommandHandler("unmute", unmute))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("unban", unban))

    # Boutons interactifs
    application.add_handler(CallbackQueryHandler(button_handler))

    # Arrivées et départs
    application.add_handler(
        ChatMemberHandler(
            welcome,
            ChatMemberHandler.CHAT_MEMBER,
        )
    )

    # Messages ordinaires : anti-lien, anti-spam et jeux
    application.add_handler(
        MessageHandler(
            (filters.TEXT & ~filters.COMMAND) | filters.CAPTION,
            moderate_messages,
        )
    )

    logging.info("PHÉNIX GUY démarre...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
