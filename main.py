import os
import sqlite3
import io
import random
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from PIL import Image, ImageDraw
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# --- Render ሰርቨር ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Running!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

# --- ዋና ቅንብሮች ---
TOKEN = "8667033966:AAF_rL_vAKyNC9vtOf2mo3d8Zb-zJ5RdEAw"
ADMINS = [7705713321, 7868124597]
CAR, F_NAME, L_NAME, PHONE, TICKET, PAYMENT, SCREENSHOT, ADMIN_BROADCAST = range(8)

CAR_DATA = {"Sino": "3000 BIRR", "Isuzu": "2000 BIRR"}
PAYMENT_INFO = {"Telebirr": "ቁጥር: 0954873497", "CBE": "አካውንት: 1000536009276"}

def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, car TEXT, name TEXT, phone TEXT, ticket TEXT, payment TEXT, proof TEXT, status TEXT, reg_code TEXT, sale_date TEXT)''')
    conn.commit()
    conn.close()

# --- እጅግ በጣም ትልቅ የቲኬት ዲዛይን ---
def create_ticket_image(name, ticket, car, phone, reg_code, sale_date):
    img = Image.new('RGB', (2000, 1400), color=(10, 10, 10))
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, 1950, 1350], outline=(212, 175, 55), width=50)
    
    # ጽሁፎችን በጣም በትልቁ መሳል
    d.text((550, 100), "ግዛቸው የመኪና እቁብ", fill=(212, 175, 55))
    d.text((150, 350), f"ሙሉ ስም: {name.upper()}", fill=(255, 255, 255))
    d.text((150, 520), f"መኪና: {car.upper()}", fill=(255, 255, 255))
    d.text((150, 690), f"ስልክ: {phone}", fill=(255, 255, 255))
    d.text((150, 860), f"መዝገብ ቁጥር: {reg_code}", fill=(255, 255, 255))
    d.text((150, 1030), f"ቀን: {sale_date}", fill=(255, 255, 255))
    
    d.text((1200, 700), "TICKET NO:", fill=(212, 175, 55))
    d.text((1250, 880), f"#{ticket}", fill=(0, 255, 127))
    d.text((800, 1220), "🎉 መልካም እድል 🎉", fill=(212, 175, 55))

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# --- የአድሚን ማስታወቂያ መላኪያ ---
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ለተጠቃሚዎች የሚላክ ጽሁፍ፣ ፎቶ ወይም ቪዲዮ ይላኩ (ወደ ኋላ ለመመለስ /start ይበሉ)፦")
    return ADMIN_BROADCAST

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('lottery.db')
    users = conn.execute("SELECT id FROM users").fetchall()
    conn.close()
    for user in users:
        try:
            if update.message.text: await context.bot.send_message(user[0], update.message.text)
            elif update.message.photo: await context.bot.send_photo(user[0], update.message.photo[-1].file_id, caption=update.message.caption)
            elif update.message.video: await context.bot.send_video(user[0], update.message.video.file_id, caption=update.message.caption)
        except: continue
    await update.message.reply_text("✅ ማስታወቂያው ለሁሉም ተልኳል!")
    return ConversationHandler.END

# --- የተጠቃሚ ምዝገባ ሂደት ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["Sino", "Isuzu"]]
    if update.effective_user.id in ADMINS: kb.append(["📢 ማስታወቂያ ላክ"])
    await update.message.reply_text("እንኳን ወደ ግዛቸው የመኪና እቁብ በደህና መጡ\n\nእባክዎ መኪና ይምረጡ፦", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CAR

async def car_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice == "📢 ማስታወቂያ ላክ": return await broadcast_start(update, context)
    context.user_data['car'] = choice
    price = CAR_DATA.get(choice)
    await update.message.reply_text(f"የመረጡት መኪና: {choice}\nዋጋ: {price}\n\nእባክዎ የመጀመሪያ ስምዎን ያስገቡ፦", 
                                   reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return F_NAME

async def get_f_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return await start(update, context)
    context.user_data['f_name'] = update.message.text
    await update.message.reply_text("እባክዎ የመጨረሻ (የአባት) ስምዎን ያስገቡ፦")
    return L_NAME

async def get_l_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": 
        await update.message.reply_text("እባክዎ የመጀመሪያ ስምዎን ያስገቡ፦")
        return F_NAME
    context.user_data['l_name'] = update.message.text
    await update.message.reply_text("የኢትዮጵያ ስልክ ቁጥርዎን ያስገቡ (ምሳሌ፦ +2519...)፦")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ":
        await update.message.reply_text("እባክዎ የመጨረሻ (የአባት) ስምዎን ያስገቡ፦")
        return L_NAME
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("ከ 1-1000 ያለ የቲኬት ቁጥር ይምረጡ (በቁጥር ብቻ)፦")
    return TICKET

async def get_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ":
        await update.message.reply_text("ስልክ ቁጥርዎን ያስገቡ፦")
        return PHONE
    num = update.message.text
    if not num.isdigit():
        await update.message.reply_text("⚠️ እባክዎ ቁጥር ብቻ ያስገቡ፦")
        return TICKET
    
    conn = sqlite3.connect('lottery.db')
    exists = conn.execute("SELECT id FROM users WHERE ticket=? AND status='Verified'", (num,)).fetchone()
    conn.close()
    if exists:
        await update.message.reply_text("❌ ይቅርታ ይህ ቲኬት ቀድሞ ተይዟል! እባክዎ ሌላ ቁጥር ይምረጡ፦")
        return TICKET

    context.user_data['ticket'] = num
    kb = [["Telebirr", "CBE"], ["⬅️ ተመለስ"]]
    await update.message.reply_text("የክፍያ ዘዴ ይምረጡ፦", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return PAYMENT

async def get_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ":
        await update.message.reply_text("የቲኬት ቁጥርዎን ያስገቡ፦")
        return TICKET
    p = update.message.text
    context.user_data['payment'] = p
    await update.message.reply_text(f"{PAYMENT_INFO.get(p)}\n\nክፍያውን ፈጽመው ስክሪንሾት ይላኩ፦")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        # ለአድሚን መላክ
        admin_txt = f"🔔 አዲስ የክፍያ ጥያቄ!\n👤 ስም: {full_name}\n🚗 መኪና: {d['car']}\n🎫 ቲኬት: {d['ticket']}"
        kb = [[InlineKeyboardButton("✅ አጽድቅ", callback_data=f"v_{uid}"), InlineKeyboardButton("❌ ሰርዝ", callback_data=f"r_{uid}")]]
        for a in ADMINS: await context.bot.send_photo(a, fid, caption=admin_txt, reply_markup=InlineKeyboardMarkup(kb))
        
        await update.message.reply_text("ክፍያው እስከሚረጋገጥ ትንሽ ይጠብቁ...", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return SCREENSHOT

async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            img = create_ticket_image(*u)
            await context.bot.send_photo(uid, img, caption="እጣው በሚገባ ተመዝግቧል!\n🎉 መልካም እድል 🎉")
            await q.edit_message_caption("✅ ጸድቋል!")
    else:
        await q.edit_message_caption("❌ ተሰርዟል!")

if __name__ == '__main__':
    init_db()
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CallbackQueryHandler(handle_verification))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(filters.Regex('^⬅️ ተመለስ$'), start)],
        states={
            CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_chosen)],
            F_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_f_name)],
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_f_name)], # Reuse logic
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_l_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            TICKET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ticket)],
            PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
            ADMIN_BROADCAST: [MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO) & ~filters.COMMAND, send_broadcast)]
        },
        fallbacks=[CommandHandler('start', start)]
    ))
    application.run_polling()
