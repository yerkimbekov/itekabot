import ssl
import json
import time
import math
import telebot
import sqlite3
import requests
import logging
from sqlite3 import Error
from telebot import types


# Inilization
url = "HIDDEN"
url_cities = url + "HIDDEN"
url_short_name = url + "HIDDEN"
url_speller = "HIDDEN"
bot = telebot.TeleBot('HIDDEN')

# Sqlite Execution
def post_sql_query(sql_query):
    with sqlite3.connect('users_info.db') as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(sql_query)
        except Error:
            pass
        connection.commit()
        result = cursor.fetchall()
        return result


# Sqlite Values Execution
def post_sql_vals_query(sql_query, vals):
    with sqlite3.connect('users_info.db') as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(sql_query, vals)
        except Error:
            pass
        connection.commit()
        result = cursor.fetchall()
        return result


# Creating Tables
def create_tables():
    users_query = '''CREATE TABLE IF NOT EXISTS users 
                        (id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        city_id INTEGER,
                        lst_res TEXT);'''
    post_sql_query(users_query)
    users_query = '''CREATE TABLE IF NOT EXISTS medicaments 
                        (id INTEGER PRIMARY KEY,
                        medicament_id INTEGER,
                        city_id INTEGER,
                        request TEXT);'''
    post_sql_query(users_query)


# Register User
def register_user(message, city_id):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        if not check_user_exist(user_id):
            insert_to_db_query = 'INSERT INTO users (user_id, username, first_name,  last_name, city_id, lst_res) VALUES (?, ?, ?, ?, ?, ?)'
            vals = (user_id, username, first_name, last_name, city_id, "None",)
            post_sql_vals_query(insert_to_db_query, vals)
            # time.sleep(1)
            query_c = 'SELECT id FROM users WHERE user_id = ?'
            vals = (user_id, )
            how_many = post_sql_vals_query(query_c, vals)
            # print(how_many)
            textt = "New user #" + str(how_many[0]) + "\n" + str(user_id) + "\n" + str(username) + "\n" + str(first_name) + "\n" + str(last_name)
            bot.send_message(chat_id = "HIDDEN", text = textt)
    except Exception as e:
        print("ERROR register_user")
        print(e)


# Update City
def update_city(call, city_id):
    if get_users_city_id(call.message.chat.id) == "-1":
        send_message_keyboard(call.message, "Привет! Я чат бот i-teka по поиску лекарств. ✋😃\nЯ работаю 24/7, без выходных. Я помогу Вам найти нужное лекарство в аптеках Вашего города!", start_menu())
    update_query = 'UPDATE users SET city_id = ? WHERE user_id = ?'
    vals = (city_id, call.message.chat.id, )
    post_sql_vals_query(update_query, vals)
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = "Ваш город сохранен.")
    except:
        print("There error in editting message: {}".format(call.message.chat.id))


# Update Last Response
def update_lst_res(user_id, res):
    update_query = 'UPDATE users SET lst_res = ? WHERE user_id = ?'
    vals = (res, user_id, )
    post_sql_vals_query(update_query, vals)


# Update JSON request
def update_json(medicament_id, request, city_id):
    json_check_query = 'SELECT * FROM medicaments WHERE medicament_id = {} AND city_id = {};'.format(medicament_id, city_id)
    if post_sql_query(json_check_query):
        update_query = 'UPDATE medicaments SET request = "{}" WHERE medicament_id = {}'.format(request, medicament_id)
    else:
        update_query = 'INSERT INTO medicaments (medicament_id, request, city_id) VALUES ({}, "{}", {});'.format(medicament_id, request, city_id)
    post_sql_query(update_query)


# Get Last Response
def get_json(medicament_id, city_id):
    user_json_query = 'SELECT request FROM medicaments WHERE medicament_id = {} AND city_id = {} ORDER BY id DESC'.format(medicament_id, city_id)
    return post_sql_query(user_json_query)[0]


