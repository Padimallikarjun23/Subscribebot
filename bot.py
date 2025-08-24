from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pymongo import MongoClient
import datetime, asyncio

# ==== CONFIG ====
API_ID = 012345
API_HASH = ""
BOT_TOKEN = ""

ADMIN_ID = 123456789
CHANNEL_1 = -100
CHANNEL_2 = -100
UPI_ID = "@upi"
LOG_CHANNEL = -100   # <-- replace with your log channel ID

# ==== MONGODB ====
MONGO_URL = ""
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["subbot"]
members = db["members"]

# ==== PLAN NAMES ====
PLAN_NAMES = {
    "hc": "HC Originals Bot",
    "file": "File To Link Bot",
    "both": "Both"
}

# ==== BOT CLIENT ====
app = Client("subbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# ==== Helper keyboards ====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Buy Subscription", callback_data="buy")],
        [InlineKeyboardButton("💰 My Plan", callback_data="plan")]
    ])

def buy_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 HC Originals Bot (₹30/30d)", callback_data="plan_hc")],
        [InlineKeyboardButton("📂 File to Link Bot (₹20/30d)", callback_data="plan_file")],
        [InlineKeyboardButton("🔥 Both (₹40/30d)", callback_data="plan_both")],
    ])


# ==== START COMMAND ====
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
    total = members.distinct("user_id")  # unique users
    hc = members.count_documents({"plan": "hc"})
    file = members.count_documents({"plan": "file"})
    both = members.count_documents({"plan": "both"})

    await message.reply_text(
        f"📊 Subscription Stats:\n\n"
        f"👥 Total Unique Users: {len(total)}\n"
        f"🤖 {PLAN_NAMES['hc']}: {hc}\n"
        f"📂 {PLAN_NAMES['file']}: {file}\n"
        f"🔥 {PLAN_NAMES['both']}: {both}"
    )


# ==== ADMIN USERS LIST ====
@app.on_message(filters.command("users") & filters.user(ADMIN_ID))
async def list_users(client, message):
    docs = members.find({})
    if not docs:
        await message.reply_text("❌ No active subscribers found.")
        return

    text = "📋 Active Subscribers:\n\n"
    for doc in docs:
        user_id = doc["user_id"]
        plan = PLAN_NAMES.get(doc["plan"], doc["plan"])
        join_date = doc["join_date"]

        text += f"👤 [{user_id}](tg://user?id={user_id})\n"
        text += f"   • Plan: {plan}\n"
        text += f"   • Joined: {join_date}\n\n"

    if len(text) > 4000:
        with open("subscribers.txt", "w") as f:
            f.write(text)
        await message.reply_document("subscribers.txt")
    else:
        await message.reply_text(text, disable_web_page_preview=True)


# ==== /buy command ====
@app.on_message(filters.command("buy"))
async def buy_cmd(client, message):
    await message.reply_text("🛒 Choose your subscription plan:", reply_markup=buy_keyboard())


# ==== Buy button (REPLY not edit) ====
@app.on_callback_query(filters.regex("^buy$"))
async def buy_callback(client, cq: CallbackQuery):
    await cq.answer()
    await cq.message.reply_text("🛒 Choose your subscription plan:", reply_markup=buy_keyboard())


# ==== /plan command ====
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


# ==== Plan button (REPLY not edit) ====
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


# ==== PLAN SELECTION (HC/File/Both) → EDIT ====
@app.on_callback_query(filters.regex("^plan_"))
async def select_plan(client, cq: CallbackQuery):
    plan = cq.data.split("_")[1]
    user_id = cq.from_user.id
    prices = {"hc": 30, "file": 20, "both": 40}

    # check if already active
    existing = members.find_one({"user_id": user_id, "plan": plan, "join_date": {"$ne": "PENDING"}})
    if existing:
        await cq.answer()
        await cq.message.reply_text(f"⚠️ You already purchased this {PLAN_NAMES[plan]} plan.\nPlease wait until it expires.")
        return

    await cq.answer()
    await cq.message.edit_text(
        f"💳 Please pay ₹{prices[plan]} to:\n\n"
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

    # check if user selected a plan
    pending_doc = members.find_one({"user_id": user_id, "join_date": "PENDING"})
    if not pending_doc:
        await message.reply_text("❌ Please select a plan first using /buy before sending screenshot.")
        return

    plan = pending_doc["plan"]

    # forward screenshot to log channel
    fwd = await message.forward(LOG_CHANNEL)
    await client.send_message(
        LOG_CHANNEL,
        f"🆕 Payment request from {message.from_user.mention} (ID: {user_id}).\nPlan: {PLAN_NAMES[plan]}",
        reply_to_message_id=fwd.id,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ HC Originals Bot", callback_data=f"approve_{user_id}_hc")],
            [InlineKeyboardButton("✅ File To Link Bot", callback_data=f"approve_{user_id}_file")],
            [InlineKeyboardButton("✅ Both", callback_data=f"approve_{user_id}_both")],
        ])
    )
    await message.reply_text("✅ Screenshot sent to admin for verification. Please wait...")


# ==== ADMIN APPROVAL (EDIT MESSAGE) ====
@app.on_callback_query(filters.regex("^approve_"))
async def approve_btn(client, cq: CallbackQuery):
    _, user_id, plan = cq.data.split("_")
    user_id = int(user_id)
    join_date = datetime.date.today().isoformat()

    await cq.answer()
    try:
        if plan == "hc":
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
                f"🔹 Channel 1: {invite1.invite_link}\n"
                f"🔹 Channel 2: {invite2.invite_link}"
            )

        members.update_one(
            {"user_id": user_id, "plan": plan},
            {"$set": {"join_date": join_date}},
            upsert=True
        )

        await cq.message.edit_text(f"✅ Approved {user_id} for **{PLAN_NAMES[plan]}** plan")

    except Exception as e:
        await cq.message.edit_text(f"⚠️ Error: {e}")


# ==== AUTO REMOVE AFTER 30 DAYS ====
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
                    if plan in ["hc", "both"]:
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
