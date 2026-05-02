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

# --- Render keep_alive ---
app = Flask('')
@app.route('/')
def home(): return "ቦቱ በሰላም እየሰራ ነው!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

# --- Configurations ---
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

# --- 4x Larger Ticket Image ---
def create_ticket_image(name, ticket, car, phone, reg_code, sale_date):
    img = Image.new('RGB', (1600, 1100), color=(15, 15, 15)) 
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, 1560, 1060], outline=(212, 175, 55), width=30)
    
    # Text Drawing (Simulating 4x size by spacing and canvas scale)
    d.text((450, 100), "ግዛቸው የመኪና ሎተሪ", fill=(212, 175, 55)) 
    d.text((120, 300), f"👤 ስም: {name.upper()}", fill=(255, 255, 255))
    d.text((120, 420), f"🚗 መኪና: {car.upper()}", fill=(255, 255, 255))
    d.text((120, 540), f"📞 ስልክ: {phone}", fill=(255, 255, 255))
    d.text((120, 660), f"🔑 መዝገብ ቁጥር: {reg_code}", fill=(255, 255, 255))
    d.text((120, 780), f"📅 ቀን: {sale_date}", fill=(255, 255, 255))
    
    d.text((1000, 650), "TICKET NO:", fill=(212, 175, 55))
    d.text((1050, 780), f"#{ticket}", fill=(0, 255, 127)) # Digital number only
    d.text((600, 950), "መልካም እድል", fill=(212, 175, 55))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# --- Admin Broadcast (Photo & Video) ---
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ለተጠቃሚዎች የሚላክ ፎቶ ወይም ቪዲዮ ከነ ጽሁፉ ይላኩ፦")
    return ADMIN_BROADCAST

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption
    conn = sqlite3.connect('lottery.db')
    users = conn.execute("SELECT id FROM users").fetchall()
    conn.close()
    for user in users:
        try:
            if update.message.photo: await context.bot.send_photo(user[0], update.message.photo[-1].file_id, caption=caption)
            elif update.message.video: await context.bot.send_video(user[0], update.message.video.file_id, caption=caption)
        except: continue
    await update.message.reply_text("✅ ማስታወቂያው ተልኳል!")
    return ConversationHandler.END

# --- User Flow ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["Sino", "Isuzu"]] # Toyota removed
    if update.effective_user.id in ADMINS: kb.append(["📣 ማስታወቂያ ላክ"])
    await update.message.reply_text("እንኳን ወደ ግዛቸው የመኪና አቁብ በደህና መጡ\n\nእባክዎ መኪና ይምረጡ፦", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CAR_SELECTION

async def car_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📣 ማስታወቂያ ላክ": return await broadcast_start(update, context)
    context.user_data['car'] = update.message.text
    await update.message.reply_text("ሙሉ ስምዎን ያስገቡ፦", reply_markup=ReplyKeyboardRemove())
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("ስልክ ቁጥር ያስገቡ (10 አሃዝ)፦")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("ከ 1-1000 ያለ የቲኬት ቁጥር (በቁጥር ብቻ) ይምረጡ፦")
    return TICKET_NUM

async def get_ticket_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    num = update.message.text
    if not num.isdigit():
        await update.message.reply_text("⚠️ እባክዎ ቁጥር ብቻ ያስገቡ (ለምሳሌ 45)፦")
        return TICKET_NUM
    conn = sqlite3.connect('lottery.db')
    if conn.execute("SELECT id FROM users WHERE ticket=? AND status='Verified'", (num,)).fetchone():
        conn.close()
        await update.message.reply_text("❌ ይህ ቲኬት ተይዟል! ሌላ ይምረጡ፦")
        return TICKET_NUM
    conn.close()
    context.user_data['ticket'] = num
    kb = [["Telebirr", "CBE"]]
    await update.message.reply_text("የክፍያ ዘዴ ይምረጡ፦", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return PAYMENT_METHOD

async def payment_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = update.message.text
    context.user_data['payment'] = p
    await update.message.reply_text(f"{PAYMENT_INFO.get(p)}\n\nክፍያውን ፈጽመው ስክሪንሾት ይላኩ፦")
    return SCREENSHOT

async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        fid = update.message.photo[-1].file_id
        d, uid = context.user_data, update.effective_user.id
        reg, date = str(random.randint(100000, 999999)), (datetime.now() + timedelta(hours=3)).strftime("%d/%m/%Y")
        conn = sqlite3.connect('lottery.db')
        conn.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?,?,?,?)", (uid, d['car'], d['name'], d['phone'], d['ticket'], d['payment'], fid, 'Pending', reg, date))
        conn.commit()
        conn.close()
        txt = f"🔔 አዲስ ጥያቄ!\n👤 ስም: {d['name']}\n🎫 ቲኬት: {d['ticket']}"
        kb = [[InlineKeyboardButton("✅ Approve", callback_data=f"v_{uid}"), InlineKeyboardButton("❌ Reject", callback_data=f"r_{uid}")]]
        for a in ADMINS:
            try: await context.bot.send_photo(a, fid, caption=txt, reply_markup=InlineKeyboardMarkup(kb))
            except: continue
        await update.message.reply_text("✅ መረጃዎ ተልኳል! አድሚኑ ሲያጸድቅ ቲኬቱ ይላክልዎታል።", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return SCREENSHOT

async def handle_v(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    act, uid = q.data.split("_")
    uid = int(uid)
    if act == "v":
        conn = sqlite3.connect('lottery.db')
        conn.execute("UPDATE users SET status='Verified' WHERE id=?", (uid,))
        u = conn.execute("SELECT name, ticket, car, phone, reg_code, sale_date FROM users WHERE id=?", (uid,)).fetchone()
        conn.commit()
        conn.close()
        if u:
            img = create_ticket_image(*u)
            await context.bot.send_photo(uid, img, caption="🎉 መልካም እድል 🎉", reply_markup=ReplyKeyboardMarkup([["ሌላ የቁረጡ 🎫"]], resize_keyboard=True))
            await q.edit_message_caption(caption=q.message.caption + "\n\n✅ ጸድቋል!")
    else: await q.edit_message_caption(caption=q.message.caption + "\n\n❌ ተሰርዟል!")

if __name__ == '__main__':
    init_db()
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CallbackQueryHandler(handle_v))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(filters.Regex('^ሌላ የቁረጡ 🎫$'), start)],
        states={
            CAR_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_chosen)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            TICKET_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ticket_num)],
            PAYMENT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_chosen)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)],
            ADMIN_BROADCAST: [MessageHandler((filters.PHOTO | filters.VIDEO) & ~filters.COMMAND, send_broadcast)]
        },
        fallbacks=[CommandHandler('start', start)]
    ))
    application.run_polling()