# Get Last Response
def get_lst_res(user_id):
    user_check_query = 'SELECT lst_res FROM users WHERE user_id = {};'.format(user_id)
    return post_sql_query(user_check_query)[0][0]


# Get Users City Id
def get_users_city_id(user_id):
    try:
        user_id = str(user_id)
        user_check_query = 'SELECT city_id FROM users WHERE user_id = {};'.format(user_id)
        return str(post_sql_query(user_check_query)[0][0])
    except Exception as e:
        print("ERROR_01")
        print(e)
        return None


# Check Users Existence
def check_user_exist(user_id):
    user_check_query = 'SELECT * FROM users WHERE user_id = {};'.format(user_id)
    return post_sql_query(user_check_query)


# User Selects City
def select_city(message, want_to_change):
    if not check_user_exist(message.from_user.id):
        register_user(message, -1)
        select_city(message, want_to_change)
        return
    if get_users_city_id(message.from_user.id) == "-1" or want_to_change == True:
        city_inline_markup = city_selection(1)
        send_message_keyboard(message, "Выберите свой город:", city_inline_markup)


# City Selection Process
def city_selection(pageid):
    try:
        city_inline_markup = types.InlineKeyboardMarkup()  
        cities = GetCities()
        for i in range((pageid-1)*5, min(len(cities), pageid*5)):
            city_inline_markup.add(types.InlineKeyboardButton(cities[i]['name'], callback_data = "city-" + str(cities[i]['id'])))
        if pageid == 1:
            city_inline_markup.add(types.InlineKeyboardButton("След →", callback_data = "pagecity-" + str(pageid + 1)))
        elif math.ceil(len(cities)/5) > pageid:
            city_inline_markup.add(
                types.InlineKeyboardButton("← Пред", callback_data = "pagecity-" + str(pageid - 1)),
                types.InlineKeyboardButton("След →", callback_data = "pagecity-" + str(pageid + 1)) 
            )
        else:
            city_inline_markup.add(types.InlineKeyboardButton("← Пред", callback_data = "pagecity-" + str(pageid - 1)))
        return city_inline_markup
    except Exception as e:
        print(e)


# Medicament Selection Process
def medicament_selection(user_id, pageid):
    medicament_inline_markup = types.InlineKeyboardMarkup() 
    medicaments = GetMedicamentsFullName(get_lst_res(user_id), str(get_users_city_id(user_id)), str(pageid))['response']['medicaments']
    for i in range(0, len(medicaments)):
        medicament_inline_markup.add(types.InlineKeyboardButton(medicaments[i]['name'], callback_data = "cure-" + str(medicaments[i]['id'])))
        update_json(int(medicaments[i]['id']), medicaments[i], get_users_city_id(user_id))
    if not medicaments[0]['prev_page'] and medicaments[0]['next_page']:
        medicament_inline_markup.add(types.InlineKeyboardButton("След →", callback_data = "pagecure-" + str(pageid + 1)))
    elif medicaments[0]['prev_page'] and medicaments[0]['next_page']:
        medicament_inline_markup.add(
            types.InlineKeyboardButton("← Пред", callback_data = "pagecure-" + str(pageid - 1)),
            types.InlineKeyboardButton("След →", callback_data = "pagecure-" + str(pageid + 1)) 
        )
    elif medicaments[0]['prev_page'] and not medicaments[0]['next_page']:
        medicament_inline_markup.add(types.InlineKeyboardButton("← Пред", callback_data = "pagecure-" + str(pageid - 1)))
    return medicament_inline_markup


