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

# --- Render Keep-Alive Server ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

# --- Config ---
TOKEN = "8667033966:AAF_rL_vAKyNC9vtOf2mo3d8Zb-zJ5RdEAw"
ADMINS = [7705713321, 7868124597] 
CAR, F_NAME, L_NAME, PHONE, TICKET, PAYMENT, SCREENSHOT, BROADCAST = range(8)

CAR_DATA = {"Sino": "3000 BIRR", "Isuzu": "2000 BIRR"}
PAYMENT_INFO = {"Telebirr": "ቁጥር: 0954873497", "CBE": "አካውንት: 1000536009276"}

def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, car TEXT, name TEXT, phone TEXT, ticket TEXT, payment TEXT, proof TEXT, status TEXT, reg_code TEXT, sale_date TEXT)''')
    conn.commit()
    conn.close()

# --- Extra Large Ticket Image Generator ---
def create_ticket_image(name, ticket, car, phone, reg_code, sale_date):
    img = Image.new('RGB', (2000, 1400), color=(10, 10, 10))
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, 1950, 1350], outline=(212, 175, 55), width=50) # ወርቃማ ክፈፍ
    
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

# --- Admin Broadcast Handlers ---
async def admin_broadcast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ለተጠቃሚዎች የሚላክ ጽሁፍ፣ ፎቶ ወይም ቪዲዮ ይላኩ (ለመሰረዝ /start ይበሉ)፦")
    return BROADCAST

async def perform_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('lottery.db')
    users = conn.execute("SELECT id FROM users").fetchall()
    conn.close()
    for user in users:
        try:
            if update.message.text: await context.bot.send_message(user[0], update.message.text)
            elif update.message.photo: await context.bot.send_photo(user[0], update.message.photo[-1].file_id, caption=update.message.caption)
            elif update.message.video: await context.bot.send_video(user[0], update.message.video.file_id, caption=update.message.caption)
        except: continue
    await update.message.reply_text("✅ ማስታወቂያው ለሁሉም ተጠቃሚዎች ተልኳል!")
    return ConversationHandler.END

# --- User Registration Flow ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["Sino", "Isuzu"]]
    if update.effective_user.id in ADMINS: kb.append(["📢 ማስታወቂያ ላክ"])
    await update.message.reply_text("እንኳን ወደ ግዛቸው የመኪና እቁብ በደህና መጡ\n\nእባክዎ መኪና ይምረጡ፦", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return CAR

async def car_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice == "📢 ማስታወቂያ ላክ": return await admin_broadcast_menu(update, context)
    context.user_data['car'] = choice
    await update.message.reply_text(f"የመረጡት መኪና: {choice}\nዋጋ: {CAR_DATA[choice]}\n\nአሁን የመጀመሪያ ስምዎን ያስገቡ፦", 
                                   reply_markup=ReplyKeyboardMarkup([["⬅️ ተመለስ"]], resize_keyboard=True))
    return F_NAME

async def f_name_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "⬅️ ተመለስ": return await start(update, context)
    context.user_data['f_name'] = update.message.text
    await update.message
