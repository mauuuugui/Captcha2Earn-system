import os
import random
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ==========================
# CONFIG
# ==========================
TOKEN = os.getenv("BOT_TOKEN")  # set BOT_TOKEN in Render environment
PORT = int(os.environ.get("PORT", 8080))

# balances stored in memory (use DB for production)
user_data = {}

# ==========================
# FLASK SERVER
# ==========================
app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot.application.bot)
    bot.application.update_queue.put_nowait(update)
    return "ok"

# ==========================
# TELEGRAM BOT COMMANDS
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data.setdefault(user.id, {"balance": 0, "withdrawable": 0})
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n"
        "Use /balance to check your pesos 💰\n"
        "Use /captcha2earn to solve captchas 🧩\n"
        "Use /dice to gamble 🎲\n"
        "Use /scatterspin to spin 🎰\n"
        "Use /withdraw to cash out 💵"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = user_data.get(user.id, {"balance": 0, "withdrawable": 0})
    await update.message.reply_text(
        f"⚖️ Balance: {data['balance']} pesos\n"
        f"💵 Withdrawable: {data['withdrawable']} pesos"
    )

async def captcha2earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reward = random.randint(1, 10)
    user_data.setdefault(user.id, {"balance": 0, "withdrawable": 0})
    user_data[user.id]["balance"] += reward
    await update.message.reply_text(
        f"🧩 Captcha solved!\nYou earned ₱{reward}.\n"
        f"💰 Total balance: {user_data[user.id]['balance']} pesos"
    )

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = user_data.get(user.id, {"balance": 0, "withdrawable": 0})
    if data["withdrawable"] <= 0:
        await update.message.reply_text(
            "🚫 You don’t have withdrawable balance yet.\n"
            "👉 Play games and invite friends first!"
        )
    else:
        await update.message.reply_text(
            "💵 Withdrawal request started!\n"
            "Please send your Full Name + GCash number here."
        )

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    roll = random.randint(1, 6)
    await update.message.reply_text(f"🎲 You rolled: {roll}")

async def scatterspin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbols = ["🍒", "7️⃣", "⭐", "💎"]
    spin = [random.choice(symbols) for _ in range(3)]
    result = " ".join(spin)
    await update.message.reply_text(f"🎰 {result}")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ About this bot:\n"
        "Earn by solving captchas, playing games, and inviting friends!\n"
        "🔑 Rules:\n"
        "• Invite 10 people to unlock withdrawals\n"
        "• Must play before withdrawing\n"
        "• After 50 captchas, invite 1 person to continue"
    )

# ==========================
# MAIN
# ==========================
def main():
    global bot
    application = Application.builder().token(TOKEN).build()
    bot = application

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("captcha2earn", captcha2earn))
    application.add_handler(CommandHandler("withdraw", withdraw))
    application.add_handler(CommandHandler("dice", dice))
    application.add_handler(CommandHandler("scatterspin", scatterspin))
    application.add_handler(CommandHandler("about", about))

    # Run Flask + Telegram webhook
    async def run():
        await application.initialize()
        await application.start()
        await application.bot.set_webhook(f"{os.getenv('RENDER_EXTERNAL_URL')}/webhook")
        await application.updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="webhook",
            webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL')}/webhook"
        )

    loop = asyncio.get_event_loop()
    loop.create_task(run())
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
