from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pymongo import MongoClient
import datetime, asyncio

# ==== CONFIG ====
API_ID = 22262560
API_HASH = "73eeccd990484d0c87a90756aae9fa21"
BOT_TOKEN = "7582030546:AAFScY5tePtetBp6gj-A6i1amDkVKvOCAYo"

ADMIN_ID = 7901412493
CHANNEL_1 = -1002970592652
CHANNEL_2 = -100  # add if needed for Unlimited File's
UPI_ID = "mallikarjun.padi@ptaxis"
LOG_CHANNEL = -1003056919332

# ==== MONGODB ====
MONGO_URL = "mongodb+srv://Malliofficial:malliofficial@cluster0.db7kygq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["subbot"]
members = db["members"]

# ==== PLAN NAMES & PRICES ====
PLAN_NAMES = {
    "𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺": "𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺",
    "file": "𝗨𝗻𝗹𝗶𝗺𝗶𝘁𝗲𝗱 𝗙𝗶𝗹𝗲'𝘀",
    "both": "Both"
}

PLAN_PRICES = {
    "𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺": 35,
    "file": 20,
    "both": 40
}

# ==== BOT CLIENT ====
app = Client("subbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ==== Keyboards ====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Buy Subscription", callback_data="buy")],
        [InlineKeyboardButton("💰 My Plan", callback_data="plan")]
    ])

def buy_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🤖 {PLAN_NAMES['𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺']} (₹{PLAN_PRICES['𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺']}/30d)", callback_data="plan_𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺")],
        [InlineKeyboardButton(f"📂 {PLAN_NAMES['file']} (₹{PLAN_PRICES['file']}/30d)", callback_data="plan_file")],
        [InlineKeyboardButton(f"🔥 {PLAN_NAMES['both']} (₹{PLAN_PRICES['both']}/30d)", callback_data="plan_both")],
    ])

# ==== START ====
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "🎉 Welcome to Subscription Bot!\n\n"
        f"👤 User ID: `{message.from_user.id}`\n\n"
        "Available Commands:\n"
        "🛒 /buy - Purchase subscription\n"
        "💰 /plan - Check your plan\n\n"
        "Admin Support: @HC_Support_bot",
        reply_markup=main_menu()
    )

# ==== ADMIN STATS ====
@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats(client, message):
    total = members.distinct("user_id")
    malli = members.count_documents({"plan": "𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺"})
    file = members.count_documents({"plan": "file"})
    both = members.count_documents({"plan": "both"})

    await message.reply_text(
        f"📊 Subscription Stats:\n\n"
        f"👥 Total Unique Users: {len(total)}\n"
        f"🤖 {PLAN_NAMES['𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺']}: {malli}\n"
        f"📂 {PLAN_NAMES['file']}: {file}\n"
        f"🔥 {PLAN_NAMES['both']}: {both}"
    )

# ==== /buy ====
@app.on_message(filters.command("buy"))
async def buy_cmd(client, message):
    await message.reply_text("🛒 Choose your subscription plan:", reply_markup=buy_keyboard())

@app.on_callback_query(filters.regex("^buy$"))
async def buy_callback(client, cq: CallbackQuery):
    await cq.answer()
    await cq.message.reply_text("🛒 Choose your subscription plan:", reply_markup=buy_keyboard())

# ==== /plan ====
@app.on_message(filters.command("plan"))
async def plan_cmd(client, message):
    user_id = message.from_user.id
    docs = list(members.find({"user_id": user_id, "join_date": {"$ne": "PENDING"}}))
    if not docs:
        await message.reply_text("❌ You don’t have an active subscription. Use /buy to get one.")
        return

    text = "📋 Your Active Plans:\n\n"
    for doc in docs:
        join_date = datetime.date.fromisoformat(doc["join_date"])
        days_left = 30 - (datetime.date.today() - join_date).days
        plan_name = PLAN_NAMES.get(doc["plan"], doc["plan"])
        text += f"💬 Plan: {plan_name}\n"
        text += f"📅 Joined: {doc['join_date']}\n"
        text += f"⏳ Days left: {days_left if days_left > 0 else 0}\n\n"
    await message.reply_text(text)

@app.on_callback_query(filters.regex("^plan$"))
async def plan_callback(client, cq: CallbackQuery):
    await cq.answer()
    user_id = cq.from_user.id
    docs = list(members.find({"user_id": user_id, "join_date": {"$ne": "PENDING"}}))
    if not docs:
        await cq.message.reply_text("❌ You don’t have an active subscription. Use /buy to get one.")
        return

    text = "📋 Your Active Plans:\n\n"
    for doc in docs:
        join_date = datetime.date.fromisoformat(doc["join_date"])
        days_left = 30 - (datetime.date.today() - join_date).days
        plan_name = PLAN_NAMES.get(doc["plan"], doc["plan"])
        text += f"💬 Plan: {plan_name}\n"
        text += f"📅 Joined: {doc['join_date']}\n"
        text += f"⏳ Days left: {days_left if days_left > 0 else 0}\n\n"
    await cq.message.reply_text(text)