# Medicament Was Selected
def update_medicament(call):
    try:
        query = json.loads(get_json(call.data[5:], get_users_city_id(call.message.chat.id))[0].replace('\'', '\"').replace('True', '\"True\"').replace('False', '\"False\"'))
        url_photo = query['photo']
        choice_markup = types.InlineKeyboardMarkup()  
        if query['price']:
            text = 'Название: \"' + query['name'] + '\"\n' + query['recept'] + '\n' + 'Цена от ' + query['price'] + '<a href=\"{}\">&#8203;</a>'.format(url_photo)
            choice_markup.add(types.InlineKeyboardButton("Назад", callback_data = "back"),
                types.InlineKeyboardButton("Показать аптеки", callback_data = "show-" + str(query['id']) + '-1'))
        else:
            text = 'Название: \"' + query['name'] + '\"\n' + query['recept'] + '\n' + 'Нет в наличии в аптеках' + '<a href=\"{}\">&#8203;</a>'.format(url_photo)
            choice_markup.add(types.InlineKeyboardButton("Назад", callback_data = "back"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = text, reply_markup = choice_markup, parse_mode = "HTML")
    except Exception as e:
        print("There error in editting message: {}".format(call.message.chat.id))
        print(e)


# Pharmacies Selecetion Process
def pharm_get(call):
    try:
        pageid = int(call.data[5:].split('-')[1])
        pharms = get_pharm(call)['response']['pharmacies']
        text = ""
        for pharm in pharms: 
            text = text + 'Название: ' + pharm['name'] + '\nЦена: ' + pharm['price'] + '\nАдрес: ' + pharm['address'] + '\n' + pharm['phone'] + '\nДата обновления: ' + pharm['updated']
            if pharm['availability'] == "1":
                text = text + '\n<b>Наличие: Подтверждено (Можно идти и покупать)</b>'
            else:
                text = text + '\n<b>Наличие: Неподтверждено (Необходимо уточнить в аптеке)</b>'
            text = text + '\n\n'
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = text, reply_markup = pharm_pages(call), parse_mode = "HTML")
    except Exception as e:
        pass


# Pharmacies Pages Process
def pharm_pages(call):
    try:
        pageid = int(call.data[5:].split('-')[1])
        pharm_inline_markup = types.InlineKeyboardMarkup() 
        pharms = get_pharm(call)['response']['pharmacies']
        count_all = pharms[0]['count_all']
        if pharms[0]['next_page'] and not pharms[0]['prev_page']:
            pharm_inline_markup.add(types.InlineKeyboardButton("След →", callback_data = "show-" + str(call.data[5:].split('-')[0]) + '-' + str(pageid + 1)))
        elif pharms[0]['next_page'] and pharms[0]['prev_page']:
            pharm_inline_markup.add(
                types.InlineKeyboardButton("← Пред", callback_data = "show-" + str(call.data[5:].split('-')[0]) + '-' + str(pageid - 1)),
                types.InlineKeyboardButton("След →", callback_data = "show-" + str(call.data[5:].split('-')[0]) + '-' + str(pageid + 1)) 
            )
        elif not pharms[0]['next_page'] and pharms[0]['prev_page']:
            pharm_inline_markup.add(types.InlineKeyboardButton("← Пред", callback_data = "show-" + str(call.data[5:].split('-')[0]) + '-' + str(pageid - 1)))
        return pharm_inline_markup  
    except Exception as e:
        pass


# Get Pharmacies
def get_pharm(call):
    med_id = call.data[5:].split('-')[0]
    pageid = call.data[5:].split('-')[1]
    url_pharm = "HIDDEN"
    payload = {
        'request': '{"city":{"id": "' + get_users_city_id(call.message.chat.id) + '"}, "medicament": {"id": "' + med_id + '"}, "page_number": "' + str(pageid) + '", "count_on_page": "5" }'
    }
    response = requests.post(url_pharm, data = payload, timeout=5)
    return response.json()


# Get All Cities
def GetCities():
    try:
        response = requests.get(url_cities, timeout=5)         # TODO check when it's not 200
        if response.status_code != 200:
            print("ERROR: Status Code :", response.status_code)
            return
        return(response.json()['response']['city'])
    except Exception as e:
        print("ERROR GetCities")
        print(e)


# Get Cures Short Name
def GetMedicamentsFullName(text, city_id, page_id):
    payload = {
        'request': '{"text": "' + text + '", "city":{"id": "' + city_id + '"}, "page_number":"' + page_id + '", "count_on_page": "5"}'
    }
    response = requests.post(url_short_name, data = payload, timeout=5)
    return response.json()


