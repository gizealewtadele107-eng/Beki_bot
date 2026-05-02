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

# --- Render Server ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Running!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

# --- Config ---
TOKEN = "8667033966:AAF_rL_vAKyNC9vtOf2mo3d8Zb-zJ5RdEAw"
ADMINS = [7705713321, 7868124597]
CAR, F_NAME, L_NAME, PHONE, TICKET, PAYMENT, SCREENSHOT = range(7)

CAR_DATA = {
    "Sino": "2,500,000 ETB",
    "Isuzu": "1,800,000 ETB"
}
PAYMENT_INFO = {"Telebirr": "ቁጥር: 0954873497", "CBE": "አካውንት: 1000536009276"}

def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, car TEXT, name TEXT, phone TEXT, ticket TEXT, payment TEXT, proof TEXT, status TEXT, reg_code TEXT, sale_date TEXT)''')
    conn.commit()
    conn.close()

# --- Extra Large Ticket Design ---
def create_ticket_image(name, ticket, car, phone, reg_code, sale_date):
    img = Image.new('RGB', (1800, 1200), color=(10, 10, 10))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, 1760, 1160], outline=(212, 175, 55), width=40)
    
    # Very Large Text Simulation
    d.text((500, 80), "ግዛቸው የመኪና እቁብ", fill=(212, 175, 55))
    d.text((120, 300), f"ስም: {name.upper()}", fill=(255, 255, 255))
    d.text((120, 450), f"መኪና: {car.upper()}", fill=(255, 255, 255))
    d.text((120, 600), f"ስልክ: {phone}", fill=(255, 255, 255))
    d.text((120, 750), f"መዝገብ ቁጥር: {reg_code}", fill=(255, 255, 255))
    d.text((120, 900), f"ቀን: {sale_date}", fill=(255, 255, 255))
    
    d.text((1100, 600), "TICKET NO:", fill=(212, 175, 55))
    d.text((1150, 750), f"#{ticket}", fill=(0, 255, 127))
    d.text((700, 1050), "መልካም እድል", fill=(212, 175, 55))

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["Sino", "Isuzu"]]
    if update.effective_user.id in ADMINS: kb.append(["📢 ማስታወቂያ"])
    await update.message.reply_text("እንኳን ወደ ግዛቸው የመኪና እቁብ በደህና መጡ\n\nእባክዎ መኪና ይምረጡ፦", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CAR

async def car_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice == "📢 ማስታወቂያ": return ConversationHandler.END # Admin functionality simplified
    context.user_data['car'] = choice
    price = CAR_DATA.get(choice, "ያልታወቀ")
    await update.message.reply_text(f"የመረጡት መኪና: {choice}\nዋጋ: {price}\n\nአሁን የእርስዎን የመጀመሪያ ስም ያስገቡ፦", 
                                   reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return F_NAME

async def get_f_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return await start(update, context)
    context.user_data['f_name'] = update.message.text
    await update.message.reply_text("የአባት ስም ያስገቡ፦")
    return L_NAME

async def get_l_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": 
        await update.message.reply_text("የመጀመሪያ ስምዎን ያስገቡ፦")
        return F_NAME
    context.user_data['l_name'] = update.message.text
    await update.message.reply_text("የኢትዮጵያ ስልክ ቁጥርዎን ያስገቡ (ለምሳሌ፦ +2519...)፦")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ":
        await update.message.reply_text("የአባት ስምዎን ያስገቡ፦")
        return L_NAME
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("ከ 1-1000 ያለ የቲኬት ቁጥር በቁጥር ብቻ ይምረጡ፦")
    return TICKET

async def get_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ":
        await update.message.reply_text("ስልክ ቁጥርዎን ያስገቡ፦")
        return PHONE
    num = update.message.text
    if not num.isdigit():
        await update.message.reply_text("⚠️ እባክዎ ቁጥር ብቻ ያስገቡ (ምሳሌ: 50)፦")
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
        
        # Notify Admin
        admin_txt = f"🔔 አዲስ ጥያቄ!\n👤 {full_name}\n🚗 {d['car']}\n🎫 ቲኬት {d['ticket']}"
        kb = [[InlineKeyboardButton("✅ አጽድቅ", callback_data=f"v_{uid}"), InlineKeyboardButton("❌ ሰርዝ", callback_data=f"r_{uid}")]]
        for a in ADMINS: await context.bot.send_photo(a, fid, caption=admin_txt, reply_markup=InlineKeyboardMarkup(kb))
        
        await update.message.reply_text("እጣዎ በሚገባ ተመዝግቧል! አድሚኑ ሲያጸድቅ ቲኬቱ ይላክልዎታል።", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return SCREENSHOT

async def handle_v(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    act, uid = q.data.split("_")
    if act == "v":
        conn = sqlite3.connect('lottery.db')
        u = conn.execute("SELECT name, ticket, car, phone, reg_code, sale_date FROM users WHERE id=?", (uid,)).fetchone()
        conn.commit()
        conn.close()
        if u:
            img = create_ticket_image(*u)
            await context.bot.send_photo(uid, img, caption="🎉 እንኳን ደስ አለዎት! ቲኬትዎ ይኸውና።")
            await q.edit_message_caption("✅ ጸድቋል!")

if __name__ == '__main__':
    init_db()
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CallbackQueryHandler(handle_v))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(filters.Regex('^ሌላ የቁረጡ 🎫$'), start)],
        states={
            CAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, car_chosen)],
            F_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_f_name)],
            L_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_l_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            TICKET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ticket)],
            PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, get_screenshot)]
        },
        fallbacks=[CommandHandler('start', start)]
    ))
    application.run_polling()
