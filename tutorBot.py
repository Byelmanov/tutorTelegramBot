# pip install pyTelegramBotAPI
# pip install pymysql
import telebot
from telebot import types
import pymysql
from datetime import datetime

bot = telebot.TeleBot("928244332:AAFXeSpQSVauw_3Efi6P_oiLkdcxjz7QK-Y")
DB = pymysql.connect('localhost', 'root', '', 'unnamed')

try:
    cursor = DB.cursor()

    class DataCurrSession:
        group_id = 0
        subject_id = 0
        tutor_id = 0
        curr_student_id = 0

    data_obj = DataCurrSession()


    def wrap_cursor_execute(sql):
        global DB
        if not DB.open:
            DB = pymysql.connect('localhost', 'root', '', 'unnamed')

        row_count = cursor.execute(sql)
        if (row_count == 0):
            return None
        else:
            result = cursor.fetchall()
            return result



    def check_is_tutor_and_return_id_of_they(username):
        usernames_from_DB = wrap_cursor_execute('SELECT * FROM tutors_tg')

        if usernames_from_DB == None:
            return False
        else:
            for i in usernames_from_DB:
                if(i[1] == username):
                    return i[0]

        return False


    @bot.message_handler(commands=['help'])
    def help_handler(message):
        user_name = message.from_user.first_name
        help_message = 'Рады преветствовать вас, {}!\nДля того чтобы начать, пожалуйста,' \
                       ' введите команду /start'.format(user_name)

        bot.send_message(message.chat.id, help_message)


    @bot.message_handler(commands=['start'])
    def start_handler(message):
        username = message.from_user.username
        user_name = message.from_user.first_name

        tutor_id = check_is_tutor_and_return_id_of_they(username)

        if(tutor_id):
            bot.send_message(message.chat.id, "Добро пожаловать, {}".format(user_name))

            data_obj.tutor_id = tutor_id

            sql_to_get_groups = """
                SELECT groups.id, groups.title
                FROM tutors_tg
                INNER JOIN group_subject ON tutors_tg.user_id = group_subject.tutor_id
                INNER JOIN groups ON group_subject.group_id = groups.id
                WHERE tutors_tg.user_id = {};
            """.format(tutor_id)

            array_of_groups = wrap_cursor_execute(sql_to_get_groups)

            if (array_of_groups == None):
                bot.send_message(message.chat.id, 'У вас нет групп')
            else:
                keyboard_groups = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
                for group in array_of_groups:
                    group_button = types.KeyboardButton(group[1])
                    keyboard_groups.add(group_button)

                msg = bot.send_message(message.chat.id, 'Выберите группу:', reply_markup=keyboard_groups)
                bot.register_next_step_handler(msg, handle_group)

        else:
            bot.send_message(message.chat.id, "Извините, но вы не преподаватель. У вас нет прав"
                                              " на редактирование журнала. Вы можете только"
                                              " просматривать его на сайте www.site.com")


    def handle_group(message):

        # not sure it is a good way to use names instead of id
        sql_to_set_group_id = """
        SELECT id FROM groups
        WHERE title = '{}';
        """.format(message.text)

        group_id = wrap_cursor_execute(sql_to_set_group_id)

        # test it, I'm not sure that it must work - [0][0]
        data_obj.group_id = group_id[0][0]

        sql_to_get_subjects = """
        SELECT title, type FROM subjects
        INNER JOIN group_subject ON subjects.id = group_subject.subject_id
        WHERE group_subject.group_id = {} AND group_subject.tutor_id = {};
        """.format(group_id[0], data_obj.tutor_id)

        array_of_subjects = wrap_cursor_execute(sql_to_get_subjects)

        if (array_of_subjects == None):
            bot.send_message(message.chat.id, 'У этой группы пока нет предметов')
        else:
            keyboard_subjects = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
            for subject in array_of_subjects:
                subject_button = types.KeyboardButton('{} ({})'.format(subject[0], subject[1]))
                keyboard_subjects.add(subject_button)

            msg = bot.send_message(message.chat.id, 'Выберите предмет:', reply_markup=keyboard_subjects)
            bot.register_next_step_handler(msg, handle_subject)


    def handle_subject(message):
        sql_to_get_subject_id = """
        SELECT id FROM subjects
        WHERE CONCAT(title, ' (', type, ')') = '{}';
        """.format(message.text)

        subject_id = wrap_cursor_execute(sql_to_get_subject_id)

        data_obj.subject_id = subject_id[0][0]

        sql_to_get_students = """
        SELECT id, lastname, firstname FROM students
        WHERE group_id = {};
        """.format(data_obj.group_id)

        array_of_students = wrap_cursor_execute(sql_to_get_students)

        if (array_of_students == None):
            bot.send_message(message.chat.id, 'В этой группе пока нет студентов')
        else:
            def launch_students(message, i):

                def handle_one_student(message, i, length):

                    answer = True if (message.text == 'Есть') else False

                    current_data_string = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

                    sql_to_insert_to_journal = """
                    INSERT INTO journals (student_id, subject_id, value, created_at, updated_at)
                    VALUES ({}, {}, {}, '{}', '{}')
                    """.format(data_obj.curr_student_id, data_obj.subject_id, answer,
                               current_data_string, current_data_string)

                    try:
                        global DB
                        if not DB.open():
                            DB = pymysql.connect('localhost', 'root', '', 'unnamed')

                        cursor.execute(sql_to_insert_to_journal)
                        DB.commit()
                    except:
                        DB.rollback()

                    if(i < length - 1):
                        i += 1
                        launch_students(message, i)


                length_of_array_students = len(array_of_students)

                one_time_keyboard = False if (i < length_of_array_students - 1) else True

                keyboard_student = types.ReplyKeyboardMarkup(row_width=2,
                                                             one_time_keyboard=one_time_keyboard)
                btn_is = types.KeyboardButton('Есть')
                btn_absent = types.KeyboardButton('Нет')
                keyboard_student.row(btn_is, btn_absent)
                msg = bot.send_message(message.chat.id,
                                       array_of_students[i][1]+' '+array_of_students[i][2],
                                       reply_markup=keyboard_student)
                data_obj.curr_student_id = array_of_students[i][0]

                bot.register_next_step_handler(msg, handle_one_student, i, length_of_array_students)

            launch_students(message, 0)

except:
    print('Error')

finally:
    bot.polling()
    DB.close()