# Get All Num Of Medicaments
def col_medicaments(text, city_id):
    payload = {
        'request': '{"text": "' + text + '", "city":{"id": "' + city_id + '"}, "page_number":"1", "count_on_page": "5"}'
    }
    response = requests.post(url_short_name, data = payload, timeout=5)
    return response.json()['response']['medicaments'][0]['count_all']

# Get Medicaments Info
def GetMedicamentsInfo(text, city_id):
    payload = {
        'request': '{"text": "' + text + '", "city":{"id": "' + city_id + '", "withoutdescription": "1"}}'
    }
    response = requests.post(url + "HIDDEN", data = payload, timeout=5)
    return response.json()


# Yandex Speller
def Speller(text):
    payload = {
        'request': '{"text": "' + text + '"}'
    }
    response = requests.post(url_speller, data = payload, timeout=5)
    if response.json():
        return response.json()['response']['words']
    return response.json()


# Sending Keyboard Message
def send_message_keyboard(message, text, keyboard):
    try:
        bot.send_message(chat_id = message.chat.id, text = text, reply_markup = keyboard)
    except Exception as e:
        print("No such chat: {}".format(message.chat.id))
        print(e)


# Edit Call Message Next/Prev Pages Of Cities
def edit_call_city_page(call, keyboard):
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = "Выберите свой город:", reply_markup = keyboard)
    except:
        pass


# Edit Call Message Next/Prev Pages Of Cures
def edit_call_cure_page(call, keyboard):
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = "✅ Вот что мы нашли по вашему запросу:\nВсего найдено: {}".format(col_medicaments(str(get_lst_res(call.message.chat.id)), get_users_city_id(call.message.chat.id))), reply_markup = keyboard)
    except Exception as e:
        pass


# Sending Message
def send_message(message, text):
    try:
        return bot.send_message(chat_id = message.chat.id, text = text)
    except:
        print("No such chat: {}".format(message.chat.id))


# Building Start Menu
def start_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    choice_search = types.KeyboardButton("🔍Поиск")
    choice_city = types.KeyboardButton("🔁Сменить город")
    choice_help = types.KeyboardButton("🆘Помощь")
    markup.add(choice_search,choice_city,choice_help)
    return markup


# Correction On Choice
def correction(message):
    correction_inline = types.InlineKeyboardMarkup()
    for i in Speller(message.text):
        if (utf8len("_" + i['word']) > 63):
            continue
        correction_inline.add(types.InlineKeyboardButton(i['word'], callback_data = "_" + str(i['word'])))
    send_message_keyboard(message, "❔Мы ничего не нашли по запросу \"{}\"\nВозможно вы имели ввиду:".format(message.text), correction_inline)  


# Showing Results After Correction
def show_result_correction(call):
    try:
        update_lst_res(call.message.chat.id, str(call.data[1:]))
        medicament_inline_markup = medicament_selection(call.message.chat.id, 1)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = "✅ Вот что мы нашли по вашему запросу:\nВсего найдено: {}".format(col_medicaments(str(call.data[1:]), get_users_city_id(call.message.chat.id))), reply_markup = medicament_inline_markup)
    except Exception as e:
        print("ERROR show_result_correction\n", e)

# Showing Results Of Medicaments
def show_result(message):
    try:
        update_lst_res(message.from_user.id, str(message.text))
        medicament_inline_markup = medicament_selection(message.from_user.id, 1)
        send_message_keyboard(message, "✅ Вот что мы нашли по вашему запросу:\nВсего найдено: {}".format(col_medicaments(str(message.text), get_users_city_id(message.from_user.id))), medicament_inline_markup)
    except Exception as e:
        print("ERROR show_result\n", e)

# Size of Bytes of String
def utf8len(s):
    return len(s.encode('utf-8'))


# Main Code
create_tables()


# Handlers
@bot.message_handler(commands = ['start'])

