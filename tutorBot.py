# pip install pyTelegramBotAPI
# pip install pymysql

# main library for bot
import telebot
# it's a keyboard
from telebot import types
# library for DB connection
import pymysql
from datetime import datetime
# to show description of errors in except block
import traceback

# create a bot using our token
bot = telebot.TeleBot("928244332:AAFXeSpQSVauw_3Efi6P_oiLkdcxjz7QK-Y")
# connect to DB
DB = pymysql.connect('localhost', 'root', '', 'unnamed')

# all code in try-except because if error we need bot to continue running
try:
    # cursor to execute sql queries
    cursor = DB.cursor()

    # to store information about current user instead of using global variables
    class DataCurrSession:
        group_id = 0
        subject_id = 0
        tutor_id = 0
        curr_student_id = 0
        column_id = 0

    # object of this class
    data_obj = DataCurrSession()


    def wrap_cursor_execute(sql):
        """
        wrap function to check if DB connection is open
        if open: okay, execute sql query
        else : open and execute query
        :param sql:
        :return: DB collection with data if data
                                        else None
        """
        global DB
        global cursor
        if not DB.open:
            DB = pymysql.connect('localhost', 'root', '', 'unnamed')
            cursor = DB.cursor()


        row_count = cursor.execute(sql)
        if (row_count == 0):
            return None
        else:
            result = cursor.fetchall()
            return result



    def check_is_tutor_and_return_id_of_they(username):
        """
        when user write /start command this function checks if they are tutor or not
        :param username: current username who wrote /start
        :return: false if current user not tutor
                tutor telegram login if tutor exist
        """
        usernames_from_DB = wrap_cursor_execute('SELECT user_id, telegram FROM tutors')

        if usernames_from_DB == None:
            return False
        else:
            for i in usernames_from_DB:
                if(i[1] == username):
                    return i[0]

        return False


    # handler for /help command
    @bot.message_handler(commands=['help'])
    def help_handler(message):
        # first name of current user
        user_name = message.from_user.first_name
        help_message = 'Рады преветствовать вас, {}!\nДля того чтобы начать, пожалуйста,' \
                       ' введите команду /start'.format(user_name)

        # send message to user who wrote /help command
        bot.send_message(message.chat.id, help_message)

    # handler for /start command
    @bot.message_handler(commands=['start'])
    def start_handler(message):
        username = message.from_user.username
        user_name = message.from_user.first_name

        tutor_id = check_is_tutor_and_return_id_of_they(username)

        if(tutor_id):
            # if current user is tutor send Welcome message
            bot.send_message(message.chat.id, "Добро пожаловать, {}".format(user_name))

            # store tutor id in object of DataCurrSession class
            data_obj.tutor_id = tutor_id

            sql_to_get_groups = """
                SELECT groups.id, groups.title
                FROM tutors
                INNER JOIN group_subject ON tutors.user_id = group_subject.tutor_id
                INNER JOIN groups ON group_subject.group_id = groups.id
                WHERE tutors.user_id = {};
            """.format(tutor_id)

            # get array of groups of current tutor
            array_of_groups = wrap_cursor_execute(sql_to_get_groups)

            # if tutor has no group send message and DO NOT CONTINUE sending messages to that tutor-
            # only waiting for /help or /start command
            if (array_of_groups == None):
                bot.send_message(message.chat.id, 'У вас нет групп')
            else:
                # if tutor has groups - create a keyboard with group.name as button
                keyboard_groups = types.ReplyKeyboardMarkup(row_width=3, one_time_keyboard=True)
                for group in array_of_groups:
                    group_button = types.KeyboardButton(group[1])
                    keyboard_groups.add(group_button)

                # send message "Выберите группу" and show keyboard with groups
                # reply_markup argument - means that user can only write to bot using out keyboard with groups
                msg = bot.send_message(message.chat.id, 'Выберите группу:', reply_markup=keyboard_groups)
                # msg - our message ('Выберите группу:')
                # register_next_step_handler - it means that out message above will handle another handler
                # function handle_group will handle group after clicking on keyboard
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

        # get group id to store it in data_obj
        group_id = wrap_cursor_execute(sql_to_set_group_id)

        data_obj.group_id = group_id[0][0]

        sql_to_get_subjects = """
        SELECT s.title, st.short FROM subjects AS s
        INNER JOIN group_subject ON s.id = group_subject.subject_id
        INNER JOIN subject_types AS st on s.type_id = st.id
        WHERE group_subject.group_id = {} AND group_subject.tutor_id = {};
        """.format(data_obj.group_id, data_obj.tutor_id)

        array_of_subjects = wrap_cursor_execute(sql_to_get_subjects)

        # if that group has no subjects DO NOT CONTINUE processing, only send message
        if (array_of_subjects == None):
            bot.send_message(message.chat.id, 'У этой группы пока нет предметов')
        else:
            # everything is like in previous handler
            keyboard_subjects = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
            for subject in array_of_subjects:
                subject_button = types.KeyboardButton('{} ({})'.format(subject[0], subject[1]))
                keyboard_subjects.add(subject_button)

            msg = bot.send_message(message.chat.id, 'Выберите предмет:', reply_markup=keyboard_subjects)

            # handle_subject will handle that message (msg)
            bot.register_next_step_handler(msg, handle_subject)


    def handle_subject(message):
        sql_to_get_subject_id = """
        SELECT s.id FROM subjects AS s
        INNER JOIN subject_types AS st ON s.type_id = st.id
        WHERE CONCAT(s.title, ' (', st.short, ')') = '{}';
        """.format(message.text)

        # get subject id to store it in data_obj
        subject_id = wrap_cursor_execute(sql_to_get_subject_id)

        data_obj.subject_id = subject_id[0][0]

        sql_to_get_students = """
        SELECT id, lastname, firstname FROM students
        WHERE group_id = {}
        ORDER BY lastname
        COLLATE  utf8_unicode_ci;
        """.format(data_obj.group_id)

        array_of_students = wrap_cursor_execute(sql_to_get_students)

        # if that group has no student send message and DO NOT CONTINUE processing
        if (array_of_students == None):
            bot.send_message(message.chat.id, 'В этой группе пока нет студентов')
        else:
            # function in function because I need to handle students as chain one after another one
            # cycle doesn't work for it
            # it's like recursion but with 2 functions)
            def launch_students(message, i):
                """
                Main function which works with counter i which we are using as index for array of students
                :param message: form this param we take chat.id to send messages only for current user
                :param i: counter and index for array of students
                :return:
                """

                def handle_one_student(message, i, length):
                    """

                    :param message: message obj, we use it to get text of the message from user and to get chat.id
                    :param i: counter, index for array
                    :param length: length of array of students (if out of bounds) do not call launch_students()
                    :return:
                    """

                    # convert answer 'Есть', "Нету" into bool to send in DB
                    answer = 0 if (message.text == 'Есть') else 'null'

                    current_data_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    sql_to_insert_to_journal = """
                    INSERT INTO journal_records (student_id, column_id, value, created_at, updated_at)
                    VALUES ({}, {}, {}, '{}', '{}')
                    """.format(data_obj.curr_student_id, data_obj.column_id, answer,
                               current_data_string, current_data_string)

                    # try to write data into DB
                    try:
                        global DB
                        if not DB.open:
                            DB = pymysql.connect('localhost', 'root', '', 'unnamed')

                        cursor.execute(sql_to_insert_to_journal)
                        # if okay - commit changes
                        DB.commit()
                    except Exception as e:
                        # if error - rollback and print error in console
                        DB.rollback()
                        print(traceback.format_exc())

                    # i < than length of array of student - continue
                    if(i < length - 1):
                        i += 1
                        launch_students(message, i)


                length_of_array_students = len(array_of_students)

                # one_time_keyboard - is a param for keyboard. Here I check
                # if current student is the last in array: hide keyboard after him
                # else do not hide keyboard
                one_time_keyboard = False if (i < length_of_array_students - 1) else True

                # creating a keyboard
                keyboard_student = types.ReplyKeyboardMarkup(row_width=2,
                                                             one_time_keyboard=one_time_keyboard)
                # two buttons for keyboard
                btn_is = types.KeyboardButton('Есть')
                btn_absent = types.KeyboardButton('Нет')
                keyboard_student.row(btn_is, btn_absent)
                # msg with fullname of student
                # array_of_students[i][1] - lastname array_of_students[i][2] - firstname
                msg = bot.send_message(message.chat.id,
                                       array_of_students[i][1]+' '+array_of_students[i][2],
                                       reply_markup=keyboard_student)
                # store id of current student in data_obj to get easy access to it in handle_one_student func
                data_obj.curr_student_id = array_of_students[i][0]

                # as handler for message (msg) we set handle_one_student function
                # then handle_one_student will call current function and this 'recursion' will
                # be continued while i < length of array of students
                bot.register_next_step_handler(msg, handle_one_student, i, length_of_array_students)

            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            wrap_cursor_execute("""
                insert into journal_columns (group_id, subject_id, created_at, updated_at)
                values ({}, {}, '{}', '{}')
                """.format(data_obj.group_id, data_obj.subject_id, date, date)
            )
            data_obj.column_id = cursor.lastrowid
            launch_students(message, 0)

except:
    print('Error')
    print(traceback.format_exc())
finally:
    # for bot working all time
    bot.polling()
    DB.close()


