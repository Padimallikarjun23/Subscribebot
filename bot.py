# ===============================
#  Subscription Bot - Malli4U 🔥
#  Pyrogram v2 + MongoDB
#  Author: Mallikarjun
# ===============================

from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pymongo import MongoClient
import datetime, asyncio


# ==== CONFIG ====
API_ID      = 22262560
API_HASH    = "73eeccd990484d0c87a90756aae9fa21"
BOT_TOKEN   = "YOUR_BOT_TOKEN"

ADMIN_ID    = 7901412493
LOG_CHANNEL = -1003056919332  # Payment logs channel

# ⚠️ Replace with your actual channel IDs (use /getid)
CHANNEL_1   = -1002123456789   # Premium Channel
CHANNEL_2   = -1002987654321   # Files Channel

UPI_ID      = "mallikarjun.padi@ptaxis"

# Subscription limits
DAYS_LIMIT     = 1        # test: 1 day, real: 30
CHECK_INTERVAL = 60       # test: 60 sec, real: 86400 sec (1 day)


# ==== DATABASE ====
MONGO_URL = "mongodb+srv://Mallikarjun:malli123@cluster0.54pprxf.mongodb.net/?retryWrites=true&w=majority"
mongo_client = MongoClient(MONGO_URL)
db      = mongo_client["subbot"]
members = db["members"]


# ==== PLAN NAMES ====
PLAN_NAMES = {
    "m4u" : "𝗠𝟰𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺",
    "file": "𝗨𝗻𝗹𝗶𝗺𝗶𝘁𝗲𝗱 𝗙𝗶𝗹𝗲'𝘀",
    "both": "𝗕𝗼𝘁𝗵"
}


# ==== BOT CLIENT ====
app = Client("subbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# ===============================
#  Keyboards
# ===============================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Buy Subscription", callback_data="plan_menu")],
        [InlineKeyboardButton("💰 My Plan", callback_data="myplan")]
    ])

def buy_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✨ {PLAN_NAMES['m4u']} (₹35/{DAYS_LIMIT}d)",  callback_data="plan_m4u")],
        [InlineKeyboardButton(f"📂 {PLAN_NAMES['file']} (₹20/{DAYS_LIMIT}d)", callback_data="plan_file")],
        [InlineKeyboardButton(f"🔥 {PLAN_NAMES['both']} (₹50/{DAYS_LIMIT}d)", callback_data="plan_both")]
    ])


# ===============================
#  Commands
# ===============================
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "🎉 Welcome to Subscription Bot!\n\n"
        f"👤 User ID: `{message.from_user.id}`\n\n"
        "Commands:\n"
        "🛒 /buy - Purchase subscription\n"
        "💰 /plan - Check your plan\n\n"
        "Admin Support: @M4U_Admin_Bot",
        reply_markup=main_menu()
    )

@app.on_message(filters.command("buy"))
async def buy_cmd(client, message):
    await message.reply_text("🛒 Choose your subscription plan:", reply_markup=buy_keyboard())

@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats(client, message):
    total = members.distinct("user_id")
    m4u   = members.count_documents({"plan": "m4u"})
    file  = members.count_documents({"plan": "file"})
    both  = members.count_documents({"plan": "both"})
    await message.reply_text(
        f"📊 Subscription Stats:\n\n"
        f"👥 Total Users: {len(total)}\n"
        f"✨ {PLAN_NAMES['m4u']}: {m4u}\n"
        f"📂 {PLAN_NAMES['file']}: {file}\n"
        f"🔥 {PLAN_NAMES['both']}: {both}"
    )

# Helper to get Channel ID
@app.on_message(filters.command("getid") & filters.user(ADMIN_ID))
async def get_id(client, message):
    await message.reply_text(f"Chat ID: `{message.chat.id}`")


# ===============================
#  Button Handler
# ===============================
@app.on_callback_query()
async def all_callbacks(client, cq: CallbackQuery):
    await cq.answer()

    if cq.data == "plan_menu":
        await cq.message.edit_text("🛒 Choose your subscription plan:", reply_markup=buy_keyboard())

    elif cq.data == "myplan":
        doc = members.find_one({"user_id": cq.from_user.id, "join_date": {"$ne": "PENDING"}})
        if doc:
            await cq.message.reply_text(
                f"💰 Current Plan: {PLAN_NAMES[doc['plan']]}\n"
                f"📅 Joined On: {doc['join_date']}"
            )
        else:
            await cq.message.reply_text("❌ No active plan found. Use /buy to subscribe.")

    elif cq.data.startswith("plan_"):
        await handle_plan(client, cq)

    elif cq.data.startswith("approve_"):
        await handle_approve(client, cq)


