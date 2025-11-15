import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = 21705136
API_HASH = "78730e89d196e160b0f1992018c6cb19"
BOT_TOKEN = "8395895550:AAE8ucM2C_YZ76vAxcA7zInt1Nv41Fcm6NQ"

STRING_SESSION = "BQFLMbAAWQeJX940vXUXyOdLLi7Cn6A5myy1ovFQcrs8ozwAhymMKIG4UEfiETDPqn5aLAax5l1Zrfey1KjtSIh9gt_cSqKZd4b1NVp7r4ctyqBWd8gSd678_LNM1ZUQSVN6gHPDPG7WduQ9C37Cj-CsuaW769QsW6o4-IUkGahEe_TNH273p8xPUDvdcFvQA-srM1PKQJLZcFYmBsavM8xWjuNS53t0-Vmh2-UOmcdk9mE4LMJNW2fKOWRfaq00Zl_mOJeAU65AloMwOvJr_q4dR8QrZGGsq9dDTSWNhXJrRhGnCA8Hh5o0bXGhqPtR8LNB4bH2Kdb0rrabTrGPOhsiD71wJAAAAAHTfWlHAA"

OWNER_ID = 7843178823
CUSTOM_MSG = "Welcome! Your request has been accepted."

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
ubot = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

accepted_users = set()


# ------------------ SEND DM ------------------
async def send_dm(user_id):
    try:
        if user_id not in accepted_users:
            await bot.send_message(user_id, CUSTOM_MSG)
            accepted_users.add(user_id)
    except Exception as e:
        print("DM Error:", e)


# ------------------ ACCEPT ALL OLD REQUESTS ------------------
async def accept_all_requests(chat_id):
    try:
        print(f"Checking old requests for {chat_id}...")

        # 🔹 Bot approve
        async for req in bot.get_chat_join_requests(chat_id):
            await bot.approve_chat_join_request(chat_id, req.user.id)
            await send_dm(req.user.id)

        # 🔹 Userbot approve
        async for req in ubot.get_chat_join_requests(chat_id):
            await ubot.approve_chat_join_request(chat_id, req.user.id)
            await send_dm(req.user.id)

        print("Old requests processed.")

    except Exception as e:
        print("OLD REQUEST ERROR:", e)


# ------------------ AUTO ACCEPT LIVE REQUESTS ------------------
@bot.on_chat_join_request()
async def join_request_handler(client, req):
    try:
        await client.approve_chat_join_request(req.chat.id, req.from_user.id)
    except:
        pass

    try:
        await ubot.approve_chat_join_request(req.chat.id, req.from_user.id)
    except:
        pass

    await send_dm(req.from_user.id)


# ------------------ BOT ADDED TO GROUP/CHANNEL ------------------
@bot.on_message(filters.new_chat_members)
async def added_to_chat(_, m: Message):
    for u in m.new_chat_members:
        if u.is_self:  # bot added
            chat_id = m.chat.id
            print(f"Bot added in {chat_id}")

            # USERBOT JOIN
            try:
                await ubot.join_chat(chat_id)
                print("Userbot joined.")
            except Exception as e:
                print("Userbot join error:", e)

            # USERBOT PROMOTE
            try:
                me = await ubot.get_me()
                await ubot.promote_chat_member(
                    chat_id, me.id,
                    can_manage_chat=True,
                    can_invite_users=True,
                    can_delete_messages=True,
                    can_manage_topics=True
                )
                print("Userbot promoted.")
            except Exception as e:
                print("Promote error:", e)

            await m.reply("🟢 Bot Ready!\nAuto Accept + DM Active.")

            await accept_all_requests(chat_id)


# ------------------ START COMMAND ------------------
@bot.on_message(filters.command("start"))
async def start_cmd(_, m):
    await m.reply("🤖 Auto Accept Bot Online!")


# ------------------ BROADCAST ------------------
@bot.on_message(filters.command("broadcast"))
async def broadcast(_, m):
    if m.from_user.id != OWNER_ID:
        return await m.reply("❌ You are not the owner.")

    if not m.reply_to_message:
        return await m.reply("Reply to a message to broadcast.")

    count = 0
    for uid in accepted_users:
        try:
            await bot.copy_message(uid, m.chat.id, m.reply_to_message.id)
            count += 1
        except:
            pass

    await m.reply(f"📢 Broadcast sent to {count} users.")


# ------------------ MAIN LOOP ------------------
async def main():
    print("Starting Userbot...")
    await ubot.start()

    print("Starting Bot...")
    await bot.start()

    print("BOT + USERBOT RUNNING...")
    await asyncio.get_event_loop().create_future()


asyncio.run(main())
