import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
import requests
from bs4 import BeautifulSoup
import datetime as dt

BOT_TOKEN = "6171562705:AAFfbU05aBM1pRFQnxOA2RSN_0vxgI_ERbo"
USER_BD = dict()
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
    global USER_BD
    user = update.effective_user
    USER_BD[user] = {
        "LOGIN": "",
        "PASSWORD": "",
        "SESSION": requests.Session()
    }
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я твой помощник по школьным делам. Мне нужен ваш логин и пароль"
        rf" от вашего аккаунта на сайте edu.tatar.ru. Введите логин:",
    )
    return 1


async def help_command(update, context):
    await update.message.reply_text("Я пока не умею помогать...")


async def get_login(update, context):
    global USER_BD
    USER_BD[update.effective_user]["LOGIN"] = update.message.text
    await update.message.reply_text("Теперь введите пароль.")
    return 2


async def get_password_and_logon(update, context):
    global USER_BD
    USER_BD[update.effective_user]["PASSWORD"] = update.message.text
    await update.message.reply_text("Произвожу анализ данных...")
    datas = {
        'main_login2': USER_BD[update.effective_user]["LOGIN"],
        'main_password2': USER_BD[update.effective_user]["PASSWORD"]
    }
    if "Выберите дальнейшее действие" in requests.post('https://edu.tatar.ru/logon', data=datas, headers=header).text:
        await update.message.reply_text(
            "Не правильный логин или пароль. Вход не произведен. Чтобы заново произвести вход введите /start"
        )
    elif "Мой дневник" not in requests.post('https://edu.tatar.ru/logon', data=datas, headers=header).text:
        await update.message.reply_text(
            "Вы ввели данные не от аккаунта ученика. Вход не произведен. Чтобы заново произвести вход введите /start"
        )
    else:
        save_cookies = USER_BD[update.effective_user]["SESSION"].post('https://edu.tatar.ru/logon',
                                                                      data=datas, headers=header)
        await update.message.reply_text(
            "Вы успешно авторизовались как ученик. Выберите действия: /homework, /lesson_time, /full_term, /short_term"
        )
    return ConversationHandler.END


async def stop(update, context):
    return ConversationHandler.END


async def homework_command(update, context):
    global USER_BD
    soup = BeautifulSoup(USER_BD[update.effective_user]["SESSION"].get("https://edu.tatar.ru/user/diary/day",
                                                                       headers=header).text, features="lxml")
    urls = soup.find('div', {"class": "dsw"}).find_all('a')
    next_day = BeautifulSoup(USER_BD[update.effective_user]["SESSION"].get(urls[1].get("href"),
                                                                           headers=header).text, features="lxml")
    db = []
    subjects_homeworks = []
    for i in next_day.find('tbody').find_all('td'):
        db.append(i.text)
    for i in range(len(db)):
        if i % 5 == 1:
            subjects_homeworks.append(
                f"Предмет: {db[i][:]}\nДомашнее задание: {' '.join(db[i + 1][:].split())}"
            )
    for i in subjects_homeworks:
        await update.message.reply_text(i)


async def lesson_time_command(update, context):
    global USER_BD
    soup = BeautifulSoup(USER_BD[update.effective_user]["SESSION"].get("https://edu.tatar.ru/user/diary/day",
                                                                       headers=header).text, features="lxml")
    lesson_time = []
    n = 1
    for i in soup.find('tbody').find_all('td'):
        if len(i.text) == 11 and i.text.count(":") == 2:
            lesson_time.append(f"{n} урок: " + i.text)
            n += 1
    if not lesson_time:
        urls = soup.find('div', {"class": "dsw"}).find_all('a')
        next_day = BeautifulSoup(USER_BD[update.effective_user]["SESSION"].get(urls[1].get("href"),
                                                                               headers=header).text, features="lxml")
        lesson_time = []
        n = 1
        for i in next_day.find('tbody').find_all('td'):
            if len(i.text) == 11 and i.text.count(":") == 2:
                lesson_time.append(f"{n} урок: " + i.text)
                n += 1
    await update.message.reply_text("\n".join(lesson_time))


async def full_term_command(update, context):
    global USER_BD
    term = BeautifulSoup(USER_BD[update.effective_user]["SESSION"].get("https://edu.tatar.ru/user/diary/term",
                                                                       headers=header).text, features="lxml")
    termDB = []
    n = 1
    for i in term.find('tbody').find_all('tr'):
        if n != len(term.find('tbody').find_all('tr')):
            termDB.append((i.text.split('\n'))[1:-4])
        n += 1
    for i in termDB:
        if '.' not in i[-1]:
            i[-1] = "- Оценки по данному предмету не ставятся"
        i = [j for j in i if j != ""]
        await update.message.reply_text(" ".join(i))


async def short_term_command(update, context):
    global USER_BD
    term = BeautifulSoup(USER_BD[update.effective_user]["SESSION"].get("https://edu.tatar.ru/user/diary/term",
                                                                       headers=header).text, features="lxml")
    termDB = []
    n = 1
    for i in term.find('tbody').find_all('tr'):
        if n != len(term.find('tbody').find_all('tr')):
            termDB.append((i.text.split('\n'))[1:-4])
        n += 1
    for i in termDB:
        if '.' not in i[-1]:
            i[-1] = "Оценки по данному предмету не ставятся"
        i = [i[0], i[-1]]
        await update.message.reply_text(": ".join(i))


async def set_timer(update, context):
    chat_id = update.effective_message.chat_id
    context.job_queue.run_once(task, 5, chat_id=chat_id, name=str(chat_id), data=5)

    text = f'Вернусь через 5 с.!'
    await update.effective_message.reply_text(text)


async def task(context):
    await context.bot.send_message(context.job.chat_id, text=f'КУКУ! 5c. прошли!')


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('homework', homework_command))
    application.add_handler(CommandHandler('lesson_time', lesson_time_command))
    application.add_handler(CommandHandler('full_term', full_term_command))
    application.add_handler(CommandHandler('short_term', short_term_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler("set", set_timer))
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