# ===============================
#  Plan Selection
# ===============================
async def handle_plan(client, cq: CallbackQuery):
    plan     = cq.data.split("_", 1)[1]
    user_id  = cq.from_user.id
    prices   = {"m4u": 35, "file": 20, "both": 50}

    existing = members.find_one({"user_id": user_id, "plan": plan, "join_date": {"$ne": "PENDING"}})
    if existing:
        await cq.message.reply_text(f"⚠️ You already purchased {PLAN_NAMES[plan]}. Wait until expiry.")
        return

    await cq.message.edit_text(
        f"💳 Pay ₹{prices[plan]} to:\n\n"
        f"👉 UPI ID: `{UPI_ID}`\n\n"
        "📸 After payment, send screenshot to Admin: @M4U_Admin_Bot"
    )
    members.update_one(
        {"user_id": user_id, "plan": plan},
        {"$set": {"join_date": "PENDING"}},
        upsert=True
    )


# ===============================
#  Screenshot Handler
# ===============================
@app.on_message(filters.photo & ~filters.command(["start", "buy", "plan"]))
async def handle_screenshot(client, message):
    user_id = message.from_user.id
    pending = members.find_one({"user_id": user_id, "join_date": "PENDING"})
    if not pending:
        await message.reply_text("❌ Use /buy first before sending screenshot.")
        return

    plan = pending["plan"]
    fwd  = await message.forward(LOG_CHANNEL)

    await client.send_message(
        LOG_CHANNEL,
        f"🆕 Payment request from {message.from_user.mention} (ID: {user_id}).\nPlan: {PLAN_NAMES[plan]}",
        reply_to_message_id=fwd.id,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ Approve {PLAN_NAMES['m4u']}",  callback_data=f"approve_{user_id}_m4u")],
            [InlineKeyboardButton(f"✅ Approve {PLAN_NAMES['file']}", callback_data=f"approve_{user_id}_file")],
            [InlineKeyboardButton(f"✅ Approve {PLAN_NAMES['both']}", callback_data=f"approve_{user_id}_both")]
        ])
    )
    await message.reply_text("✅ Screenshot sent. Please wait for Admin approval.")


# ===============================
#  Approve Handler
# ===============================
async def handle_approve(client, cq: CallbackQuery):
    _, user_id, plan = cq.data.split("_")
    user_id  = int(user_id)
    join_date = datetime.date.today().isoformat()

    try:
        if plan in ["m4u", "both"]:
            link1 = await client.create_chat_invite_link(CHANNEL_1, member_limit=1)
            await client.send_message(user_id, f"🎉 Approved!\nHere’s your link:\n{link1.invite_link}")

        if plan in ["file", "both"]:
            link2 = await client.create_chat_invite_link(CHANNEL_2, member_limit=1)
            await client.send_message(user_id, f"🎉 Approved!\nHere’s your link:\n{link2.invite_link}")

        members.update_one(
            {"user_id": user_id, "plan": plan},
            {"$set": {"join_date": join_date}},
            upsert=True
        )

        await cq.message.edit_text(f"✅ Approved {user_id} for {PLAN_NAMES[plan]}")

    except Exception as e:
        await cq.message.edit_text(f"⚠️ Error: {e}")


# ===============================
#  Auto Expiry Checker
# ===============================
async def check_and_remove():
    while True:
        today = datetime.date.today()
        for doc in members.find({"join_date": {"$ne": "PENDING"}}):
            user_id = doc["user_id"]
            plan    = doc["plan"]
            joined  = datetime.date.fromisoformat(doc["join_date"])
            days    = (today - joined).days

            if days >= DAYS_LIMIT:
                try:
                    if plan in ["m4u", "both"]:
                        await app.ban_chat_member(CHANNEL_1, user_id)
                    if plan in ["file", "both"]:
                        await app.ban_chat_member(CHANNEL_2, user_id)

                    await app.send_message(user_id, f"❌ Your {PLAN_NAMES[plan]} expired. Renew with /buy.")
                    members.delete_one({"user_id": user_id, "plan": plan})
                    print(f"Removed {user_id} from {PLAN_NAMES[plan]}")

                except Exception as e:
                    print("Error removing:", e)

        await asyncio.sleep(CHECK_INTERVAL)


# ===============================
#  Main Runner
# ===============================
async def main():
    asyncio.create_task(check_and_remove())
    await app.start()
    print("🔥 Bot running...")
    await idle()

if __name__ == "__main__":
    app.run(main())
