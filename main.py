import os
import random
import logging
from datetime import datetime, timedelta, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatMemberStatus
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

TOKEN = os.environ.get("BOT_TOKEN")
BOT_NAME = "PHÉNIX GUY"

WELCOME = (
    "╭━━━〔 👑 𝐏𝐇É𝐍𝐈𝐗 𝐆𝐔𝐘 〕━━━╮\n\n"
    "✨ Bienvenue {name} !\n"
    "💜 Heureux de t'accueillir dans notre communauté.\n"
    "🤝 Respecte les membres et profite de l'ambiance !\n\n"
    "╰━━━━━━〔 ⚡ 𝐅𝐀𝐌𝐈𝐋𝐘 〕━━━━━━╯"
)

GOODBYE = (
    "╭━━━〔 🥀 𝐀𝐔 𝐑𝐄𝐕𝐎𝐈𝐑 〕━━━╮\n\n"
    "🌙 {name} vient de quitter le groupe.\n"
    "💜 Merci pour le moment partagé avec nous.\n"
    "✨ Bonne continuation !\n\n"
    "╰━━━━━━〔 👑 𝐏𝐇É𝐍𝐈𝐗 𝐆𝐔𝐘 〕━━━━━━╯"
)

MENU = (
    "╔════════════════════╗\n"
    "      👑 𝐏𝐇É𝐍𝐈𝐗 𝐆𝐔𝐘 👑\n"
    "╚════════════════════╝\n\n"
    "💠 libolo\n"
    "┏━━━━━━━━━━━━━━━━━━\n"
    "┃ /start — Démarrer le bot\n"
    "┃ /menu — Afficher le menu\n"
    "┃ /help — Aide\n"
    "┃ /id — Ton identifiant\n"
    "┃ /info — Infos du groupe\n"
    "┗━━━━━━━━━━━━━━━━━━\n\n"
    "🛡️ makata\n"
    "┏━━━━━━━━━━━━━━━━━━\n"
    "┃ /ban — Bannir un membre\n"
    "┃ /unban — Débannir un membre\n"
    "┃ /mute — Restreindre un membre\n"
    "┃ /unmute — Autoriser à écrire\n"
    "┃ /rules — Règles du groupe\n"
    "┗━━━━━━━━━━━━━━━━━━\n\n"
    "🎮 𝐉𝐄𝐔𝐗\n"
    "┏━━━━━━━━━━━━━━━━━━\n"
    "┃ /quiz — Question mystère\n"
    "┃ /devinette — Devinette\n"
    "┃ /nombre — Deviner un nombre\n"
    "┃ /score — Ton score\n"
    "┗━━━━━━━━━━━━━━━━━━\n\n"
    "⚙️ 𝐏𝐑É𝐅𝐈𝐗 : / (slash)\n"
    "👑 𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐛𝐲 @Mr_king_kayseur"
)

QUIZZES = [
    ("Quelle est la planète rouge ?", "mars"),
    ("Combien de jours y a-t-il dans une semaine ?", "7"),
    ("Quel animal est surnommé le roi des animaux ?", "lion"),
    ("Combien font 8 × 7 ?", "56"),
]

RIDDLES = [
    ("Je monte et je descends sans bouger. Qui suis-je ?", "escalier"),
    ("J'ai des aiguilles, mais je ne couds pas. Qui suis-je ?", "horloge"),
    ("Plus je sèche, plus je deviens mouillée. Qui suis-je ?", "serviette"),
]

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.effective_user:
        return False
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 Ouvrir le menu", callback_data="menu")],
        [InlineKeyboardButton("🎮 Jouer au quiz", callback_data="quiz")],
    ])
    await update.effective_message.reply_text(
        "╭━━〔 👑 PHÉNIX GUY 👑 〕━━╮\n\n"
        "🔥 Salut ! Je suis PHÉNIX GUY.\n"
        "🛡️ Je peux aider à gérer ton groupe.\n"
        "🎮 Je propose aussi des jeux.\n\n"
        "╰━━〔 Utilise les boutons ci-dessous 〕━━╯",
        reply_markup=keyboard,
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(MENU)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "menu":
        await query.message.reply_text(MENU)
    elif query.data == "quiz":
        await quiz(update, context, from_button=True)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Besoin d'aide ? Utilise /menu pour voir les commandes disponibles."
    )

async def user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.effective_message.reply_text(
        f"🆔 Ton identifiant Telegram : {user.id}"
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await update.effective_message.reply_text(
        f"╭━━〔 📊 INFOS 〕━━╮\n"
        f"Nom : {chat.title or 'Discussion privée'}\n"
        f"Identifiant : {chat.id}\n"
        f"╰━━━━━━━━━━━━━━╯"
    )

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "╭━━〔 📜 RÈGLES DU GROUPE 〕━━╮\n"
        "┃ 🤝 Respect entre les membres\n"
        "┃ 🔗 Pas de liens publicitaires interdits\n"
        "┃ 🚫 Pas de spam\n"
        "┃ 💜 Respecte les administrateurs\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯"
    )

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    old = result.old_chat_member.status
    new = result.new_chat_member.status
    user = result.new_chat_member.user

    joined = (
        new in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR)
        and old not in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    )
    left = (
        old in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
        and new in (
            ChatMemberStatus.LEFT,
            ChatMemberStatus.BANNED,
        )
    )

    if user.is_bot:
        return

    name = user.first_name
    if joined:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=WELCOME.format(name=name),
        )
    elif left:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=GOODBYE.format(name=name),
        )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE,
               from_button=False):
    question, answer = random.choice(QUIZZES)
    context.chat_data["quiz_answer"] = answer
    await update.effective_message.reply_text(
        f"╭━━〔 🎮 QUIZ PHÉNIX 〕━━╮\n\n"
        f"❓ {question}\n\n"
        f"Réponds dans le groupe !\n"
        f"╰━━━━━━━━━━━━━━━━━━╯"
    )

