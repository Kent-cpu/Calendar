import telebot
import gspread
import datetime
import calendar
from bs4 import BeautifulSoup
from datetime import date, timedelta

gc = gspread.service_account(filename="creds.json")
sh = gc.open("Расписание")
bot = telebot.TeleBot("1799617235:AAH6YI3rdpbthgXvZxryYNWzQzxzl11cbXc")
koordinateCell = {"Программирование (лаб) 9:45-11:20": "A3", "Исит (лаб) 11:45-13:20": "A4"}

def determineParity(currentDate): # определяет четность недели
    year = currentDate.year if currentDate.month >= 9 else currentDate.year - 1
    startDate = datetime.date(year, 9, 1)
    d1 = startDate - timedelta(days = startDate.weekday())
    d2 = currentDate - timedelta(days = currentDate.weekday())
    if ((d2-d1).days // 7) % 2 == 0:
        return "Нечетная неделя"
    return "Четная неделя"  

worksheet = sh.worksheet(determineParity(date.today())) # datetime.now = 2021-04-05 01:21:16.883348

def parse(path, htmlEl, className): # парсит из определенного html контента дедлайн и возращает отформатированный список словарей с датами
    with open(path, encoding= 'utf-8') as file:
        fileParse = file.read()
    soup = BeautifulSoup(fileParse, "lxml")
    htmlContent = soup.find_all(htmlEl, class_= className)
    dedline = {"День": 0, "Месяц": 0, "Год": 0}
    allDedlineList = []
    for el in htmlContent:
        text = el.text.split("-")
        for i in range(0, len(text)):
            dedline[list(dedline)[i]] = int(text[i])
        allDedlineList.append(dedline.copy()) 
    return allDedlineList 


def write(path, htmlEl, className, itemName, currDate): # записывает в google shets дедлайны
    dedline = parse(path, htmlEl, className)
    for el in dedline: 
        if currDate.day <= el["День"] and currDate.month <= el["Месяц"] and currDate.year <= el["Год"]:
            stateWeek = determineParity(datetime.date(el["Год"], el["Месяц"], el["День"]))           
            textCell = f"{itemName} {el['День']}.{el['Месяц']}.{el['Год']}"
            sh.worksheet(stateWeek).update(koordinateCell[itemName], textCell)
            break
            
def clearDedline():
    for key in koordinateCell.keys():
        sh.worksheet("Нечетная неделя").update(koordinateCell[key], key)
        sh.worksheet("Четная неделя").update(koordinateCell[key], key)
        

def beauPrint(objStr):
    return "\n".join(study for study in objStr)

def fillingDeadlines(todayYear):
    write("icit.html", "td", "dedline", "Исит (лаб) 11:45-13:20", todayYear)
    write("programm.html", "td", "dedline", "Программирование (лаб) 9:45-11:20", todayYear)

clearDedline()

@bot.message_handler(commands=['start'])
def startWork(message):
    bot.send_message(message.chat.id, "Команды:\n1./Сегодня\n2./Завтра\n3./Неделя\n4./Неделя_сл")


@bot.message_handler(commands=['Сегодня'])
def myToday(message):
    fillingDeadlines(datetime.date.today())
    bot.send_message(message.chat.id, beauPrint(worksheet.col_values(datetime.datetime.now().isocalendar()[2]))) # Получаем индекс дня Понедельник - 1 и выводим.
  

@bot.message_handler(commands=['Завтра'])
def tomorrow(message):
    currentDate = datetime.date.today()
    nextDay = currentDate.day + 1
    d = date(currentDate.year, currentDate.month, nextDay)
    fillingDeadlines(d)
    bufWorksheet = sh.worksheet(determineParity(d))
    bot.send_message(message.chat.id, beauPrint(bufWorksheet.col_values(datetime.datetime.now().isocalendar()[2] + 1)))

@bot.message_handler(commands=['Неделя'])
def thisWeek(message):
    fillingDeadlines(datetime.date.today())
    for dayWeek in range(1 , 6): 
        bot.send_message(message.chat.id, beauPrint(worksheet.col_values(dayWeek)))


@bot.message_handler(commands=['Неделя_сл'])
def nextWeek(message):
    nextWeek = datetime.timedelta(days = 7) + datetime.date.today()
    dNext = datetime.date(nextWeek.year, nextWeek.month, nextWeek.day)
    fillingDeadlines(dNext)
    buf = worksheet
    if determineParity(date.today()) == "Четная неделя":
        buf = sh.worksheet("Нечетная неделя")
    else:
        buf = sh.worksheet("Четная неделя")
    for dayWeek in range(1, 6):
        bot.send_message(message.chat.id, beauPrint(buf.col_values(dayWeek)))

bot.polling()