import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = "6171562705:AAFfbU05aBM1pRFQnxOA2RSN_0vxgI_ERbo"
LOGIN = ""
PASSWORD = ""
SESSION = requests.Session()
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/41.0.2272.101 Safari/537.36',
    'referer': 'https://edu.tatar.ru/logon'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я твой помощник по школьным делам. Мне нужен ваш логин и пароль"
        rf" от вашего аккаунта на сайте edu.tatar.ru. Введите логин:",
    )
    return 1


async def help_command(update, context):
    await update.message.reply_text("Я пока не умею помогать...")


async def get_login(update, context):
    global LOGIN
    LOGIN = update.message.text
    await update.message.reply_text("Теперь введите пароль.")
    return 2


async def get_password_and_logon(update, context):
    global PASSWORD
    PASSWORD = update.message.text
    await update.message.reply_text("Произвожу анализ данных...")
    n = logon()
    if n == 1:
        await update.message.reply_text("Не правильный логин или пароль. Вход не произведен. "
                                        "Чтобы заново произвести вход введите /start")
    elif n == 2:
        await update.message.reply_text("Вы ввели данные не от аккаунта ученика. Вход не произведен. "
                                        "Чтобы заново произвести вход введите /start")
    else:
        await update.message.reply_text("Вы успешно авторизовались как ученик. Выберите действия:")
    return ConversationHandler.END


async def stop(update, context):
    return ConversationHandler.END


async def homework_command(update, context):
    global SESSION
    soup = BeautifulSoup(SESSION.get("https://edu.tatar.ru/user/diary/day", headers=header).text, features="lxml")
    urls = soup.find('div', {"class": "dsw"}).find_all('a')
    next_day = BeautifulSoup(SESSION.get(urls[1].get("href"), headers=header).text, features="lxml")
    db = []
    subjects_homeworks = []
    for i in next_day.find('tbody').find_all('td'):
        db.append(i.text)
    for i in range(len(db)):
        if i % 5 == 1:
            subjects_homeworks.append(f"Предмет: {db[i][:]}\n"
                                      f"Домашнее задание: {' '.join(db[i + 1][:].split())}")
    for i in subjects_homeworks:
        await update.message.reply_text(i)


def logon():
    global SESSION
    datas = {
        'main_login2': LOGIN,
        'main_password2': PASSWORD
    }
    if "Выберите дальнейшее действие" in requests.post('https://edu.tatar.ru/logon', data=datas, headers=header).text:
        return 1
    elif "Мой дневник" not in requests.post('https://edu.tatar.ru/logon', data=datas, headers=header).text:
        return 2
    else:
        save_cookies = SESSION.post('https://edu.tatar.ru/logon', data=datas, headers=header)
        return 3


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('homework', homework_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_login)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password_and_logon)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    ))
    application.run_polling()


if __name__ == '__main__':
    main()