def start(message):
    register_user(message, -1)
    if get_users_city_id(message.from_user.id) == "-1":
        select_city(message, False)
        return
    send_message_keyboard(message, "Привет! Я чат бот i-teka по поиску лекарств в твоем городе. ✋😃\nЯ работаю 24/7, без выходных. Я помогу Вам найти нужное лекарство в аптеках Вашего города!", start_menu())


@bot.message_handler(content_types=['text'])

def handle_message(message):
    try:
        if not check_user_exist(message.from_user.id):
            start(message)
            return
        if message.text == "🆘 Помощь":
            return send_message(message, "Привет! Я чат бот i-teka по поиску лекарств. ✋😃\nЯ работаю 24/7, без выходных. Я помогу Вам найти нужное лекарство в аптеках Вашего города!\n\n❓Что я умею?\n✅Искать лекарства по названию\n✅Искать аптеки в которых есть это лекарство\n✅Подбирать аналоги лекарства, если нужного лекарства нет в аптеках\n✅Показываю статусы \"Наличие подтверждено\" и \"наличие не подтверждено\". \n☝️Если Вы видите статус \"наличие подтверждено\", то можно смело идти в аптеку и покупать лекарство, оно там точно есть!\n☝️Если видите статус \"наличие не подтверждено\" то это означает, что фармацевты не успели обновить информацию, и Вам лучше позвонить в аптеку и уточнить о наличии лекарства.\n\n‼️Помните о том, что я лишь программа и не понимаю человеческую речь! Я понимаю лишь то, что указано в инструкции по пользованию ☝️Советую внимательно ознакомиться, в случае, если у Вас что-то не получилось. \n\nА вот и инструкция:\n✅Вам нужно выбрать свой город \n✅Отправьте название лекарства (убедитесь, что Вы написали его без ошибок)\n✅Я предложу Вам список лекарств и дозировку\n✅Я покажу аптеки, в которых есть данное лекарство и статус \"наличие подтверждено\" или \"наличие не подтверждено\".")
        elif message.text == "🔍 Поиск":
            return send_message(message, "Какое лекарство вас интересует ?")
        elif get_users_city_id(message.from_user.id) == "-1":
            select_city(message, False)
            return
        elif message.text == "🔁 Сменить город":
            select_city(message, True)
        elif len(message.text) < 3:
            return send_message(message, "🚫 Длина поисковой строки должна быть больше 2-х символов")
        else:
            found = GetMedicamentsFullName(message.text, str(get_users_city_id(message.from_user.id)), "1")
            if len(found) == 0:
                if len(Speller(message.text)) == 0:
                    return send_message(message, '🚫 Прошу прощение, такого лекарства в базе нету.')
                correction(message)
                return
            show_result(message)
    except Exception as e:
        print("something went wrong during handling message")
        print(e)

@bot.message_handler(content_types=['audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'location', 'contact'])

def not_message(message):
    try:
        send_message(message, '🚫 Пожалуйста, отправьте сообщение в виде текста.')
    except Exception as e:
        print(e)


@bot.callback_query_handler(func=lambda call:True)

def callback_handler(call):
    try:
        if call.data.startswith('pagecity'):
            pageid = int(call.data[9:])
            edit_call_city_page(call, city_selection(pageid))
        elif call.data.startswith('city'):
            cityid = int(call.data[5:])
            update_city(call, cityid)
        elif call.data.startswith('pagecure'):
            pageid = int(call.data[9:])
            edit_call_cure_page(call, medicament_selection(call.message.chat.id,pageid))
        elif call.data.startswith('back'):
            edit_call_cure_page(call, medicament_selection(call.message.chat.id,1))
        elif call.data.startswith('cure'):
            update_medicament(call)
        elif call.data.startswith('_'):
            show_result_correction(call)
        elif call.data.startswith('show'):
            pharm_get(call)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print("ERROR during callback handler")
        print(e)

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as err:
        logging.error(err)
        time.sleep(5)
        print("Internet error")
