# pip install pyTelegramBotAPI
import telebot
from telebot import types

bot = telebot.TeleBot("928244332:AAFXeSpQSVauw_3Efi6P_oiLkdcxjz7QK-Y")

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Hello, you wrote me /start')

@bot.message_handler(content_types=['text'])
def text_message(message):

    if message.text == "1":
        bot.send_message(message.chat.id, 'You chose 1')
    elif message.text == "2":
        bot.send_message(message.chat.id, 'You chose 2')


bot.polling()


