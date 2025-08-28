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
CHANNEL_2 = -100  # if needed later
UPI_ID = "mallikarjun.padi@ptaxis"
LOG_CHANNEL = -1003056919332

# ==== MONGODB ====
MONGO_URL = "mongodb+srv://Mallikarjun:malli123@cluster0.54pprxf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["subbot"]
members = db["members"]

# ==== PLAN NAMES ====
PLAN_NAMES = {
    "m4u": "𝗠𝟰𝗨_𝗣𝗿𝗲𝗺𝗶𝘂𝗺",
    "file": "𝗨𝗻𝗹𝗶𝗺𝗶𝘁𝗲𝗱 𝗙𝗶𝗹𝗲'𝘀",
    "both": "𝗕𝗼𝘁𝗵"
}

# ==== BOT CLIENT ====
app = Client("subbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# ==== Helper keyboards ====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Buy Subscription", callback_data="buy_menu")],
        [InlineKeyboardButton("💰 My Plan", callback_data="my_plan")]
    ])

def buy_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✨ {PLAN_NAMES['m4u']} (₹35/30d)", callback_data="plan_m4u")],
        [InlineKeyboardButton(f"📂 {PLAN_NAMES['file']} (₹20/30d)", callback_data="plan_file")],
        [InlineKeyboardButton(f"🔥 {PLAN_NAMES['both']} (₹50/30d)", callback_data="plan_both")],
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
        "Admin Support: @M4U_Admin_Bot",
        reply_markup=main_menu()
    )


# ==== ADMIN STATS ====
@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats(client, message):
    total = members.distinct("user_id")
    m4u = members.count_documents({"plan": "m4u"})
    file = members.count_documents({"plan": "file"})
    both = members.count_documents({"plan": "both"})

    await message.reply_text(
        f"📊 Subscription Stats:\n\n"
        f"👥 Total Unique Users: {len(total)}\n"
        f"✨ {PLAN_NAMES['m4u']}: {m4u}\n"
        f"📂 {PLAN_NAMES['file']}: {file}\n"
        f"🔥 {PLAN_NAMES['both']}: {both}"
    )


# ==== /buy command ====
@app.on_message(filters.command("buy"))
async def buy_cmd(client, message):
    await message.reply_text("🛒 Choose your subscription plan:", reply_markup=buy_keyboard())


# ==== /plan command ====
@app.on_message(filters.command("plan"))
async def plan_cmd(client, message):
    user_id = message.from_user.id
    subs = list(members.find({"user_id": user_id, "join_date": {"$ne": "PENDING"}}))
    if not subs:
        await message.reply_text("❌ You have no active subscription.\nUse /buy to purchase.")
        return

    plans = "\n".join([f"✅ {PLAN_NAMES[s['plan']]} (Joined: {s['join_date']})" for s in subs])
    await message.reply_text(f"💰 Your Active Plans:\n\n{plans}")


# ==== Handle all buttons ====
@app.on_callback_query()
async def all_callbacks(client, cq: CallbackQuery):
    await cq.answer()  # must include, prevents button freeze

    # Buy menu
    if cq.data == "buy_menu":
        await cq.message.edit_text("🛒 Choose your subscription plan:", reply_markup=buy_keyboard())
        return

    # My plan
    if cq.data == "my_plan":
        user_id = cq.from_user.id
        subs = list(members.find({"user_id": user_id, "join_date": {"$ne": "PENDING"}}))
        if not subs:
            await cq.message.reply_text("❌ You have no active subscription.\nUse /buy to purchase.")
            return
        plans = "\n".join([f"✅ {PLAN_NAMES[s['plan']]} (Joined: {s['join_date']})" for s in subs])
        await cq.message.reply_text(f"💰 Your Active Plans:\n\n{plans}")
        return

    # Plan selection
    if cq.data.startswith("plan_"):
        plan = cq.data.split("_", 1)[1]
        user_id = cq.from_user.id
        prices = {"m4u": 35, "file": 20, "both": 50}

        existing = members.find_one({"user_id": user_id, "plan": plan, "join_date": {"$ne": "PENDING"}})
        if existing:
            await cq.message.reply_text(f"⚠️ You already purchased {PLAN_NAMES[plan]}.\nWait until it expires.")
            return

        await cq.message.edit_text(
            f"💳 Please pay ₹{prices[plan]} to:\n\n"
            f"👉 UPI ID: `{UPI_ID}`\n\n"
            "📸 After payment, send screenshot here to Admin: @M4U_Admin_Bot"
        )
        members.update_one(
            {"user_id": user_id, "plan": plan},
            {"$set": {"join_date": "PENDING"}},
            upsert=True
        )
        return

    # Approve button
    if cq.data.startswith("approve_"):
        _, user_id, plan = cq.data.split("_")
        user_id = int(user_id)
        join_date = datetime.date.today().isoformat()

        try:
            if plan == "m4u":
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
                    f"🎉 Approved!\nHere are your links:\n\n🔹 {invite1.invite_link}\n🔹 {invite2.invite_link}"
                )

            members.update_one(
                {"user_id": user_id, "plan": plan},
                {"$set": {"join_date": join_date}},
                upsert=True
            )

            await cq.message.edit_text(f"✅ Approved {user_id} for **{PLAN_NAMES[plan]}** plan")

        except Exception as e:
            await cq.message.edit_text(f"⚠️ Error: {e}")


# ==== Handle Screenshot ====
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
            [InlineKeyboardButton(f"✅ {PLAN_NAMES['m4u']}", callback_data=f"approve_{user_id}_m4u")],
            [InlineKeyboardButton(f"✅ {PLAN_NAMES['file']}", callback_data=f"approve_{user_id}_file")],
            [InlineKeyboardButton(f"✅ {PLAN_NAMES['both']}", callback_data=f"approve_{user_id}_both")],
        ])
    )
    await message.reply_text("✅ Screenshot sent to admin for verification. Please wait...")


# ==== Auto Remove After 1 Day (for testing) ====
async def check_and_remove():
    while True:
        today = datetime.date.today()
        for doc in members.find({"join_date": {"$ne": "PENDING"}}):
            user_id = doc["user_id"]
            plan = doc["plan"]
            join_date = datetime.date.fromisoformat(doc["join_date"])
            days_passed = (today - join_date).days

            if days_passed >= 1:  # 1 day for testing
                try:
                    if plan in ["m4u", "both"]:
                        await app.ban_chat_member(CHANNEL_1, user_id)
                    if plan in ["file", "both"]:
                        await app.ban_chat_member(CHANNEL_2, user_id)

                    await app.send_message(
                        user_id,
                        f"❌ Your subscription for {PLAN_NAMES[plan]} expired.\n\n"
                        "Please pay again using /buy to rejoin."
                    )
                    members.delete_one({"user_id": user_id, "plan": plan})
                    print(f"Removed {user_id} from {PLAN_NAMES[plan]}")
                except Exception as e:
                    print("Error removing:", e)

        await asyncio.sleep(86400)  # check daily


# ==== RUN BOT ====
async def main():
    asyncio.create_task(check_and_remove())
    await app.start()
    print("Bot running...")
    await idle()

if __name__ == "__main__":
    app.run(main())
