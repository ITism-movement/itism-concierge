import os

import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# Replace 'YOUR_BOT_TOKEN' with your Telegram Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Google Sheets setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credentials.json"  # Path to the JSON file
SHEET_NAME = "lightning_talks"  # Name of your Google Sheet

# Initialize Google Sheets client
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
gc = gspread.authorize(credentials)
sheet = gc.open(SHEET_NAME).sheet1  # Open the first sheet

# Initialize the bot
bot = telebot.TeleBot(BOT_TOKEN)

# State management
user_data = {}


# Start command handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Send a welcome message and show the registration button
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = telebot.types.KeyboardButton("Register for Lightning Talks")
    markup.add(button)
    bot.send_message(message.chat.id, "Welcome to the Lightning Talks registration bot! Click below to register.",
                     reply_markup=markup)


# Registration button handler
@bot.message_handler(func=lambda message: message.text == "Register for Lightning Talks")
def start_registration(message):
    # Hide the button by sending a new message with no button
    markup = telebot.types.ReplyKeyboardRemove()  # Remove the keyboard
    bot.send_message(message.chat.id, "Great! What's your name?", reply_markup=markup)

    # Start the registration process
    user_data[message.chat.id] = {}
    bot.register_next_step_handler(message, get_name)


# Step 1: Get the user's name
def get_name(message):
    user_data[message.chat.id]['name'] = message.text
    bot.send_message(message.chat.id, "What is the topic of your talk?")
    bot.register_next_step_handler(message, get_topic)


# Step 2: Get the topic of the talk
def get_topic(message):
    user_data[message.chat.id]['topic'] = message.text
    name = user_data[message.chat.id]['name']
    topic = user_data[message.chat.id]['topic']

    # Ask the user to confirm their registration
    confirmation_message = f"Please confirm your registration:\nName: {name}\nTopic: {topic}"
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    confirm_button = telebot.types.KeyboardButton("Confirm")
    cancel_button = telebot.types.KeyboardButton("Cancel")
    markup.add(confirm_button, cancel_button)
    bot.send_message(message.chat.id, confirmation_message, reply_markup=markup)


# Step 3: Confirm or Cancel registration
@bot.message_handler(func=lambda message: message.text in ["Confirm", "Cancel"])
def confirm_or_cancel(message):
    if message.text == "Confirm":
        name = user_data[message.chat.id]['name']
        topic = user_data[message.chat.id]['topic']

        # Write data to Google Sheets
        sheet.append_row([name, topic])

        # Send success message
        bot.send_message(message.chat.id,
                         f"Registration successful! Your talk: '{topic}' by {name} has been registered.")
    else:
        # Cancel registration
        bot.send_message(message.chat.id, "Registration cancelled. You can register again anytime.")

    # Remove the keyboard after the confirmation/cancellation
    markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Goodbye!", reply_markup=markup)


# Start polling
bot.polling()