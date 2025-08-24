import os
import random
import string
import io
import asyncio
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, request
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN", "8083828200:AAE9RY4TW2BAUJqdJF1KLXpzK_-7V8aULSY")

users = {}

flask_app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()

# =========================
# Helpers
# =========================
def get_user(uid):
    if uid not in users:
        users[uid] = {
            "balance": 0,
            "withdrawable": 0,
            "captcha_done": 0,
            "captcha_code": None,
            "invites": set(),
            "games_played": 0,
            "gcash": None,
            "fullname": None,
            "referrer": None
        }
    return users[uid]

def generate_captcha():
    text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    img = Image.new('RGB', (200, 70), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    draw.text((40, 15), text, font=font, fill=(0, 0, 0))
    bio = io.BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)
    return text, bio

# =========================
# Commands
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    args = context.args
    if args and args[0].isdigit():  # Referral system
        ref_id = int(args[0])
        if ref_id != update.effective_user.id:
            ref = get_user(ref_id)
            ref["invites"].add(update.effective_user.id)
            u["referrer"] = ref_id
    await update.message.reply_text("👋 Welcome! Use /captcha2earn to earn money by solving captchas!")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    await update.message.reply_text(
        f"💰 Your wallet is shining!\n\n"
        f"Main Balance: ₱{u['balance']}\n"
        f"Withdrawable Balance: ₱{u['withdrawable']}\n"
        f"Captchas Solved: {u['captcha_done']}\n"
        f"Invites: {len(u['invites'])}"
    )

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    if u['withdrawable'] <= 0:
        await update.message.reply_text("❌ You don’t have withdrawable balance yet.")
        return
    if len(u['invites']) < 10:
        await update.message.reply_text("❌ You must invite at least 10 people before withdrawing.")
        return
    if u['games_played'] < 1:
        await update.message.reply_text("🎮 You must play at least one game before withdrawing.")
        return
    await update.message.reply_text("💵 Please send your full name:")
    context.user_data["withdraw_step"] = "name"

async def captcha2earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    if u["captcha_done"] >= 50 and len(u["invites"]) < 1:
        await update.message.reply_text("❌ You need to invite at least 1 friend to continue earning captchas.")
        return
    code, img = generate_captcha()
    u["captcha_code"] = code
    await update.message.reply_photo(photo=InputFile(img, filename="captcha.png"), caption="🧩 Solve this captcha (5 sec limit)")
    await asyncio.sleep(5)
    u["captcha_code"] = None

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    link = f"https://t.me/{context.bot.username}?start={update.effective_user.id}"
    total_earn = sum(users[i]["balance"]*0.1 for i in u["invites"])
    await update.message.reply_text(
        f"👥 Invite friends & earn 10% of their captcha earnings!\n\n"
        f"Your link: {link}\n"
        f"Invites: {len(u['invites'])}\n"
        f"Earnings from invites: ₱{total_earn:.2f}"
    )

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    if len(context.args) < 2:
        await update.message.reply_text("🎲 Usage: /dice <bet_amount> <even/odd>")
        return
    bet = int(context.args[0])
    choice = context.args[1].lower()
    if u["balance"] < bet:
        await update.message.reply_text("❌ Not enough balance.")
        return
    roll = random.randint(1, 6)
    u["games_played"] += 1
    if (choice == "even" and roll % 2 == 0) or (choice == "odd" and roll % 2 == 1):
        u["balance"] += bet
        await update.message.reply_text(f"🎲 Rolled {roll}! You win ₱{bet}. Balance: ₱{u['balance']}")
    else:
        u["balance"] -= bet
        await update.message.reply_text(f"🎲 Rolled {roll}! You lost ₱{bet}. Balance: ₱{u['balance']}")

async def scatter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("🎰 Usage: /scatterSpin <bet_amount>")
        return
    bet = int(context.args[0])
    if u["balance"] < bet:
        await update.message.reply_text("❌ Not enough balance.")
        return
    u["games_played"] += 1
    symbols = ["🍒", "7️⃣", "⭐", "💎"]
    spin = [random.choice(symbols) for _ in range(3)]
    result = "".join(spin)
    win = 0
    if spin == ["7️⃣", "7️⃣", "7️⃣"]:
        win = bet * 10
    elif len(set(spin)) == 1:
        win = bet * 5
    elif len(set(spin)) == 2:
        win = bet * 2
    else:
        win = -bet
    u["balance"] += win
    await update.message.reply_text(f"🎰 {result}\nYou {'won' if win>0 else 'lost'} ₱{abs(win)}. Balance: ₱{u['balance']}")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ This is a fun earning & casino bot!\n\n"
        "🧩 Solve captchas to earn ₱1–₱10\n"
        "👥 Invite friends & earn 10% of their captcha earnings\n"
        "🎲 Play dice or 🎰 slot machine to grow your balance\n"
        "💵 Withdraw to GCash (after invites & games)\n\n"
        "⚠️ Rules:\n"
        "- Need 10 invites to withdraw\n"
        "- Must play games before withdrawing\n"
        "- After 50 captchas, you must invite 1 friend"
    )

# =========================
# Text handler (captcha answers & withdraw info)
# =========================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    step = context.user_data.get("withdraw_step")
    if step == "name":
        u["fullname"] = update.message.text
        await update.message.reply_text("📱 Now send your GCash number:")
        context.user_data["withdraw_step"] = "gcash"
        return
    elif step == "gcash":
        u["gcash"] = update.message.text
        await update.message.reply_text(f"✅ Withdraw request submitted for {u['fullname']} ({u['gcash']}).")
        u["withdrawable"] = 0
        context.user_data["withdraw_step"] = None
        return
    if u["captcha_code"] and update.message.text.upper() == u["captcha_code"]:
        earn = random.randint(1, 10)
        u["balance"] += earn
        u["withdrawable"] += earn
        u["captcha_done"] += 1
        if u["referrer"]:
            users[u["referrer"]]["balance"] += earn * 0.1
        await update.message.reply_text(f"✅ Correct! You earned ₱{earn}. Balance: ₱{u['balance']}")
        u["captcha_code"] = None

# =========================
# Flask + Webhook
# =========================
@flask_app.route("/" + BOT_TOKEN, methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    application.update_queue.put_nowait(update)
    return "OK"

@flask_app.route("/")
def index():
    return "Bot running!"

def main():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("withdraw", withdraw))
    application.add_handler(CommandHandler("captcha2earn", captcha2earn))
    application.add_handler(CommandHandler("invite", invite))
    application.add_handler(CommandHandler("dice", dice))
    application.add_handler(CommandHandler("scatterSpin", scatter))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    port = int(os.environ.get("PORT", 5000))
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,
        webhook_url=f"https://YOUR-RENDER-APP.onrender.com/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
