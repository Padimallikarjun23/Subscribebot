import os
import pymongo
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ============ CONFIG ============
API_ID = 22262560
API_HASH = "73eeccd990484d0c87a90756aae9fa21"
BOT_TOKEN = "7582030546:AAFScY5tePtetBp6gj-A6i1amDkVKvOCAYo"

ADMIN_ID = 7901412493
CHANNEL_1 = -1002970592652
CHANNEL_2 = -100  # replace with your second channel ID
LOG_CHANNEL = -1003056919332

MONGO_URL = "mongodb+srv://Malliofficial:malliofficial@cluster0.db7kygq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
UPI_ID = "mallikarjun.padi@ptaxis"

client = pymongo.MongoClient(MONGO_URL)
db = client["SubscriptionBot"]
members = db["members"]

# ============ PLAN NAMES ============
PLAN_NAMES = {
    "m4u": "𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺",
    "files": "𝗨𝗻𝗹𝗶𝗺𝗶𝘁𝗲𝗱 𝗙𝗶𝗹𝗲'𝘀",
    "both": "𝗕𝗼𝘁𝗵"
}

# ============ BOT INIT ============
app = Client("SubscriptionBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ============ START ============
@app.on_message(filters.command("start"))
async def start(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Buy Plans", callback_data="buy")],
        [InlineKeyboardButton("ℹ️ My Plan", callback_data="status")]
    ])
    await message.reply_text("👋 Welcome! Choose an option:", reply_markup=keyboard)

# ============ BUY PLANS ============
@app.on_callback_query(filters.regex("^buy$"))
async def buy_plans(client, cq: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ 𝗠𝗮𝗹𝗹𝗶𝟒𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺 (₹35/30d)", callback_data="plan_m4u")],
        [InlineKeyboardButton("✨ 𝗨𝗻𝗹𝗶𝗺𝗶𝘁𝗲𝗱 𝗙𝗶𝗹𝗲'𝘀 (₹20/30d)", callback_data="plan_files")],
        [InlineKeyboardButton("✨ 𝗕𝗼𝘁𝗵 (₹50/30d)", callback_data="plan_both")]
    ])
    await cq.message.edit_text("💳 Choose your subscription plan:", reply_markup=keyboard)
    await cq.answer()

# ============ PLAN SELECTION ============
@app.on_callback_query(filters.regex("^plan_"))
async def select_plan(client, cq: CallbackQuery):
    plan = cq.data.split("_", 1)[1]
    user_id = cq.from_user.id
    prices = {"m4u": 35, "files": 20, "both": 50}

    existing = members.find_one({"user_id": user_id, "plan": plan, "join_date": {"$ne": "PENDING"}})
    if existing:
        await cq.answer()
        await cq.message.reply_text(f"⚠️ You already purchased this {PLAN_NAMES[plan]} plan.\nPlease wait until it expires.")
        return

    await cq.answer()
    await cq.message.edit_text(
        f"💳 Please pay ₹{prices[plan]} to:\n\n"
        f"👉 UPI ID: `{UPI_ID}`\n\n"
        "📸 After payment, send a screenshot here to Admin: @M4U_Admin_Bot\n\n"
        "(Admin will verify and approve your subscription.)"
    )
    members.update_one(
        {"user_id": user_id, "plan": plan},
        {"$set": {"join_date": "PENDING"}},
        upsert=True
    )

# ============ HANDLE SCREENSHOTS ============
@app.on_message(filters.photo & ~filters.private)
async def handle_screenshot(client, message):
    user_id = message.from_user.id
    pending = members.find_one({"user_id": user_id, "join_date": "PENDING"})
    if not pending:
        return

    plan = pending["plan"]
    await app.send_message(
        LOG_CHANNEL,
        f"🆕 Payment request from {message.from_user.mention} (ID: {user_id}).\nPlan: {PLAN_NAMES.get(plan, plan)}",
    )
    await message.reply_text("✅ Payment screenshot received. Admin will verify soon.")

# ============ STATUS ============
@app.on_callback_query(filters.regex("^status$"))
async def my_plan(client, cq: CallbackQuery):
    user_id = cq.from_user.id
    data = members.find_one({"user_id": user_id, "join_date": {"$ne": "PENDING"}})
    if not data:
        await cq.message.reply_text("❌ You have no active subscription.")
        return

    join_date = datetime.strptime(data["join_date"], "%Y-%m-%d")
    expiry = join_date + timedelta(days=30)
    await cq.message.reply_text(f"📅 Your Plan: {PLAN_NAMES[data['plan']]}\n"
                                f"🗓 Joined: {join_date.date()}\n"
                                f"⌛ Expires: {expiry.date()}")
    await cq.answer()

# ============ RUN ============
app.run()
mber(CHANNEL_1, user_id)
                    if plan in ["files", "both"]:
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
