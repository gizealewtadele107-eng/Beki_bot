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

# --- Render ሰርቨር ---
app = Flask('')
@app.route('/')
def home(): return "ቦቱ እየሰራ ነው!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

# --- የቦቱ ቅንብሮች ---
TOKEN = "8667033966:AAF_rL_vAKyNC9vtOf2mo3d8Zb-zJ5RdEAw"
OWNER_ID = 7705713321
CAR_SELECTION, NAME, PHONE, TICKET_NUM, PAYMENT_METHOD, SCREENSHOT = range(6)

PRICES = {"Sino": "2000 ETB", "Isuzu": "1500 ETB", "Toyota": "1000 ETB"}
PAYMENT_INFO = {"Telebirr": "ቁጥር: 0954873497", "CBE": "አካውንት: 1000536009276"}

def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, car TEXT, name TEXT, phone TEXT, ticket TEXT, payment TEXT, proof TEXT, status TEXT, reg_code TEXT, sale_date TEXT)''')
    conn.commit()
    conn.close()

def create_ticket_image(name, ticket, car, phone, reg_code, sale_date):
    img = Image.new('RGB', (850, 550), color=(15, 15, 15))
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 830, 530], outline=(212, 175, 55), width=8)
    d.text((220, 45), "ታምራት የመኪና ሎተሪ ትኬት", fill=(212, 175, 55))
    d.text((70, 130), f"👤 ስም (NAME): {name.upper()}", fill=(255, 255, 255))
    d.text((70, 190), f"🚗 መኪና (CAR): {car.upper()}", fill=(255, 255, 255))
    d.text((70, 250), f"📞 ስልክ (PHONE): {phone}", fill=(255, 255, 255))
    d.text((70, 310), f"🔢 የምዝገባ ኮድ (REG CODE): {reg_code}", fill=(255, 255, 255))
    d.text((70, 370), f"📅 የተሸጠበት ቀን (DATE): {sale_date}", fill=(255, 255, 255))
    d.text((500, 320), "TICKET NO:", fill=(212, 175, 55))
    d.text((520, 370), f"#{ticket}", fill=(0, 255, 127))
    d.text((350, 480), "መልካም እድል", fill=(212, 175, 55))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, user_id = query.data.split("_")
    user_id = int(user_id)
    if action == "verify":
        conn = sqlite3.connect('lottery.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, ticket, car, phone, reg_code, sale_date FROM users WHERE id = ?", (user_id,))
        u = cursor.fetchone()
        if u:
            conn.execute("UPDATE users SET status = 'Verified' WHERE id = ?", (user_id,))
            conn.commit()
            t_img = create_ticket_image(u[0], u[1], u[2], u[3], u[4], u[5])
            await context.bot.send_photo(chat_id=user_id, photo=t_img, caption="✅ ክፍያዎ ተረጋግጧል! መልካም እድል!")
            await query.edit_message_caption(caption=query.message.caption + f"\n\n✅ ጸድቋል!")
        conn.close()
    else:
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ ተሰርዟል!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["Sino", "Isuzu"], ["Toyota"]]
    await update.message.reply_text("እንኳን ደህና መጡ! እባክዎ መኪና ይምረጡ፦", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CAR_SELECTION

async def car_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['car'] = update.message.text
    await update.message.reply_text("ሙሉ ስምዎን (ባለ 3 ቃል) ያስገቡ፦", reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "⬅️ ተመለስ": return await start(update, context)
    if len(text.split()) < 3:
        await update.message.reply_text("⚠️ ስምዎ በትክክል ባለ 3 ቃል መሆን አለበት (ለምሳሌ፦ ታምራት አበበ ካሳ)። እባክዎ በድጋሚ ያስገቡ፦")
        return NAME
    context.user_data['name'] = text
    await update.message.reply_text("ስልክ ቁጥርዎን ያስገቡ (10 አሃዝ)፦", reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "⬅️ ተመለስ": return NAME
    if not (text.startswith('0') and len(text) == 10 and text.isdigit()):
        await update.message.reply_text("⚠️ ስልክ ቁጥር በትክክል 10 አሃዝ መሆን አለበት (ለምሳሌ፦ 0912345678)። እባክዎ በድጋሚ ያስገቡ፦")
        return PHONE
    context.user_data['phone'] = text
    await update.message.reply_text("ከ 1 እስከ 1000 ያለ የቲኬት ቁጥር ይምረጡ፦", reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return TICKET_NUM

async def get_ticket_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    num = update.message.text
    if num == "⬅️ ተመለስ": return PHONE
    if not num.isdigit() or not (1 <= int(num) <= 1000):
        await update.message.reply_text("እባክዎ ከ 1 እስከ 1000 ያለ ቁጥር ብቻ ያስገቡ፦")
        return TICKET_NUM
    conn = sqlite3.connect('lottery.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE ticket = ?", (num,))
    if cursor.fetchone():
        await update.message.reply_text("⚠️ ይህ ቁጥር ተይዟል! እባክዎ ሌላ ይምረጡ፦")
        conn.close()
        return TICKET_NUM
    conn.close()
    context.user_data['ticket'] = num
    await update.message.reply_text("የክፍያ ዘዴ ይምረጡ፦", reply_markup=ReplyKeyboardMarkup([["Telebirr", "CBE"], ["⬅️ ተመለስ"]], resize_keyboard=True))
    return PAYMENT_METHOD

async def payment_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return TICKET_NUM
    context.user_data['payment'] = update.message.text
    await update.message.reply_text(f"{PAYMENT_INFO.get(update.message.text, '')}\n\nክፍያውን ፈጽመው ስክሪንሾት ይላኩ፦")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        d, uid = context.user_data, update.effective_user.id
        reg_code = str(random.randint(10000, 99999))
        sale_date = (datetime.now() + timedelta(hours=3)).strftime("%d/%m/%Y")
        conn = sqlite3.connect('lottery.db')
        conn.execute("INSERT OR REPLACE INTO users (id, car, name, phone, ticket, payment, proof, status, reg_code, sale_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     (uid, d['car'], d['name'], d['phone'], d['ticket'], d['payment'], file_id, 'Pending', reg_code, sale_date))
        conn.commit()
        conn.close()
        text = f"🔔 አዲስ ጥያቄ!\n👤 ስም: {d['name']}\n📞 ስልክ: {d['phone']}\n🎫 ቁጥር: {d['ticket']}"
        kb = [[InlineKeyboardButton("✅ Approve", callback_data=f"verify_{uid}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}")]]
        await context.bot.send_photo(chat_id=OWNER_ID, photo=file_id, caption=text, reply_markup=InlineKeyboardMarkup(kb))
        await update.message.reply_text("✅ መረጃዎ ደርሶናል። አስተዳዳሪው ሲያረጋግጥ የቲኬት ፎቶ ይላክለታል።", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return SCREENSHOT

if __name__ == '__main__':
    init_db()
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CallbackQueryHandler(handle_verification))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CAR_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_chosen)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            TICKET_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ticket_num)],
            PAYMENT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_chosen)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)]
        },
        fallbacks=[CommandHandler('start', start)]
    ))
    application.run_polling()
