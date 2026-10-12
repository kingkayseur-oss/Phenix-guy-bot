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
START_IMAGE = "https://ibb.co/ycWd72ZM"

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


# ═══════ COMMANDES GÉNÉRALES ═══════

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = main_menu_text(user)
    keyboard = None
    if configured_channel():
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📢 Rejoindre la chaîne", url=CHANNEL_URL)]]
        )
    try:
        if START_IMAGE:
            await update.message.reply_photo(
                photo=START_IMAGE, caption=text, reply_markup=keyboard
            )
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
    except Exception:
        await update.message.reply_text(text, reply_markup=keyboard)


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(main_menu_text(update.effective_user))


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        royal_box("𝐀𝐈𝐃𝐄", ["Utilise /menu pour voir toutes les commandes."])
    )


async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text(
        royal_box(
            "𝐈𝐃𝐄𝐍𝐓𝐈𝐅𝐈𝐀𝐍𝐓𝐒",
            [f"𝐔𝐬𝐞𝐫 𝐈𝐃 : {user.id}", f"𝐂𝐡𝐚𝐭 𝐈𝐃 : {chat.id}"],
        )
    )


async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        royal_box(
            "𝐈𝐍𝐅𝐎 𝐔𝐓𝐈𝐋𝐈𝐒𝐀𝐓𝐄𝐔𝐑",
            [
                f"𝐍𝐨𝐦 : {user.full_name}",
                f"𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞 : @{user.username or 'aucun'}",
                f"𝐈𝐃 : {user.id}",
            ],
        )
    )


async def rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        royal_box(
            "𝐑È𝐆𝐋𝐄𝐒",
            [
                "1. Respect entre membres.",
                "2. Pas de spam.",
                "3. Pas de contenu illégal.",
                "4. Écoute les admins.",
            ],
        )
    )


# ═══════ GLITCH LAB (fun) ═══════

async def bugmenu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        royal_box(
            "𝐆𝐋𝐈𝐓𝐂𝐇 𝐋𝐀𝐁",
            ["/bug", "/glitch", "/ferror", "/load", "/matrix", "/diagnostic"],
        )
    )


async def bug_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🐞 Bug détecté : {random.choice(FAKE_TASKS)}")


async def glitch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    glitch_text = "".join(random.choice("#@$%&/\\*01") for _ in range(20))
    await update.message.reply_text(f"⚡ GLITCH : {glitch_text}")


async def ferror_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ FATAL ERROR 0x" + str(random.randint(1000, 9999)))


async def load_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Chargement...")
    for pct in (25, 50, 75, 100):
        await asyncio.sleep(0.6)
        await msg.edit_text(f"⏳ Chargement... {pct}%")


async def matrix_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["".join(random.choice("01") for _ in range(20)) for _ in range(5)]
    await update.message.reply_text("```\n" + "\n".join(lines) + "\n```", parse_mode="Markdown")


async def diagnostic_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        royal_box("𝐃𝐈𝐀𝐆𝐍𝐎𝐒𝐓𝐈𝐂", ["Tous les systèmes sont opérationnels. ✅"])
    )


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 Arrêt des processus simulés.")


# ═══════ MODÉRATION ═══════

async def _get_target_user(update):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user
    return None


async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("🚫 Réservé aux admins.")
        return
    target = await _get_target_user(update)
    if not target:
        await update.message.reply_text("Réponds au message de la personne à bannir.")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"🔨 {target.full_name} a été banni.")
    except Exception as e:
        await update.message.reply_text(f"Erreur : {e}")


async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("🚫 Réservé aux admins.")
        return
    if not context.args:
        await update.message.reply_text("Utilise /unban <user_id>")
        return
    try:
        user_id = int(context.args[0])
        await context.bot.unban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text("✅ Utilisateur débanni.")
    except Exception as e:
        await update.message.reply_text(f"Erreur : {e}")


async def mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("🚫 Réservé aux admins.")
        return
    target = await _get_target_user(update)
    if not target:
        await update.message.reply_text("Réponds au message de la personne à mute.")
        return
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target.id,
            permissions=ChatPermissions(can_send_messages=False),
        )
        await update.message.reply_text(f"🔇 {target.full_name} a été mute.")
    except Exception as e:
        await update.message.reply_text(f"Erreur : {e}")


async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("🚫 Réservé aux admins.")
        return
    target = await _get_target_user(update)
    if not target:
        await update.message.reply_text("Réponds au message de la personne à démute.")
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
        await update.message.reply_text(f"🔊 {target.full_name} a été démute.")
    except Exception as e:
        await update.message.reply_text(f"Erreur : {e}")


# ═══════ JEUX ═══════

async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question, answer = random.choice(QUIZZES)
    context.chat_data["quiz_answer"] = answer.lower()
    await update.message.reply_text(f"🧠 QUIZ : {question}")


async def devinette_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question, answer = random.choice(RIDDLES)
    context.chat_data["quiz_answer"] = answer.lower()
    await update.message.reply_text(f"🔎 DEVINETTE : {question}")


async def nombre_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    NUMBER_GAMES[update.effective_chat.id] = random.randint(1, 100)
    await update.message.reply_text("🔢 J'ai pensé à un nombre entre 1 et 100. Devine-le !")


async def score_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pts = SCORES.get(user.id, 0)
    await update.message.reply_text(f"🏆 Ton score : {pts} point(s).")


# ═══════ MESSAGES TEXTE (jeux + anti-spam) ═══════

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text.strip()

    # Anti-spam
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

    # Réponse quiz/devinette
    expected = context.chat_data.get("quiz_answer")
    if expected and text.lower() == expected:
        SCORES[user.id] += 1
        context.chat_data["quiz_answer"] = None
        await update.message.reply_text(f"✅ Bonne réponse {user.first_name} ! +1 point.")
        return

    # Jeu du nombre mystère
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
        text = f"👑 Bienvenue {user.mention_html()} dans le royaume !"
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
        text = f"👋 {user.full_name} a quitté le royaume."
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
    app.add_handler(CommandHandler("glitch", glitch_cmd))
    app.add_handler(CommandHandler("ferror", ferror_cmd))
    app.add_handler(CommandHandler("load", load_cmd))
    app.add_handler(CommandHandler("matrix", matrix_cmd))
    app.add_handler(CommandHandler("diagnostic", diagnostic_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))

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
 
