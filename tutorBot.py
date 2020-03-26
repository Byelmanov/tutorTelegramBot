# pip install pyTelegramBotAPI
# pip install pymysql
import telebot
from telebot import types
import pymysql

bot = telebot.TeleBot("928244332:AAFXeSpQSVauw_3Efi6P_oiLkdcxjz7QK-Y")

# TODO last parameter is db name
DB = pymysql.connect('localhost', 'root', 'hr220400', 'telegramBot')
cursor = DB.cursor()


class DataCurrSession:
    group_id = 0
    subject_id = 0
    tutor_id = 0
    curr_student_id = 0

data_obj = DataCurrSession()


def check_is_tutor_and_return_id_of_they(username):
    # TODO add somewhere a field with tutors telegram's usernames and check SQL
    cursor.execute('SELECT * FROM tutors')
    usernames_from_DB = cursor.fetchall()

    for i in usernames_from_DB:
        if(i[1] == username):
            return i[0]

    return False


@bot.message_handler(commands=['help'])
def help_handler(message):
    user_name = message.from_user.first_name
    help_message = 'Рады преветствовать вас, {}!\n Для того чтобы начать, пожалуйста,' \
                   'введите команду /start'.format(user_name)

    bot.send_message(message.chat.id, help_message)


@bot.message_handler(commands=['start'])
def start_handler(message):
    username = message.from_user.username
    user_name = message.from_user.first_name

    tutor_id = check_is_tutor_and_return_id_of_they(username)

    if(tutor_id):
        bot.send_message(message.chat.id, "Добро пожаловать, {}".format(user_name))

        data_obj.tutor_id = tutor_id

        # TODO check sql
        sql_to_get_groups = """
            SELECT `groups`.name, `groups`.id
            FROM tutor_group
            LEFT JOIN `tutors` ON tutor_group.tutor_id = `tutors`.id
            LEFT JOIN `groups` ON tutor_group.group_id = `groups`.id
            WHERE tutor_group.tutor_id = {};
        """.format(tutor_id)

        cursor.execute(sql_to_get_groups)
        array_of_groups = cursor.fetchall()

        keyboard_groups = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
        for group in array_of_groups:
            group_button = types.KeyboardButton(group[0])
            keyboard_groups.add(group_button)

        msg = bot.send_message(message.chat.id, 'Выберите группу:', reply_markup=keyboard_groups)
        bot.register_next_step_handler(msg, handle_group)

    else:
        bot.send_message(message.chat.id, "Извините, но вы не преподователь. У вас нет прав"
                                          "на редактирование журнала. Вы можете только"
                                          " просматривать его на сайте www.site.com")


def handle_group(message):

    # TODO check sql
    sql_to_set_group_id = """
    SELECT id FROM telegramBot.groups
    WHERE name = '{}';
    """.format(message.text)

    cursor.execute(sql_to_set_group_id)

    group_id = cursor.fetchone()
    data_obj.group_id = group_id[0]

    # TODO need to get only subjects of chosen group with that tutor, but I get all subjects
    sql_to_get_subjects = """
    SELECT * FROM subjects;
    """
    cursor.execute(sql_to_get_subjects)

    array_of_subjects = cursor.fetchall()

    keyboard_subjects = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
    for subject in array_of_subjects:
        subject_button = types.KeyboardButton(subject[1])
        keyboard_subjects.add(subject_button)

    msg = bot.send_message(message.chat.id, 'Выберите предмет:', reply_markup=keyboard_subjects)
    bot.register_next_step_handler(msg, handle_subject)


def handle_subject(message):
    # TODO check sql
    sql_to_get_subject_id = """
    SELECT id FROM telegramBot.subjects
    WHERE name = '{}';
    """.format(message.text)
    cursor.execute(sql_to_get_subject_id)
    subject_id = cursor.fetchone()
    data_obj.subject_id = subject_id[0]

    # TODO need to add WHERE group_id and subject_id
    sql_to_get_students = """
    SELECT * FROM telegramBot.students;
    """
    cursor.execute(sql_to_get_students)
    array_of_students = cursor.fetchall()


    def launch_students(message, i):

        def handle_one_student(message, i, length):

            answer = True if (message.text == 'Есть') else False

            # TODO check SQL
            sql_to_insert_to_journal = """
            INSERT INTO journals (student_id, subject_id, value, created_at, updated_at)
            VALUES
            ({}, {}, {}, '0000-00-00 00:00:00', '0000-00-00 00:00:00')
            """.format(data_obj.curr_student_id, data_obj.subject_id, answer)

            try:
                cursor.execute(sql_to_insert_to_journal)
                DB.commit()
            except:
                DB.rollback()

            if(i < length - 1):
                i += 1
                launch_students(message, i)


        length_of_array_students = len(array_of_students)

        one_time_keyboard = False if (i < length_of_array_students - 1) else True

        keyboard_student = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=one_time_keyboard)
        btn_is = types.KeyboardButton('Есть')
        btn_absent = types.KeyboardButton('Нет')
        keyboard_student.row(btn_is, btn_absent)
        msg = bot.send_message(message.chat.id, array_of_students[i][1], reply_markup=keyboard_student)
        data_obj.curr_student_id = array_of_students[i][0]

        bot.register_next_step_handler(msg, handle_one_student, i, length_of_array_students)

    launch_students(message, 0)



bot.polling()
DB.close()


