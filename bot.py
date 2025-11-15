import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid

API_ID = 21705136
API_HASH = "78730e89d196e160b0f1992018c6cb19"
BOT_TOKEN = "8395895550:AAE8ucM2C_YZ76vAxcA7zInt1Nv41Fcm6NQ"

# USERBOT STRING SESSION
STRING_SESSION = "BQFLMbAAWQeJX940vXUXyOdLLi7Cn6A5myy1ovFQcrs8ozwAhymMKIG4UEfiETDPqn5aLAax5l1Zrfey1KjtSIh9gt_cSqKZd4b1NVp7r4ctyqBWd8gSd678_LNM1ZUQSVN6gHPDPG7WduQ9C37Cj-CsuaW769QsW6o4-IUkGahEe_TNH273p8xPUDvdcFvQA-srM1PKQJLZcFYmBsavM8xWjuNS53t0-Vmh2-UOmcdk9mE4LMJNW2fKOWRfaq00Zl_mOJeAU65AloMwOvJr_q4dR8QrZGGsq9dDTSWNhXJrRhGnCA8Hh5o0bXGhqPtR8LNB4bH2Kdb0rrabTrGPOhsiD71wJAAAAAHTfWlHAA"

# Custom DM Message
CUSTOM_MSG = "Welcome! Your request has been accepted."

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
ubot = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

accepted_users = set()

async def accept_all_requests(chat_id, app):
    try:
        async for req in app.get_chat_join_requests(chat_id):
            await app.approve_chat_join_request(chat_id, req.user.id)
            await send_dm(req.user.id)
    except Exception as e:
        print("Error:", e)

async def send_dm(user_id):
    try:
        if user_id not in accepted_users:
            await bot.send_message(user_id, CUSTOM_MSG)
            accepted_users.add(user_id)
    except:
        pass

@bot.on_message(filters.command("start"))
async def start(_, m: Message):
    await m.reply("🤖 Bot Active: Auto Accept + DM Sender + Userbot Linked")

@bot.on_message(filters.command("broadcast"))
async def broadcast(_, m: Message):
    if m.from_user.id != 7843178823:
        return await m.reply("❌ Only owner can broadcast")

    if not m.reply_to_message:
        return await m.reply("Reply to a message to broadcast.")

    sent = 0
    for uid in accepted_users:
        try:
            await bot.copy_message(uid, m.chat.id, m.reply_to_message.message_id)
            sent += 1
        except:
            pass

    await m.reply(f"Broadcast sent: {sent} users")

@bot.on_chat_join_request()
async def auto_accept(client, req):
    await client.approve_chat_join_request(req.chat.id, req.from_user.id)
    await send_dm(req.from_user.id)

@bot.on_message(filters.new_chat_members)
async def bot_added(_, m: Message):
    for user in m.new_chat_members:
        if user.is_self:
            try:
                await ubot.join_chat(m.chat.id)
                await ubot.promote_chat_member(
                    m.chat.id,
                    (await ubot.get_me()).id,
                    can_invite_users=True,
                    can_manage_chat=True,
                    can_manage_topics=True,
                    can_delete_messages=True
                )
                await m.reply("🟢 Userbot joined & promoted.")
                await accept_all_requests(m.chat.id, bot)
                await accept_all_requests(m.chat.id, ubot)
            except Exception as e:
                print("Join error:", e)

async def main():
    await ubot.start()
    await bot.start()
    print("BOT + USERBOT STARTED")
    await asyncio.get_event_loop().create_future()

asyncio.run(main())
