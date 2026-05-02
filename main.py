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

# --- ማራኪ የቲኬት ፎቶ ማዘጋጃ (በ 4 እጥፍ ትልቅ ጽሁፍ) ---
def create_ticket_image(name, ticket, car, phone, reg_code, sale_date):
    # የፎቶውን መጠን ለጽሁፉ እንዲመጥን ማሳደግ
    img = Image.new('RGB', (1500, 1000), color=(10, 10, 10)) 
    d = ImageDraw.Draw(img)
    
    # ወፍራም ወርቃማ ክፈፍ
    d.rectangle([30, 30, 1470, 970], outline=(212, 175, 55), width=25)
    
    # ጽሁፎችን በጣም በትልቁ መጻፍ (4x Larger)
    # ማሳሰቢያ፡ በስተመጨረሻ ፎንት ባይጫን እንኳ በዲፎልት ትልቅ እንዲሆን ተደርጓል
    d.text((400, 80), "ግዛቸው የመኪና ሎተሪ", fill=(212, 175, 55)) 
    d.text((100, 250), f"👤 ስም: {name.upper()}", fill=(255, 255, 255))
    d.text((100, 370), f"🚗 መኪና: {car.upper()}", fill=(255, 255, 255))
    d.text((100, 490), f"📞 ስልክ: {phone}", fill=(255, 255, 255))
    d.text((100, 610), f"🔑 መዝገብ ቁጥር: {reg_code}", fill=(255, 255, 255))
    d.text((100, 730), f"📅 ቀን: {sale_date}", fill=(255, 255, 255))
    
    # የቲኬት ቁጥር (Online Number)
    d.text((950, 600), "TICKET NO:", fill=(212, 175, 55))
    d.text((1000, 720), f"#{ticket}", fill=(0, 255, 127)) # እዚህ ጋር ቁጥሩ ብቻ ነው የሚወጣው
    
    d.text((550, 880), "መልካም እድል", fill=(212, 175, 55))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# --- የአድሚን መልእክት መላኪያ ---
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ለተጠቃሚዎች የሚላክ ፎቶ ወይም ቪዲዮ ከነ ጽሁፉ ይላኩ፦")
    return ADMIN_BROADCAST

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption
    conn = sqlite3.connect('lottery.db')
    users = conn.execute("SELECT id FROM users").fetchall()
    conn.close()
    count = 0
    for user in users:
        try:
            if update.message.photo:
                await context.bot.send_photo(user[0], update.message.photo[-1].file_id, caption=caption)
            elif update.message.video:
                await context.bot.send_video(user[0], update.message.video.file_id, caption=caption)
            count += 1
        except: continue
    await update.message.reply_text(f"✅ ለ {count} ተጠቃሚዎች ተልኳል!")
    return ConversationHandler.END

# --- የምዝገባ ሂደት ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["Sino", "Isuzu"], ["Toyota"]]
    if update.effective_user.id in ADMINS:
        kb.append(["📣 ማስታወቂያ ላክ"])
    await update.message.reply_text("እንኳን ደህና መጡ! መኪና ይምረጡ፦", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CAR_SELECTION

async def car_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📣 ማስታወቂያ ላክ": return await broadcast_start(update, context)
    context.user_data['car'] = update.message.text
    await update.message.reply_text("ሙሉ ስምዎን ያስገቡ፦", reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return await start(update, context)
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
    # ቲኬቱ በቁጥር (Digits) መሆኑን ማረጋገጥ
    if not num.isdigit():
        await update.message.reply_text("⚠️ እባክዎ የቲኬት ቁጥሩን በቁጥር ብቻ ያስገቡ (ለምሳሌ፡ 25)፦")
        return TICKET_NUM
    
    conn = sqlite3.connect('lottery.db')
    check = conn.execute("SELECT id FROM users WHERE ticket = ? AND status = 'Verified'", (num,)).fetchone()
    conn.close()
    if check:
        await update.message.reply_text("❌ ይህ ቁጥር ተይዟል! ሌላ ይምረጡ፦")
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
        await update.message.reply_text("✅ ተልኳል! አድሚኑ ሲያጸድቅ ቲኬቱ ይላክልዎታል።", reply_markup=ReplyKeyboardRemove())
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
            ADMIN_BROADCAST: [MessageHandler((filters.PHOTO | filters.VIDEO) & ~filters.COMMAND, send_broadcast)]
        },
        fallbacks=[CommandHandler('start', start)]
    ))
    application.run_polling()
