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
ADMINS = [7705713321, 7868124597] # አዲሱ አድሚን እዚህ ተጨምሯል
CAR_SELECTION, NAME, PHONE, TICKET_NUM, PAYMENT_METHOD, SCREENSHOT = range(6)
ADMIN_MSG_TEXT, ADMIN_MSG_PHOTO = range(10, 12)

PAYMENT_INFO = {"Telebirr": "ቁጥር: 0954873497", "CBE": "አካውንት: 1000536009276"}

def init_db():
    conn = sqlite3.connect('lottery.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, car TEXT, name TEXT, phone TEXT, ticket TEXT, payment TEXT, proof TEXT, status TEXT, reg_code TEXT, sale_date TEXT)''')
    conn.commit()
    conn.close()

# --- ማራኪ የቲኬት ፎቶ ማዘጋጃ ---
def create_ticket_image(name, ticket, car, phone, reg_code, sale
