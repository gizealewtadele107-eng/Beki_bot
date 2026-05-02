import os
import sqlite3
import random
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# --- 1. ቦቱ እንዳይተኛ (Keep-Alive) የሚያደርግ የ Flask ሰርቨር ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online and Active!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. ዋና ቅንብሮች ---
TOKEN = "8667033966:AAF_rL_vAKyNC9vtOf2mo3d8Zb-zJ5RdEAw"
ADMINS = [7868124597] 
CAR, F_NAME, L_NAME, PHONE, TICKET, PAYMENT, SCREENSHOT, QUESTION, BROADCAST = range(9)

CAR_DATA = {"Sino": "3000 BIRR", "Isuzu": "2000 BIRR"}
PAYMENT_INFO = {"Telebirr": "ቁጥር: 0954873497", "CBE": "አካውንት: 1000536009276"}

def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, car TEXT, name TEXT, phone TEXT, ticket TEXT, payment TEXT, proof TEXT, status TEXT, reg_code TEXT, sale_date TEXT)''')
    conn.commit()
    conn.close()

# --- 3. ቦት ተግባራት ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    kb = [["Sino", "Isuzu"], ["❓ ጥያቄ ለመጠየቅ"]]
    if update.effective_user.id in ADMINS: 
        kb.append(["📢 ማስታወቂያ ላክ"])
    await update.message.reply_text(
        "👋 እንኳን ወደ ግዛቸው የመኪና እቁብ በደህና መጡ\n\nእባክዎ መኪና ይምረጡ፦", 
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    return CAR

async def car_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice == "📢 ማስታወቂያ ላክ":
        await update.message.reply_text("ለተጠቃሚዎች የሚላክ መልእክት ወይም ፎቶ ይላኩ፦")
        return BROADCAST
    if choice == "❓ ጥያቄ ለመጠየቅ":
        await update.message.reply_text("ጥያቄዎን እዚህ ይጻፉ፤ አድሚኑ መልስ ይሰጥዎታል፦")
        return QUESTION
        
    context.user_data['car'] = choice
    await update.message.reply_text(
        f"🚗 የመረጡት መኪና: {choice}\n💰 ዋጋ: {CAR_DATA[choice]}\n\n👤 የመጀመሪያ ስምዎን ያስገቡ፦", 
        reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True)
    )
    return F_NAME

# --- ጥያቄ ለመቀበል ---
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    txt = update.message.text
    admin_msg = f"📩 **አዲስ ጥያቄ መጥቷል!**\n\n👤 ስም: {user.first_name}\n🆔 ID: {user.id}\n📝 ጥያቄ: {txt}"
    for a in ADMINS:
        await context.bot.send_message(a, admin_msg)
    await update.message.reply_text("✅ ጥያቄዎ ተልኳል! አድሚኑ በቅርቡ ይመልስልዎታል። ወደ መጀመሪያ ለመመለስ /start ይበሉ")
    return ConversationHandler.END

async def f_name_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return await start(update, context)
    context.user_data['f_name'] = update.message.text
    await update.message.reply_text("👤 የአባት ስምዎን ያስገቡ፦")
    return L_NAME

async def l_name_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return F_NAME
    context.user_data['l_name'] = update.message.text
    await update.message.reply_text("📞 ስልክ ቁጥርዎን ያስገቡ (+251...)፦")
    return PHONE

async def phone_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return L_NAME
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("🎫 ከ 1-1000 ያለ የቲኬት ቁጥር ይምረጡ፦")
    return TICKET

async def ticket_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return PHONE
    num = update.message.text
    if not num.isdigit():
        await update.message.reply_text("⚠️ እባክዎ ቁጥር ብቻ ያስገቡ፦")
        return TICKET
    
    conn = sqlite3.connect('lottery.db')
    check = conn.execute("SELECT id FROM users WHERE ticket=? AND status='Verified'", (num,)).fetchone()
    conn.close()
    if check:
        await update.message.reply_text("❌ ይህ ቲኬት ተይዟል! እባክዎ ሌላ ቁጥር ይምረጡ፦")
        return TICKET

    context.user_data['ticket'] = num
    kb = [["Telebirr", "CBE"], ["⬅️ ተመለስ"]]
    await update.message.reply_text("💳 የክፍያ ዘዴ ይምረጡ፦", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return PAYMENT

async def payment_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return TICKET
    p = update.message.text
    context.user_data['payment'] = p
    await update.message.reply_text(f"💳 {PAYMENT_INFO.get(p)}\n\n📸 ክፍያውን ፈጽመው ስክሪንሾት (Screenshot) ይላኩ፦")
    return SCREENSHOT

async def screenshot_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        fid = update.message.photo[-1].file_id
        d, uid = context.user_data, update.effective_user.id
        full_name = f"{d['f_name']} {d['l_name']}"
        reg, date = str(random.randint(100000, 999999)), (datetime.now() + timedelta(hours=3)).strftime("%d/%m/%Y")
        
        conn = sqlite3.connect('lottery.db')
        conn.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?,?,?,?)", 
                     (uid, d['car'], full_name, d['phone'], d['ticket'], d['payment'], fid, 'Pending', reg, date))
        conn.commit()
        conn.close()
        
        admin_txt = f"🔔 **አዲስ የክፍያ ጥያቄ!**\n\n👤 ስም: {full_name}\n📞 ስልክ: {d['phone']}\n🚗 መኪና: {d['car']}\n🎫 ቲኬት: {d['ticket']}"
        kb = [[InlineKeyboardButton("✅ አጽድቅ", callback_data=f"v_{uid}"), InlineKeyboardButton("❌ ሰርዝ", callback_data=f"r_{uid}")]]
        
        for a in ADMINS:
            try: await context.bot.send_photo(chat_id=a, photo=fid, caption=admin_txt, reply_markup=InlineKeyboardMarkup(kb))
            except: pass
        
        await update.message.reply_text("⌛ ጥያቄዎ በሚገባ ተመዝግቧል! አድሚኑ ክፍያውን እስኪያረጋግጥ ድረስ ትንሽ ይጠብቁ...", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return SCREENSHOT

async def handle_v(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    act, uid = q.data.split("_")
    if act == "v":
        conn = sqlite3.connect('lottery.db')
        conn.execute("UPDATE users SET status='Verified' WHERE id=?", (uid,))
        u = conn.execute("SELECT name, ticket, car, phone, reg_code, sale_date FROM users WHERE id=?", (uid,)).fetchone()
        conn.commit()
        conn.close()
        if u:
            # ጽሁፍ እና አይኮን ብቻ በመጠቀም ቲኬት መላክ (ፎቶ የለም)
            msg = (
                f"✅ **በተሳካ ሁኔታ ተመዝግበዋል!**\n\n"
                f"🎫 **የቲኬት መረጃ**\n"
                f"━━━━━━━━━━━━━━━\n"
                f"👤 ሙሉ ስም: {u[0]}\n"
                f"🚗 የመረጡት መኪና: {u[2]}\n"
                f"🎫 የቲኬት ቁጥር: #{u[1]}\n"
                f"📞 ስልክ: {u[3]}\n"
                f"🆔 መዝገብ ቁጥር: {u[4]}\n"
                f"📅 ቀን: {u[5]}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🎉 **መልካም እድል!** 🎉"
            )
            await context.bot.send_message(uid, msg, reply_markup=ReplyKeyboardMarkup([["ሌላ እጣ ይቁረጡ"]], resize_keyboard=True))
            await q.edit_message_caption(q.message.caption + "\n\n✅ ተረጋግጧል!")
    else:
        await q.edit_message_caption(q.message.caption + "\n\n❌ ተሰርዟል!")

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('lottery.db')
    users = conn.execute("SELECT id FROM users").fetchall()
    conn.close()
    for u in users:
        try:
            if update.message.text: 
                await context.bot.send_message(u[0], update.message.text)
            elif update.message.photo: 
                await context.bot.send_photo(u[0], update.message.photo[-1].file_id, caption=update.message.caption)
        except: pass
    await update.message.reply_text("✅ ማስታወቂያው ለሁሉም ተልኳል!")
    return ConversationHandler.END

if __name__ == '__main__':
    keep_alive() # ቦቱ ሳይዘጋ እንዲቆይ
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CallbackQueryHandler(handle_v))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(filters.Regex('^ሌላ እጣ ይቁረጡ$'), start)],
        states={
            CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_step)],
            F_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, f_name_step)],
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, l_name_step)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_step)],
            TICKET: [MessageHandler(filters.TEXT & ~filters.COMMAND, ticket_step)],
            PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_step)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, screenshot_step)],
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question)],
            BROADCAST: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, broadcast_handler)]
        },
        fallbacks=[CommandHandler('start', start)]
    ))
    application.run_polling()