# ==== PLAN SELECTION ====
@app.on_callback_query(filters.regex("^plan_"))
async def select_plan(client, cq: CallbackQuery):
    plan = cq.data.split("_", 1)[1]
    user_id = cq.from_user.id

    existing = members.find_one({"user_id": user_id, "plan": plan, "join_date": {"$ne": "PENDING"}})
    if existing:
        await cq.answer()
        await cq.message.reply_text(f"⚠️ You already purchased this {PLAN_NAMES[plan]} plan.\nPlease wait until it expires.")
        return

    await cq.answer()
    await cq.message.edit_text(
        f"💳 Please pay ₹{PLAN_PRICES[plan]} to:\n\n"
        f"👉 UPI ID: `{UPI_ID}`\n\n"
        "📸 After payment, send a screenshot here.\n\n"
        "(Admin will verify and approve your subscription.)"
    )
    members.update_one(
        {"user_id": user_id, "plan": plan},
        {"$set": {"join_date": "PENDING"}},
        upsert=True
    )

# ==== HANDLE SCREENSHOT ====
@app.on_message(filters.photo & ~filters.command(["start", "buy", "plan"]))
async def handle_screenshot(client, message):
    user_id = message.from_user.id
    pending_doc = members.find_one({"user_id": user_id, "join_date": "PENDING"})
    if not pending_doc:
        await message.reply_text("❌ Please select a plan first using /buy before sending screenshot.")
        return

    plan = pending_doc["plan"]
    fwd = await message.forward(LOG_CHANNEL)
    await client.send_message(
        LOG_CHANNEL,
        f"🆕 Payment request from {message.from_user.mention} (ID: {user_id}).\nPlan: {PLAN_NAMES[plan]}",
        reply_to_message_id=fwd.id,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve Malli4U Premium", callback_data=f"approve_{user_id}_𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺")],
            [InlineKeyboardButton("✅ Approve Unlimited Files", callback_data=f"approve_{user_id}_file")],
            [InlineKeyboardButton("✅ Approve Both", callback_data=f"approve_{user_id}_both")],
        ])
    )
    await message.reply_text("✅ Screenshot sent to admin for verification. Please wait...")

# ==== ADMIN APPROVAL ====
@app.on_callback_query(filters.regex("^approve_"))
async def approve_btn(client, cq: CallbackQuery):
    _, user_id, plan = cq.data.split("_", 2)
    user_id = int(user_id)
    join_date = datetime.date.today().isoformat()

    await cq.answer()
    try:
        if plan == "𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺":
            invite1 = await client.create_chat_invite_link(CHANNEL_1, member_limit=1)
            await client.send_message(user_id, f"🎉 Approved!\nHere is your invite link:\n{invite1.invite_link}")

        elif plan == "file":
            invite2 = await client.create_chat_invite_link(CHANNEL_2, member_limit=1)
            await client.send_message(user_id, f"🎉 Approved!\nHere is your invite link:\n{invite2.invite_link}")

        elif plan == "both":
            invite1 = await client.create_chat_invite_link(CHANNEL_1, member_limit=1)
            invite2 = await client.create_chat_invite_link(CHANNEL_2, member_limit=1)
            await client.send_message(
                user_id,
                f"🎉 Approved!\nHere are your invite links:\n\n"
                f"🔹 Malli4U Premium: {invite1.invite_link}\n"
                f"🔹 Unlimited Files: {invite2.invite_link}"
            )

        members.update_one(
            {"user_id": user_id, "plan": plan},
            {"$set": {"join_date": join_date}},
            upsert=True
        )
        await cq.message.edit_text(f"✅ Approved {user_id} for **{PLAN_NAMES[plan]}** plan")

    except Exception as e:
        await cq.message.edit_text(f"⚠️ Error: {e}")

# ==== AUTO REMOVE ====
async def check_and_remove():
    while True:
        today = datetime.date.today()
        for doc in members.find({"join_date": {"$ne": "PENDING"}}):
            user_id = doc["user_id"]
            plan = doc["plan"]
            join_date = datetime.date.fromisoformat(doc["join_date"])
            days_passed = (today - join_date).days

            if days_passed >= 30:
                try:
                    if plan in ["𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺", "both"]:
                        await app.kick_chat_member(CHANNEL_1, user_id)
                    if plan in ["file", "both"]:
                        await app.kick_chat_member(CHANNEL_2, user_id)

                    await app.send_message(
                        user_id,
                        f"❌ Your 30-day subscription for {PLAN_NAMES[plan]} expired.\n\n"
                        "Please pay again using /buy to rejoin."
                    )
                    members.delete_one({"user_id": user_id, "plan": plan})
                    print(f"Removed {user_id} from {PLAN_NAMES[plan]}")
                except Exception as e:
                    print("Error removing:", e)

        await asyncio.sleep(86400)

# ==== RUN BOT ====
async def main():
    asyncio.create_task(check_and_remove())
    await app.start()
    print("Bot running...")
    await idle()

if __name__ == "__main__":
    app.run(main())
