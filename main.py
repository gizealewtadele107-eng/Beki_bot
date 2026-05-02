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

# --- ዋና ቅንብሮች ---
TOKEN = "8667033966:AAF_rL_vAKyNC9vtOf2mo3d8Zb-zJ5RdEAw"
OWNER_ID = 7705713321
CAR_SELECTION, NAME, PHONE, TICKET_NUM, PAYMENT_METHOD, SCREENSHOT = range(6)
ADMIN_MSG_TEXT, ADMIN_MSG_PHOTO, ADMIN_MSG_VIDEO = range(10, 13)

CAR_PRICES = {"Sino": "2500 ETB", "Isuzu": "1800 ETB"} # የመኪና ዋጋዎች
PAYMENT_INFO = {"Telebirr": "ቁጥር: 0954873497", "CBE": "አካውንት: 1000536009276"}

def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, car TEXT, name TEXT, phone TEXT, ticket TEXT, payment TEXT, proof TEXT, status TEXT, reg_code TEXT, sale_date TEXT)''')
    conn.commit()
    conn.close()

# --- በትልልቅ ፊደላት የቲኬት ፎቶ ማዘጋጃ ---
def create_ticket_image(name, ticket, car, phone, reg_code, sale_date):
    img = Image.new('RGB', (800, 550), color=(15, 15, 15))
    d = ImageDraw.Draw(img)
    # የጌጥ ክፈፍ
    d.rectangle([20, 20, 780, 530], outline=(212, 175, 55), width=8)
    
    # ጽሁፎችን በጣም በትልቁ መጻፍ (እንደፈለጉት)
    d.text((220, 40), "ግዛቸው የመኪና ሎተሪ", fill=(212, 175, 55))
    d.text((60, 120), f"ስም (NAME): {name.upper()}", fill=(255, 255, 255))
    d.text((60, 190), f"መኪና (CAR): {car.upper()}", fill=(255, 255, 255))
    d.text((60, 260), f"ስልክ (PHONE): {phone}", fill=(255, 255, 255))
    d.text((60, 330), f"መዝገብ ቁጥር: {reg_code}", fill=(255, 255, 255))
    d.text((60, 400), f"ቀን (DATE): {sale_date}", fill=(255, 255, 255))
    
    d.text((500, 310), "TICKET NO:", fill=(212, 175, 55))
    d.text((530, 360), f"#{ticket}", fill=(0, 255, 127))
    d.text((350, 480), "መልካም እድል", fill=(212, 175, 55))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# --- የአድሚን ተግባራት (ማስታወቂያ መላኪያ) ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["📣 ጽሁፍ ላክ", "🖼️ ፎቶ ላክ"], ["📹 ቪዲዮ ላክ"]]
    await update.message.reply_text("አድሚን ፓነል:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_admin_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📣 ጽሁፍ ላክ":
        await update.message.reply_text("ጽሁፉን ያስገቡ:")
        return ADMIN_MSG_TEXT
    elif update.message.text == "🖼️ ፎቶ ላክ":
        await update.message.reply_text("ፎቶውን ይላኩ:")
        return ADMIN_MSG_PHOTO
    elif update.message.text == "📹 ቪዲዮ ላክ":
        await update.message.reply_text("ቪዲዮውን ይላኩ:")
        return ADMIN_MSG_VIDEO

async def broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    conn = sqlite3.connect('lottery.db')
    users = conn.execute("SELECT id FROM users").fetchall()
    conn.close()
    for user in users:
        try: await context.bot.send_message(user[0], text)
        except: continue
    await update.message.reply_text("ተልኳል!")
    return ConversationHandler.END

async def broadcast_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1].file_id
    conn = sqlite3.connect('lottery.db')
    users = conn.execute("SELECT id FROM users").fetchall()
    conn.close()
    for user in users:
        try: await context.bot.send_photo(user[0], photo)
        except: continue
    await update.message.reply_text("ተልኳል!")
    return ConversationHandler.END

async def broadcast_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video.file_id
    conn = sqlite3.connect('lottery.db')
    users = conn.execute("SELECT id FROM users").fetchall()
    conn.close()
    for user in users:
        try: await context.bot.send_video(user[0], video)
        except: continue
    await update.message.reply_text("ተልኳል!")
    return ConversationHandler.END

# --- የተጠቃሚ ምዝገባ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    if update.effective_user.id == OWNER_ID:
        await admin_panel(update, context)
        return
    
    kb = [["Sino", "Isuzu"], ["❓ ጥያቄ ለመጠየቅ"]]
    await update.message.reply_text("እንኳን ደህና መጡ! መኪና ይምረጡ፦", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CAR_SELECTION

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("እባክዎ ጥያቄዎን በጽሁፍ ያስገቡ። አስተዳዳሪው ይመልስልዎታል።", reply_markup=ReplyKeyboardRemove())
    return

async def car_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    car = update.message.text
    if car == "❓ ጥያቄ ለመጠየቅ": return await ask_question(update, context)
    context.user_data['car'] = car
    await update.message.reply_text("ሙሉ ስምዎን ያስገቡ፦", reply_markup=ReplyKeyboardRemove())
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("ስልክ ቁጥርዎን ያስገቡ፦")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("ከ 1 እስከ 1000 ያለ የቲኬት ቁጥር ይምረጡ፦")
    return TICKET_NUM

async def get_ticket_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ticket'] = update.message.text
    kb = [["Telebirr", "CBE"]]
    await update.message.reply_text("የክፍያ ዘዴ ይምረጡ፦", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return PAYMENT_METHOD

async def payment_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p_method = update.message.text
    context.user_data['payment'] = p_method
    car = context.user_data['car']
    price = CAR_PRICES.get(car, "Unknown")
    await update.message.reply_text(f"የመረጡት መኪና: {car}\nዋጋ: {price}\n{PAYMENT_INFO.get(p_method)}\n\nክፍያውን ፈጽመው ስክሪንሾት ይላኩ፦")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        d, uid = context.user_data, update.effective_user.id
        
        # የዘፈቀደ የመዝገብ ቁጥር እና ቀን
        reg_code = str(random.randint(100000, 999999))
        sale_date = (datetime.now() + timedelta(hours=3)).strftime("%d/%m/%Y")
        
        conn = sqlite3.connect('lottery.db')
        conn.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?,?,?,?)", (uid, d['car'], d['name'], d['phone'], d['ticket'], d['payment'], file_id, 'Pending', reg_code, sale_date))
        conn.commit()
        conn.close()
        
        # ለአድሚን መላክ (የመኪና ዓይነት ተጨምሯል)
        price = CAR_PRICES.get(d['car'], "Unknown")
        text = f"🔔 አዲስ ጥያቄ!\n👤 {d['name']}\n📞 {d['phone']}\n🚗 መኪና: {d['car']} ({price})\n🎫 ቲኬት: {d['ticket']}"
        kb = [[InlineKeyboardButton("✅ Approve", callback_data=f"verify_{uid}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}")]]
        await context.bot.send_photo(chat_id=OWNER_ID, photo=file_id, caption=text, reply_markup=InlineKeyboardMarkup(kb))
        
        await update.message.reply_text("✅ መረጃዎ ደርሶናል። አስተዳዳሪው ሲያረጋግጥ የቲኬት ፎቶ ይላክለታል።", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return SCREENSHOT

# --- ባለቤት ማረጋገጫ ---
async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, user_id = query.data.split("_")
    user_id = int(user_id)

    if action == "verify":
        conn = sqlite3.connect('lottery.db')
        u = conn.execute("SELECT name, ticket, car, phone, reg_code, sale_date FROM users WHERE id = ?", (user_id,)).fetchone()
        if u:
            # ፎቶውን መፍጠር
            img = create_ticket_image(u[0], u[1], u[2], u[3], u[4], u[5])
            await context.bot.send_photo(chat_id=user_id, photo=img, caption="✅ ክፍያዎ ተረጋግጧል! የእርስዎ ቲኬት ይኸውና።")
            conn.execute("UPDATE users SET status = 'Verified' WHERE id = ?", (user_id,))
            conn.commit()
            await query.edit_message_caption(caption=query.message.caption + "\n\n✅ ጸድቋል!")
        conn.close()
    else: await query.edit_message_caption(caption=query.message.caption + "\n\n❌ ተሰርዟል!")

if __name__ == '__main__':
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
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
            # አድሚን ግዛት
            ADMIN_MSG_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_text)],
            ADMIN_MSG_PHOTO: [MessageHandler(filters.PHOTO, broadcast_photo)],
            ADMIN_MSG_VIDEO: [MessageHandler(filters.VIDEO, broadcast_video)]
        },
        fallbacks=[CommandHandler('start', start), MessageHandler(filters.Regex('^📣 ማስታወቂያ$'), admin_panel)]
    ))
    application.run_polling()