async def devinette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question, answer = random.choice(RIDDLES)
    context.chat_data["riddle_answer"] = answer
    await update.effective_message.reply_text(
        f"🧩 DEVINETTE : {question}"
    )

async def nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["number_answer"] = random.randint(1, 10)
    await update.effective_message.reply_text(
        "🎯 Devine un nombre entre 1 et 10 ! Réponds dans le groupe."
    )

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    points = context.user_data.get("score", 0)
    await update.effective_message.reply_text(
        f"🏆 Ton score PHÉNIX : {points} point(s)."
    )

async def game_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.text or not update.effective_user:
        return

    text = message.text.strip().lower()
    answer = context.chat_data.get("quiz_answer")
    riddle = context.chat_data.get("riddle_answer")
    number = context.chat_data.get("number_answer")

    correct = (
        (answer is not None and text == answer)
        or (riddle is not None and text == riddle)
        or (number is not None and text == str(number))
    )
    if correct:
        context.chat_data.pop("quiz_answer", None)
        context.chat_data.pop("riddle_answer", None)
        context.chat_data.pop("number_answer", None)
        context.user_data["score"] = context.user_data.get("score", 0) + 1
        await message.reply_text(
            f"🏆 Bravo {update.effective_user.first_name} ! +1 point."
        )

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.effective_message.reply_text(
            "⛔ Cette commande est réservée aux administrateurs."
        )
        return
    if not update.effective_message.reply_to_message:
        await update.effective_message.reply_text(
            "Réponds au message du membre avec /mute."
        )
        return

    user = update.effective_message.reply_to_message.from_user
    seconds = 3600
    if context.args:
        try:
            seconds = max(60, min(int(context.args[0]) * 60, 172800))
        except ValueError:
            pass

    until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user.id,
            permissions=__import__(
                "telegram"
            ).ChatPermissions(can_send_messages=False),
            until_date=until,
        )
        await update.effective_message.reply_text(
            f"🔇 {user.first_name} ne peut plus écrire temporairement."
        )
    except Exception:
        await update.effective_message.reply_text(
            "⚠️ Vérifie que je suis administrateur avec le droit de restreindre."
        )

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not update.effective_message.reply_to_message:
        await update.effective_message.reply_text(
            "Réponds au message du membre avec /unmute."
        )
        return
    user = update.effective_message.reply_to_message.from_user
    from telegram import ChatPermissions
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user.id,
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
        await update.effective_message.reply_text(
            f"🔊 {user.first_name} peut de nouveau écrire."
        )
    except Exception:
        await update.effective_message.reply_text(
            "⚠️ Je n'ai pas pu rétablir ses permissions."
        )

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    reply = update.effective_message.reply_to_message
    if not reply:
        await update.effective_message.reply_text(
            "Réponds au message du membre avec /ban."
        )
        return
    try:
        await context.bot.ban_chat_member(
            update.effective_chat.id, reply.from_user.id
        )
        await update.effective_message.reply_text("🔨 Membre banni.")
    except Exception:
        await update.effective_message.reply_text(
            "⚠️ Vérifie mes droits d'administration."
        )

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text(
            "Utilisation : /unban ID_UTILISATEUR"
        )
        return
    try:
        await context.bot.unban_chat_member(
            update.effective_chat.id, int(context.args[0])
        )
        await update.effective_message.reply_text("✅ Bannissement annulé.")
    except Exception:
        await update.effective_message.reply_text(
            "⚠️ Impossible de débannir ce membre."
        )

async def links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message or not user or user.is_bot:
        return
    if chat.type == "private":
        return
    if await is_admin(update, context):
        return

    text = message.text or message.caption or ""
    entities = list(message.entities or []) + list(message.caption_entities or [])
    has_link = any(
        entity.type in ("url", "text_link")
        for entity in entities
    ) or "http://" in text.lower() or "https://" in text.lower() or "t.me/" in text.lower() or "www." in text.lower()

    if not has_link:
        await game_answers(update, context)
        return

    try:
        await message.delete()
        until = datetime.now(timezone.utc) + timedelta(hours=48)
        from telegram import ChatPermissions
        await context.bot.restrict_chat_member(
            chat.id,
            user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until,
        )
        await context.bot.send_message(
            chat.id,
            f"╭━━〔 🛡️ PHÉNIX SECURITY 〕━━╮\n\n"
            f"⚠️ {user.first_name}, lien interdit détecté.\n"
            f"🔇 Restriction appliquée pendant 48 heures.\n\n"
            f"╰━━━━━━━━━━━━━━━━━━╯",
        )
    except Exception:
        logging.exception("Erreur de modération des liens")

def main():
    if not TOKEN:
        raise RuntimeError("La variable BOT_TOKEN n'est pas configurée.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("id", user_id))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("devinette", devinette))
    app.add_handler(CommandHandler("nombre", nombre))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, links))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
