import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler, ContextTypes
import requests
from bs4 import BeautifulSoup
import datetime

BOT_TOKEN = "6171562705:AAFfbU05aBM1pRFQnxOA2RSN_0vxgI_ERbo"
application = Application.builder().token(BOT_TOKEN).build()
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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global USER_BD
    user = update.effective_user
    USER_BD[user] = {
        "LOGIN": "",
        "PASSWORD": "",
        "SESSION": requests.Session(),
        "SITE_CODE": ""
    }
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я твой помощник по школьным делам. Мне нужен ваш логин и пароль"
        rf" от вашего аккаунта на сайте edu.tatar.ru. Введите логин:",
    )
    return 1


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(  # дополнить по мере завершения проекта
        "/start - выходит из аккаунта, надо будет заново ввести логин и пароль\n"
        "/help - показывает эту информацию повторно\n"
        "/homework - показывает домашние задания на завтра\n"
        "/lesson_time - показывает расписание звонков\n"
        "/full_term - показывает полный табель оценок\n"
        "/short_term - показывает средний балл по каждому предмету\n"
        "/set_notifications - включает ежедневные уведомления о расписании на день и о полученной оценке\n"
        "/unset_notifications - выключает все уведомления"
    )


async def get_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global USER_BD
    USER_BD[update.effective_user]["LOGIN"] = update.message.text
    await update.message.reply_text("Теперь введите пароль")
    return 2


async def get_password_and_logon(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        USER_BD[update.effective_user]["SESSION"].post('https://edu.tatar.ru/logon',
                                                       data=datas, headers=header)
        await update.message.reply_text(  # дополнить по мере завершения проекта
            "Вы успешно авторизовались как ученик. Выберите действия:\n"
            "/start - выходит из аккаунта, надо будет заново ввести логин и пароль\n"
            "/help - показывает эту информацию повторно\n"
            "/homework - показывает домашние задания на завтра\n"
            "/lesson_time - показывает расписание звонков\n"
            "/full_term - показывает полный табель оценок\n"
            "/short_term - показывает средний балл по каждому предмету\n"
            "/set_notifications - включает ежедневные уведомления о расписании на день и о полученной оценке\n"
            "/unset_notifications - выключает все уведомления"
        )
    return ConversationHandler.END


async def stop():
    return ConversationHandler.END


async def homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    if subjects_homeworks:
        for i in subjects_homeworks:
            await update.message.reply_text(i)
    else:
        await update.message.reply_text("Завтра воскресенье, отдыхай")


async def lesson_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def full_term_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def short_term_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def send_notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    global USER_BD
    job = context.job
    soup = BeautifulSoup(USER_BD[job.data]["SESSION"].get("https://edu.tatar.ru/user/diary/day",
                                                          headers=header).text, features="lxml")

    db = []
    subjects_homeworks = []
    lesson_time = []
    n = 1
    for i in soup.find('tbody').find_all('td'):
        db.append(i.text)
        if len(i.text) == 11 and i.text.count(":") == 2:
            lesson_time.append(f"{n} урок: " + i.text)
            n += 1

    for i in range(len(db)):
        if i % 5 == 1:
            subjects_homeworks.append(
                f"Предмет: {db[i][:]}"
            )

    if not lesson_time:
        urls = soup.find('div', {"class": "dsw"}).find_all('a')
        next_day = BeautifulSoup(USER_BD[job.data]["SESSION"].get(urls[1].get("href"),
                                                                  headers=header).text, features="lxml")
        lesson_time = []
        n = 1
        for i in next_day.find('tbody').find_all('td'):
            if len(i.text) == 11 and i.text.count(":") == 2:
                lesson_time.append(f"{n} урок: " + i.text)
                n += 1

    if datetime.datetime.now().isoweekday() != 7:
        await context.bot.send_message(job.chat_id, text="Ваше расписание на сегодня:")

        for i, j in zip(subjects_homeworks, lesson_time):
            await context.bot.send_message(job.chat_id, text=f"{j}\n{i}")

    context.job_queue.run_once(send_notification, 86400, chat_id=context.job.chat_id,
                               name=str(context.job.chat_id), data=job.data)


async def send_mark(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # крч, надо теперь это втюхнуть в таймер; сделать, чтоб так же ежедневно обновляться без сообщения
    global USER_BD
    job = context.job
    soup = BeautifulSoup(USER_BD[job.data]["SESSION"].get("https://edu.tatar.ru/user/diary/day",
                                                          headers=header).text, features="lxml")
    urls = soup.find('div', {"class": "dsw"}).find_all('a')
    soup = BeautifulSoup(USER_BD[update.effective_user]["SESSION"].get(urls[1].get("href"),
                                                                       headers=header).text, features="lxml")
    if USER_BD[update.effective_user]["SITE_CODE"] == "":
        USER_BD[update.effective_user]["SITE_CODE"] = soup
    elif USER_BD[update.effective_user]["SITE_CODE"] == soup:
        pass
    else:
        a = BeautifulSoup(USER_BD[job.data]["SESSION"].get("https://edu.tatar.ru/user/diary/day", headers=header).text,
                          features="lxml").find("tbody").find_all('tr')
        b = USER_BD[job.data]["SITE_CODE"].find("tbody").find_all('tr')
        for i in set(a) - set(b):
            i = i.text.split("\n")
            if len(i) > 13:
                await context.bot.send_message(context.job.chat_id, text=f"Вы получили оценку по предмету {i[2]}\n"
                                                                         f"Оценка: {i[-4]}")
        USER_BD[update.effective_user]["SITE_CODE"] = soup


async def set_notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Уведомления включены")
    time_now = [int(i) for i in str(datetime.datetime.now().time())[:8].split(":")]
    time_now = time_now[0] * 3600 + time_now[1] * 60 + time_now[2]
    TIMER = 28800 - time_now if 28800 > time_now else 86400 - time_now + 28800
    context.job_queue.run_once(send_notification, TIMER, chat_id=update.effective_message.chat_id,
                               name=str(update.effective_message.chat_id), data=update.effective_user)


async def unset_notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    def remove_job_if_exists(name, conntext):
        current_jobs = conntext.job_queue.get_jobs_by_name(name)
        if not current_jobs:
            return False
        for job in current_jobs:
            job.schedule_removal()
        return True

    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Уведомления отключены" if job_removed else 'Вы не включали уведомления'
    await update.message.reply_text(text)


def main():
    application.add_handler(CommandHandler('homework', homework_command))
    application.add_handler(CommandHandler('lesson_time', lesson_time_command))
    application.add_handler(CommandHandler('full_term', full_term_command))
    application.add_handler(CommandHandler('short_term', short_term_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('set_notifications', set_notifications_command))
    application.add_handler(CommandHandler('unset_notifications', unset_notifications_command))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_login)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password_and_logon)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    ))
    application.run_polling()


if __name__ == '__main__':
    main()
