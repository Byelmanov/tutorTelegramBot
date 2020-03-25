# pip install pyTelegramBotAPI
# pip install pymysql
import telebot
from telebot import types
import pymysql

bot = telebot.TeleBot("928244332:AAFXeSpQSVauw_3Efi6P_oiLkdcxjz7QK-Y")

# last parameter is db name
DB = pymysql.connect('localhost', 'root', 'hr220400', 'telegramBot')
# чтобы использовать методы курсора например cursor.execute('command')
cursor = DB.cursor()


def check_is_tutor_and_return_id_of_they(username):
    cursor.execute('SELECT * FROM tutors')
    usernames_from_DB = cursor.fetchall()

    for i in usernames_from_DB:
        if(i[1] == username):
            return i[0]

    return False


def main_process(message, tutor_id):


    # get all groups of that tutor and display it

    sql_to_get_subjects = """ SELECT `groups`.name, `groups`.id
                            FROM tutor_group
                        LEFT JOIN `tutors` ON tutor_group.tutor_id = `tutors`.id
                        LEFT JOIN `groups` ON tutor_group.group_id = `groups`.id
                        WHERE tutor_group.tutor_id = {};
                            
    """.format(tutor_id)

    cursor.execute(sql_to_get_subjects)
    array_of_subjects = cursor.fetchall()

    bot.send_message(message.chat.id, array_of_subjects);

    # get all subjects of that tutor and that group and display it


    # loop for students of chosen group

    bot.send_message(message.chat.id, tutor_id)


@bot.message_handler(commands=['help'])
def help_handler(message):
    user_name = message.from_user.first_name
    help_message = 'Рады преветствовать вас, {}!\n Для того чтобы начать, пожалуйста,' \
                   ' введите команду /start'.format(user_name)

    bot.send_message(message.chat.id, help_message)


@bot.message_handler(commands=['start'])
def start_handler(message):
    username = message.from_user.username
    user_name = message.from_user.first_name

    tutor_id = check_is_tutor_and_return_id_of_they(username)

    if(tutor_id):
        bot.send_message(message.chat.id, "Добро пожаловать, {}".format(user_name))
        main_process(message, tutor_id)
    else:
        bot.send_message(message.chat.id, "Извините, но вы не преподователь. У вас нет прав"
                                          "на редактирование журнала. Вы можете только"
                                          " просматривать его на сайте www.site.com")


@bot.message_handler(content_types=['text'])
def text_message(message):

    if message.text == "1":
        bot.send_message(message.chat.id, 'You chose 1')
    elif message.text == "2":
        bot.send_message(message.chat.id, 'You chose 2')


bot.polling()
DB.close()


