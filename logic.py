import telebot
import gspread
import datetime
import calendar
import time
import re
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from datetime import date, timedelta

gc = gspread.service_account(filename="creds.json")
sh = gc.open("Расписание")
bot = telebot.TeleBot("1799617235:AAH6YI3rdpbthgXvZxryYNWzQzxzl11cbXc")
koordinateCell = {"Программирование (лаб) 9:45-11:20": "A3", "Исит (лаб) 11:45-13:20": "A4"}
driver = webdriver.Chrome('chromedriver.exe')
programm , icit = "", ""

def parseDedline(needSubject):
    time.sleep(5)
    subject = driver.find_elements_by_xpath("//input[@title = 'Выбрать']")
    indexSubjectButton = {"Программирование": 13, "Исит": 12} 
    subject[indexSubjectButton[needSubject]].click()
    time.sleep(4)
    htmlContent = BeautifulSoup(driver.page_source, "lxml")
    allElementParse = ""
    for el in htmlContent.find_all("td", class_= False):
        allElementParse += el.get_text(strip = True)
    allElementParse  = re.findall(r"\d{2}-\d{2}-\d{4}", allElementParse)
    driver.find_element_by_xpath('//input[@value="Вернуться"]').send_keys(Keys.ENTER)
    time.sleep(4)
    return allElementParse

def authorization(login, password):
    driver.get('https://eios.kemsu.ru/a/eios')
    time.sleep(5)
    driver.find_element_by_name('username').send_keys("stud67266")
    driver.find_element_by_name('password').send_keys("bZqb11Fy")
    driver.find_element_by_class_name("css-h0m9oy").send_keys(Keys.ENTER)
    time.sleep(5)
    linkInfo = driver.find_element_by_link_text('Информационное обеспечение учебного процесса (ИнфОУПро)')
    driver.get(linkInfo.get_attribute("href"))

def determineParity(currentDate): # определяет четность недели
    year = currentDate.year if currentDate.month >= 9 else currentDate.year - 1
    startDate = datetime.date(year, 9, 1)
    d1 = startDate - timedelta(days = startDate.weekday())
    d2 = currentDate - timedelta(days = currentDate.weekday())
    if ((d2-d1).days // 7) % 2 == 0:
        return "Нечетная неделя"
    return "Четная неделя"  


def clearDedline():
    for key in koordinateCell.keys():
        sh.worksheet("Нечетная неделя").update(koordinateCell[key], key)
        sh.worksheet("Четная неделя").update(koordinateCell[key], key)


worksheet = sh.worksheet(determineParity(date.today())) 
clearDedline()

def parse(subjectParse): # парсит из определенного html контента дедлайн и возращает отформатированный список словарей с датами
    allDedlineList = []
    for el in range(0, len(subjectParse)):
        text = subjectParse[el].split("-")
        allDedlineList.append(datetime.date(int(text[2]), int(text[1]), int(text[0])))
    return sorted(allDedlineList) 


def write(itemName, currDate, subjectPars): # записывает в google shets дедлайны
    for el in range(0, len(subjectPars)):
        if subjectPars[el] >= currDate:
            stateWeek = determineParity(subjectPars[el])           
            sh.worksheet(stateWeek).update(koordinateCell[itemName], itemName + " " + subjectPars[el].strftime("%d.%m.%Y"))
            break
              
def beauPrint(objStr):
    return "\n".join(study for study in objStr)


def fillingDeadlines(todayYear):
    write("Исит (лаб) 11:45-13:20", todayYear, parse(icit))
    write("Программирование (лаб) 9:45-11:20", todayYear, parse(programm))


@bot.message_handler(commands=['start'])
def startWork(message):
    authorization("stud67266", "bZqb11Fy")
    global programm, icit
    programm, icit = parseDedline("Программирование"), parseDedline("Исит")
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
    nextWeek = datetime.timedelta(days = datetime.datetime.today().weekday() + 1) + datetime.date.today()
    fillingDeadlines(nextWeek)
    buf = worksheet
    if determineParity(date.today()) == "Четная неделя":
        buf = sh.worksheet("Нечетная неделя")
    else:
        buf = sh.worksheet("Четная неделя")
    for dayWeek in range(1, 6):
        bot.send_message(message.chat.id, beauPrint(buf.col_values(dayWeek)))

bot.polling()