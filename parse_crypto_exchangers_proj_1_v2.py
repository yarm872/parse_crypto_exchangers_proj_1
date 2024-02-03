from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import gspread
import telebot
import time



#1. Сделать рабочего бота
#2. Бот разделял инфу между отсутсвием и позицией (не выше 3 - плохо)
#3. Информировал на какой позиции среди всех находится и ссылка (например 15 из 50 и ссылка) если проблема
#4. Сделать бота автономным (добавить таймер каждые тридцать минут)

bot = telebot.TeleBot('6863128147:AAGgI6b2nlG2oI_mZuhDnUfJVtvsvhrDIFU')


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, '<b>Я бот смотрю инфу по обменникам :)</b>', parse_mode='html')

def get_data_from_google_table():
    
    gc = gspread.service_account(filename='D:/1_MY PROGS/ПАРСЕРЫ/проект кирилла/mytest-411319-99861ed21234.json')
    sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1uCnggnsUDmjUIlI18Iw0JxivWGlEJ9ug1IOK0orLANg/edit#gid=0')
    #sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1XBhj_Hw68Oo71ZZSRcE5qBZfZoL4oPZkISnlRv6x1Po/edit#gid=0') #test table
    worksheet = sh.sheet1
    
    
    
    list_of_exchangers_and_urls=[]
    for i in range(1,7):
        values_list = worksheet.col_values(i)
        values_list.pop(1)
        list_of_exchangers_and_urls.append(values_list)
    return list_of_exchangers_and_urls

def get_result_data():
    main_data = get_data_from_google_table()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    names = list()

    i =- 1
    for current_exchanger in main_data:
        i += 1
        names.append([current_exchanger[0]])
        #проход по обменнику и его ссылкам
    
        for url in current_exchanger[1:]:
        
            #проход по каждой ссылке обменника
            try:
                driver.get(url)                              
            
                list_of_exchangers = driver.find_element(By.ID,"rates_block")
                list_of_exchangers = list_of_exchangers.find_element(By.ID,"content_table")
                list_of_exchangers = list_of_exchangers.find_element(By.TAG_NAME,"tbody")
                list_of_exchangers = list_of_exchangers.find_elements(By.TAG_NAME,"tr")
                #список объектов обменников на сайте получен
                names_of_exchangers_on_page = []
                for exchanger in list_of_exchangers:
                    data = exchanger.find_element(By.CLASS_NAME,"bj")
                    names_of_exchangers_on_page.append(data.text) #список названий обменников на сайте получен и добавлен
                #print(f"Перед добавлением {url} names-->",names)
                names[i].append({url:names_of_exchangers_on_page}) #для каждой ссылки запись имен обменников представленных на сайте
                #print("После добавлением names-->",names,end="\n")
            except Exception as ex:
                #если в таблице встретили пустую ячейку - ничего не делаем
                pass
    return names
    #names - переменная со всей инфой
    # со структурой --> 
    # [
    # [название сервиса, {ссылка: [название обменника по ссылке, название обменника по ссылке]}, {ссылка: [название обменника по ссылке, название обменника по ссылке]}]
    # [название сервиса, {ссылка: [название обменника по ссылке, название обменника по ссылке]}, {ссылка: [название обменника по ссылке, название обменника по ссылке]}]
    # [название сервиса, {ссылка: [название обменника по ссылке, название обменника по ссылке]}, {ссылка: [название обменника по ссылке, название обменника по ссылке]}]
    # ]

def get_formated_data(data):
    result_absence="Отсутствие-\n"
    result_top3_from_bottom="Выше топ 3 снизу-\n"
    result_top3_from_start="Стоят в топ 3 сверху-\n"
    x = data[0] #название сервиса
    for item in data[1:]:
        for key, value in item.items():
            
            #на этом моменте рассматриваем одну из 3 ситуаций
            if x in value:
                position = value.index(x)
                position_from_end = len(value) - position
                
                if position in [0,1,2]:
                    direction=""
                    for j in key[26:]:
                        if j!=".":
                            direction+=j
                        else:
                            break
                    result_top3_from_start+=direction+"\n"
                
                elif position_from_end not in [1,2,3]:
                    direction=""
                    for j in key[26:]:
                        if j!=".":
                            direction+=j
                        else:
                            break
                    result_top3_from_bottom+=direction+"\n" + str(position) + "/" + str(len(value))
                    
            
            elif x not in value: #значит отсутсвие
                #вытягивание направления
                #https://www.bestchange.ru/bitcoin-to-qiwi.html?light=958
                direction=""
                for j in key[26:]:
                    if j!=".":
                        direction+=j
                    else:
                        break
                result_absence+=direction+"\n"
                #итог direction=bitcoin-to-qiwi
    
    result_data=x + ":\n" + result_absence + "\n" + result_top3_from_bottom + "\n" + result_top3_from_start         
    return result_data


global main_data
main_data=get_result_data()
for i in main_data:
    x=get_formated_data(i)
    print(x)


@bot.message_handler()
def message_fails(message):
    if message.text=="стоп":
            exit()
    if message.text == "📝 Отчет" or message.text == "отчет" or message.text == "/test":
        main_data=get_result_data()
    for i in main_data:
        x=get_formated_data(i)
        bot.send_message(message.chat.id, text=x)
        
    time.sleep(120)
    bot.send_message(message.chat.id, text="прошло 2 мин")
    return message_fails(message)


bot.polling(non_stop=True, interval=0)