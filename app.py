import os
import random
import time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("8083828200:AAE9RY4TW2BAUJqdJF1KLXpzK_-7V8aULSY")  # Put BOT_TOKEN in Render environment variables
WEBHOOK_URL = "https://captcha2earn-system-3.onrender.com"  # 👈 Replace with your Render app URL

# ========== USER DATA (in-memory) ==========
users = {}
invites = {}

# ========== HELPERS ==========
def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "withdrawable": 0,
            "invites": [],
            "earned_from_invites": 0,
            "captcha_done": 0,
            "last_captcha_time": 0
        }
    return users[user_id]

# ========== COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    # Handle referrals
    if context.args:
        referrer_id = int(context.args[0])
        if referrer_id != update.effective_user.id:
            invites[user["balance"]] = referrer_id
            referrer = get_user(referrer_id)
            if update.effective_user.id not in referrer["invites"]:
                referrer["invites"].append(update.effective_user.id)

    await update.message.reply_text(
        "🤖 Welcome to Captcha2Earn Casino Bot!\n"
        "Use /about to learn the rules."
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    await update.message.reply_text(
        f"💰 Your wallet is shining!\n"
        f"Main Balance: {user['balance']} pesos\n"
        f"Withdrawable: {user['withdrawable']} pesos"
    )

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if user["withdrawable"] <= 0:
        await update.message.reply_text("⚠️ You have no withdrawable balance yet.")
        return
    if len(user["invites"]) < 10:
        await update.message.reply_text("🚫 You need at least 10 invites before withdrawing.")
        return
    await update.message.reply_text(
        "✅ Withdrawal request started.\n"
        "Send your Full Name and GCash number to proceed."
    )

async def captcha2earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)

    # Invite restriction
    if user["captcha_done"] >= 50 and len(user["invites"]) < 1:
        await update.message.reply_text(
            "🚫 You must invite at least 1 friend to continue captcha earning."
        )
        return

    # Cooldown
    if time.time() - user["last_captcha_time"] < 5:
        await update.message.reply_text("⏳ Wait 5 seconds before solving next captcha.")
        return

    # Reward
    reward = random.randint(1, 10)
    user["balance"] += reward
    user["withdrawable"] += reward
    user["captcha_done"] += 1
    user["last_captcha_time"] = time.time()

    # Invite commission
    for referrer_id, invitee_id in invites.items():
        if invitee_id == user_id:
            referrer = get_user(referrer_id)
            commission = reward * 0.1
            referrer["balance"] += commission
            referrer["withdrawable"] += commission
            referrer["earned_from_invites"] += commission

    await update.message.reply_text(f"🧩 Captcha solved! You earned ₱{reward}.")

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
    await update.message.reply_text(
        f"👥 Your invite link: {ref_link}\n"
        f"Invited: {len(user['invites'])} people\n"
        f"Earned from invites: ₱{user['earned_from_invites']:.2f}"
    )

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if len(context.args) < 2:
        await update.message.reply_text("🎲 Usage: /dice <bet_amount> <even|odd>")
        return

    try:
        bet = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Bet must be a number.")
        return

    choice = context.args[1].lower()
    if bet > user["balance"]:
        await update.message.reply_text("⚠️ You don’t have enough balance.")
        return

    roll = random.randint(1, 6)
    result = "even" if roll % 2 == 0 else "odd"

    if choice == result:
        winnings = bet * 2
        user["balance"] += winnings
        await update.message.reply_text(f"🎲 Rolled {roll}! You won ₱{winnings}!")
    else:
        user["balance"] -= bet
        await update.message.reply_text(f"🎲 Rolled {roll}. You lost ₱{bet}.")

async def scatterspin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if len(context.args) < 1:
        await update.message.reply_text("🎰 Usage: /scatterSpin <bet_amount>")
        return

    try:
        bet = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Bet must be a number.")
        return

    if bet > user["balance"]:
        await update.message.reply_text("⚠️ Not enough balance.")
        return

    symbols = ["🍒", "7️⃣", "⭐", "💎"]
    spin = [random.choice(symbols) for _ in range(3)]

    if spin.count("7️⃣") == 3:
        multiplier = 10
    elif len(set(spin)) == 1:
        multiplier = 5
    elif len(set(spin)) == 2:
        multiplier = 2
    else:
        multiplier = 0

    winnings = bet * multiplier
    user["balance"] += winnings - bet  # subtract bet, add winnings

    await update.message.reply_text(f"🎰 {' '.join(spin)}\nYou won ₱{winnings}!")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Captcha2Earn Casino Bot\n\n"
        "🧩 Solve captchas to earn ₱1–₱10 each (cooldown 5s).\n"
        "👥 Invite friends to earn 10% of their captcha earnings.\n"
        "🎲 Play /dice or 🎰 /scatterSpin to test your luck.\n"
        "💵 Withdraw requires: 10 invites + played games.\n"
    )

# ========== MAIN ==========
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("withdraw", withdraw))
    application.add_handler(CommandHandler("captcha2earn", captcha2earn))
    application.add_handler(CommandHandler("invite", invite))
    application.add_handler(CommandHandler("dice", dice))
    application.add_handler(CommandHandler("scatterSpin", scatterspin))
    application.add_handler(CommandHandler("about", about))

    application.run_webhook(
        listen="0.0.0.0",
        port=5000,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )

if __name__ == "__main__":
    main()
