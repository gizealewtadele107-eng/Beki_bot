import os
import sqlite3
import io
import random
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# --- Render አገልጋይ ---
app = Flask('')
@app.route('/')
def home(): return "ቦቱ በሰላም እየሰራ ነው!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

# --- ዋና ቅንብሮች ---
TOKEN = "8667033966:AAF_rL_vAKyNC9vtOf2mo3d8Zb-zJ5RdEAw"
ADMINS = [7705713321, 7868124597] 
CAR_SELECTION, NAME, PHONE, TICKET_NUM, PAYMENT_METHOD, SCREENSHOT, ADMIN_BROADCAST = range(7)

PAYMENT_INFO = {"Telebirr": "ቁጥር: 0954873497", "CBE": "አካውንት: 1000536009276"}

def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, car TEXT, name TEXT, phone TEXT, ticket TEXT, payment TEXT, proof TEXT, status TEXT, reg_code TEXT, sale_date TEXT)''')
    conn.commit()
    conn.close()

# --- ማራኪ የቲኬት ፎቶ ማዘጋጃ (ጽሁፉ ትልቅ ሆኗል) ---
def create_ticket_image(name, ticket, car, phone, reg_code, sale_date):
    img = Image.new('RGB', (1000, 700), color=(10, 10, 10)) # መጠኑ ሰፋ ብሏል
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 980, 680], outline=(212, 175, 55), width=15)
    
    # ጽሁፎችን በትልቁ መጻፍ
    d.text((250, 50), "ግዛቸው የመኪና ሎተሪ", fill=(212, 175, 55))
    d.text((80, 150), f"👤 ስም: {name.upper()}", fill=(255, 255, 255))
    d.text((80, 230), f"🚗 መኪና: {car.upper()}", fill=(255, 255, 255))
    d.text((80, 310), f"📞 ስልክ: {phone}", fill=(255, 255, 255))
    d.text((80, 390), f"🔑 መዝገብ ቁጥር: {reg_code}", fill=(255, 255, 255))
    d.text((80, 470), f"📅 ቀን: {sale_date}", fill=(255, 255, 255))
    
    d.text((600, 400), "TICKET NO:", fill=(212, 175, 55))
    d.text((620, 480), f"#{ticket}", fill=(0, 255, 127))
    d.text((380, 600), "መልካም እድል", fill=(212, 175, 55))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# --- የአድሚን መልእክት መላኪያ ---
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ለተጠቃሚዎች የሚላክ ፎቶ እና ጽሁፍ ይላኩ፦")
    return ADMIN_BROADCAST

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo = update.message.photo[-1].file_id
        caption = update.message.caption
        conn = sqlite3.connect('lottery.db')
        users = conn.execute("SELECT id FROM users").fetchall()
        conn.close()
        for user in users:
            try: await context.bot.send_photo(user[0], photo, caption=caption)
            except: continue
        await update.message.reply_text("✅ ተልኳል!")
    return ConversationHandler.END

# --- ምዝገባ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["Sino", "Isuzu"], ["Toyota"]]
    if update.effective_user.id in ADMINS:
        kb.append(["📣 ለሁሉም መልእክት ላክ"])
    await update.message.reply_text("እንኳን ደህና መጡ! መኪና ይምረጡ፦", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CAR_SELECTION

async def car_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📣 ለሁሉም መልእክት ላክ": return await broadcast_start(update, context)
    context.user_data['car'] = update.message.text
    await update.message.reply_text("ሙሉ ስምዎን (ባለ 3 ቃል) ያስገቡ፦", reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return await start(update, context)
    if len(update.message.text.split()) < 3:
        await update.message.reply_text("⚠️ ስም ባለ 3 ቃል መሆን አለበት፦")
        return NAME
    context.user_data['name'] = update.message.text
    await update.message.reply_text("ስልክ ቁጥር ያስገቡ፦", reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return NAME
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("ከ 1-1000 ያለ የቲኬት ቁጥር ይምረጡ፦", reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return TICKET_NUM

async def get_ticket_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return PHONE
    num = update.message.text
    
    # ቲኬቱ መያዙን ማረጋገጥ
    conn = sqlite3.connect('lottery.db')
    check = conn.execute("SELECT id FROM users WHERE ticket = ? AND status = 'Verified'", (num,)).fetchone()
    conn.close()
    
    if check:
        await update.message.reply_text("❌ ይቅርታ ይህ ቲኬት ተይዟል! ሌላ ቁጥር ይምረጡ፦")
        return TICKET_NUM
    
    context.user_data['ticket'] = num
    await update.message.reply_text("የክፍያ ዘዴ ይምረጡ፦", reply_markup=ReplyKeyboardMarkup([["Telebirr", "CBE"], ["⬅️ ተመለስ"]], resize_keyboard=True))
    return PAYMENT_METHOD

async def payment_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return TICKET_NUM
    context.user_data['payment'] = update.message.text
    await update.message.reply_text(f"{PAYMENT_INFO.get(update.message.text)}\n\nክፍያውን ፈጽመው ስክሪንሾት ይላኩ፦")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        d, uid = context.user_data, update.effective_user.id
        reg = str(random.randint(100000, 999999))
        date = (datetime.now() + timedelta(hours=3)).strftime("%d/%m/%Y")
        
        conn = sqlite3.connect('lottery.db')
        conn.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?,?,?,?)", (uid, d['car'], d['name'], d['phone'], d['ticket'], d['payment'], file_id, 'Pending', reg, date))
        conn.commit()
        conn.close()
        
        text = f"🔔 አዲስ ጥያቄ!\n👤 ስም: {d['name']}\n📞 ስልክ: {d['phone']}\n🎫 ቲኬት: {d['ticket']}"
        kb = [[InlineKeyboardButton("✅ Approve", callback_data=f"verify_{uid}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}")]]
        for admin in ADMINS:
            try: await context.bot.send_photo(admin, file_id, caption=text, reply_markup=InlineKeyboardMarkup(kb))
            except: continue
        await update.message.reply_text("✅ ተልኳል! አስተዳዳሪው ሲያጸድቅ ቲኬቱ ይላክልዎታል።", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return SCREENSHOT

async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, uid = query.data.split("_")
    uid = int(uid)
    
    if action == "verify":
        conn = sqlite3.connect('lottery.db')
        conn.execute("UPDATE users SET status = 'Verified' WHERE id = ?", (uid,))
        u = conn.execute("SELECT name, ticket, car, phone, reg_code, sale_date FROM users WHERE id = ?", (uid,)).fetchone()
        conn.commit()
        conn.close()
        
        if u:
            img = create_ticket_image(*u)
            kb = ReplyKeyboardMarkup([["ሌላ የቁረጡ 🎫"]], resize_keyboard=True)
            await context.bot.send_photo(uid, img, caption="🎉 መልካም እድል 🎉", reply_markup=kb)
            await query.edit_message_caption(caption=query.message.caption + "\n\n✅ ጸድቋል!")
    else:
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ ተሰርዟል!")

if __name__ == '__main__':
    init_db()
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CallbackQueryHandler(handle_verification))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(filters.Regex('^ሌላ የቁረጡ 🎫$'), start)],
        states={
            CAR_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_chosen)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            TICKET_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ticket_num)],
            PAYMENT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_chosen)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
            ADMIN_BROADCAST: [MessageHandler(filters.PHOTO, send_broadcast)]
        },
        fallbacks=[CommandHandler('start', start)]
    ))
    application.run_polling())
