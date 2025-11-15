import os
import json
import asyncio
import threading
from queue import Queue
from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters as tg_filters
)

# ===========================================================
# ENV VARIABLES
# ===========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = 21705136
API_HASH = "78730e89d196e160b0f1992018c6cb19"
STRING_SESSION = os.environ.get("STRING_SESSION")
USERBOT_ID = int(os.environ.get("USERBOT_ID"))  # Your userbot's Telegram ID

DATA_FILE = "accepted_users.json"
WELCOME_MSG_FILE = "welcome_msg.txt"

WELCOME_MSG_DEFAULT = "Hello! Your request has been approved ✔\nWelcome ❤️"

# ===========================================================
# SHARED QUEUE (userbot → bot)
# ===========================================================
approved_queue = Queue()

# ===========================================================
# STORAGE FUNCTIONS
# ===========================================================
def load_users():
    try:
        with open(DATA_FILE, "r") as f:
            return set(json.load(f).get("users", []))
    except:
        return set()

def save_users(u):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": list(u)}, f)

ACCEPTED_USERS = load_users()

def get_welcome_msg():
    try:
        with open(WELCOME_MSG_FILE, "r", encoding="utf-8") as f:
            return f.read().strip() or WELCOME_MSG_DEFAULT
    except:
        return WELCOME_MSG_DEFAULT


# ===========================================================
# USERBOT (Pyrogram) - Approves ALL requests
# ===========================================================

userbot = Client(
    "userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION
)


async def approve_all_requests(chat_id: int):
    async for req in userbot.get_chat_join_requests(chat_id):
        uid = req.user.id

        try:
            await userbot.approve_chat_join_request(chat_id, uid)
        except:
            pass

        # queue → bot will DM
        approved_queue.put((uid, chat_id))


@userbot.on_chat_member_updated()
async def bot_added(client, event):
    """When bot is added, approve old pending requests."""
    if event.new_chat_member and event.new_chat_member.user.is_bot:
        bot_id = event.new_chat_member.user.id

        if bot_id == userbot.me.id:
            return

        print("📌 BOT added → scanning & approving old pending requests…")

        await approve_all_requests(event.chat.id)


async def userbot_main():
    await userbot.start()
    print("USERBOT RUNNING…\nApproving existing requests on all chats...")

    # Approve all chats at startup
    async for dialog in userbot.get_dialogs():
        chat = dialog.chat
        if chat.type in ["supergroup", "channel"]:
            await approve_all_requests(chat.id)

    await asyncio.Event().wait()  # keep running


# ===========================================================
# BOT (python-telegram-bot)
# ===========================================================

bot_app = ApplicationBuilder().token(BOT_TOKEN).build()


async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot online ✔\nUse /setmsg to update DM text.")


async def setmsg_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = " ".join(ctx.args).strip()
    if not text:
        return await update.message.reply_text("Usage: /setmsg Hello welcome…")

    with open(WELCOME_MSG_FILE, "w", encoding="utf-8") as f:
        f.write(text)

    await update.message.reply_text("✔ Custom DM updated.")


async def broadcast_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = " ".join(ctx.args).strip()

    if not msg:
        return await update.message.reply_text("Usage: /broadcast text")

    ok = 0
    fail = 0

    for uid in ACCEPTED_USERS:
        try:
            await bot_app.bot.send_message(uid, msg)
            ok += 1
        except:
            fail += 1

        await asyncio.sleep(0.25)

    await update.message.reply_text(f"Broadcast done ✔\nSent: {ok}\nFailed: {fail}")


async def auto_add_userbot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """When bot is added to group → add + promote userbot."""
    chat = update.effective_chat

    # 1. add userbot
    try:
        await ctx.bot.add_chat_member(chat.id, USERBOT_ID)
    except:
        pass

    # 2. promote userbot
    try:
        await ctx.bot.promote_chat_member(
            chat.id,
            USERBOT_ID,
            can_manage_chat=True,
            can_invite_users=True,
            can_promote_members=True
        )
    except:
        pass

    await update.message.reply_text("✔ Userbot added & promoted.\nApproving old requests…")


async def new_approve_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """New incoming bot join requests (handled by bot)."""
    jr = update.chat_join_request
    uid = jr.from_user.id

    try:
        await ctx.bot.approve_chat_join_request(jr.chat.id, uid)
    except:
        pass

    # queue for bot to DM
    approved_queue.put((uid, jr.chat.id))


# ===========================================================
# BOT LOOP – PROCESS QUEUE (DM sending)
# ===========================================================
async def queue_processor():
    while True:
        while not approved_queue.empty():
            uid, chat_id = approved_queue.get()

            ACCEPTED_USERS.add(uid)
            save_users(ACCEPTED_USERS)

            try:
                await bot_app.bot.send_message(uid, get_welcome_msg())
            except:
                pass

        await asyncio.sleep(0.5)


# ===========================================================
# MAIN STARTER (BOTH BOT + USERBOT)
# ===========================================================

async def main():
    bot_app.add_handler(CommandHandler("start", start_cmd))
    bot_app.add_handler(CommandHandler("setmsg", setmsg_cmd))
    bot_app.add_handler(CommandHandler("broadcast", broadcast_cmd))

    bot_app.add_handler(MessageHandler(tg_filters.StatusUpdate.NEW_CHAT_MEMBERS, auto_add_userbot))
    bot_app.add_handler(MessageHandler(tg_filters.StatusUpdate.CHAT_JOIN_REQUEST, new_approve_handler))

    # start bot & userbot
    asyncio.create_task(userbot_main())
    asyncio.create_task(queue_processor())

    print("BOT RUNNING…")
    await bot_app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
