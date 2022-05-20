import telegram
from telegram import Update, ForceReply
from telegram import chat
from telegram import poll
from telegram.ext import Updater, CommandHandler, MessageHandler, PollHandler, PollAnswerHandler, Filters, CallbackContext, ConversationHandler
import logging
import json
from threading import Timer
from datetime import datetime

from pathlib import Path

from db_worker import db_con
from creation_handler import quiz
import exporter

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

@db_con
def get_quiz_list(cnn, cur):
    cur.execute("select * from quizes")
    res = cur.fetchall()
    return res

@db_con
def get_quiz(cnn, cur, quiz_id):
    cur.execute(f"select * from quizes where id = '{quiz_id}'")
    res = cur.fetchall()
    return res

@db_con
def get_questions(cnn, cur, quiz_id):
    cur.execute(f"select * from questions where quiz_id = '{quiz_id}'")
    res = cur.fetchall()
    return res

@db_con
def write_quiz_start(cnn, cur, quiz_id, chat_id, polls, start_time):
    str_polls = ""
    for poll in polls:
        print(poll)
        if polls.index(poll) == len(polls)-1:
            str_polls += f"{poll}"
        else:
            str_polls += f"{poll};"
    
    cur.execute(f"insert into polls (quiz_id, chat_id, poll_msg_ids, date) values ({quiz_id}, {chat_id}, '{str_polls}', '{start_time}')")

@db_con
def write_poll_info(cnn, cur, poll_msg_id, poll_id, question, options, correct_id):
    cur.execute(f"insert into polls_info (poll_id, poll_msg_id, question, options, correct_id) values ({poll_id}, {poll_msg_id}, '{question}', '{options}', {correct_id})")

@db_con
def write_answer(cnn, cur, poll_id, option_id, user_id, name, username):
    cur.execute(f"insert into answers (poll_id, option_id, user_id, name, username) values ({poll_id}, {option_id}, {user_id}, '{name}', '{username}')")

@db_con
def write_stats(cnn, cur, update):
    options = ""
    for option in update.poll.options:
        if update.poll.options.index(option)==len(update.poll.options)-1:
            options += f"{option.text}:{option.voter_count}"
        else:
            options += f"{option.text}:{option.voter_count};"
    
    cur.execute(f"insert into poll_stats (poll_id, question, options, correct_id) values ({update.poll.id}, '{update.poll.question}', '{options}', {update.poll.correct_option_id})")

# TO FIX
@db_con
def show_stats(cnn, cur, chat_id, polls):
    stats_by_question = ""
    for poll in polls:
        cur.execute(f"select poll_id from polls_info where poll_msg_id = {poll}")
        poll_id = cur.fetchone()[0]
        print(poll_id)
        cur.execute(f"select * from poll_stats where poll_id = {poll_id}")
        poll_stats = cur.fetchone()
        print(poll_stats)
        stats_by_question += f"{poll_stats[2]}:\n"
        for count in poll_stats[3].split(';'):
            print(poll_stats[3].split(';'))
            print(f"{count.split(':')[0]}: {count.split(':')[1]}\n")
            stats_by_question += f"{count.split(':')[0]}: {count.split(':')[1]}\n"
        print(poll_stats[3].split(';'))
        stats_by_question += f"Right answer was {poll_stats[3].split(';')[poll_stats[4]].split(':')[0]}\n"

    print(stats_by_question)
    bot.send_message(chat_id, stats_by_question)

@db_con
def send_stats(cnn, cur, chat_id, quiz_id):
    exporter.to_exel(quiz_id)
    file = f"./export/{quiz_id}.xlsx"
    bot.send_document(chat_id=chat_id, document=open(file, "rb"))
            

def start(update: Update, context: CallbackContext):
    """Start the chat"""
    user = update.effective_user
    chat_id = update.message.chat.id
    quiz_id = context.args[0]
    update.message.reply_text('Value is ' + quiz_id)
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!'
    )
    ask_questions(quiz_id, chat_id)

def help(update: Update, context: CallbackContext):
    """Display help"""
    update.message.reply_text('You can view all commands by typing / or pressing commands button on the right side of the input field')

def question_generator(quiz_id):
    questions = get_questions(quiz_id)
    for question in questions:
        yield(question)

def poll_handler(update: Update, context: CallbackContext):
    print(update)
    write_stats(update)

def poll_answer_handler(update: Update, context: CallbackContext):
    print(update)
    write_answer(update.poll_answer.poll_id, update.poll_answer.option_ids[0], update.poll_answer.user.id, update.poll_answer.user.first_name, update.poll_answer.user.username)

def quizes(update: Update, context: CallbackContext):
    quiz_list = get_quiz_list()
    quiz_list_str = ""
    for quiz in quiz_list:
        quiz_list_str += str(list(quiz))[1:-1].replace(",", "").replace("'", "")+"\n"
    update.message.reply_markdown(f"Available quizes: \n {quiz_list_str}")

def start_quiz(update: Update, context: CallbackContext):
    update.message.reply_text("Which quiz would you like to participate in?")
    return 1

def quiz_id_response(update: Update, context: CallbackContext):
    print(update.message.text)
    quiz_id = update.message.text
    chat_id = update.message.chat.id
    ask_questions(quiz_id, chat_id)
    return ConversationHandler.END

def prompt_quiz_id(update: Update, context: CallbackContext):
    update.message.reply_text("Which quiz would you like to view statistics on?")
    return 1

def quiz_id_stats(update: Update, context: CallbackContext):
    print(update.message.text)
    quiz_id = update.message.text
    chat_id = update.message.chat.id
    send_stats(chat_id, quiz_id)
    return ConversationHandler.END

def ask_questions(quiz_id, chat_id):
    time = int(list(get_quiz(quiz_id))[0][3])
    questions = get_questions(quiz_id)
    polls = []
    q_cnt = 1
    for question in questions:
        if len(question[2])>300:
            #question_str = question[2][:300]
            question_str=f"{q_cnt}"
        else:
            #question_str = question[2]
            question_str=f"{q_cnt}"
        q_cnt+=1
        bot.send_message(chat_id=chat_id, text=f"Полный текст вопроса:\n{question[2]}")
        options_lst = []
        options_str = "Полный текст вариантов ответа: \n"
        o_cnt=1
        for option in question[3].split(";"):
            options_str += f"{o_cnt}.{option}\n"
            o_cnt+=1
            if len(option)>100:
                options_lst.append(option[:100])
            else:
                options_lst.append(option)
        print(question)
        msg = bot.send_poll(chat_id=chat_id, is_anonymous=False, type="quiz", question=question_str, options=options_lst, correct_option_id=int(question[4]))
        bot.send_message(chat_id=chat_id, text=options_str)
        polls.append(msg.message_id)
        write_poll_info(msg.message_id, msg.poll.id, question[2], question[3], question[4])
    print(polls)
    write_quiz_start(quiz_id, chat_id, polls, datetime.now().strftime("%d-%m-%Y %I:%M%p"))
    t=Timer(time, stop_polls, [chat_id, polls])
    t.start()

def stop_polls(chat_id, polls):
    for poll in polls:
        print(chat_id, poll)
        bot.stop_poll(chat_id, poll)
    bot.send_message(chat_id, "Test ended, all polls are closed")
    show_stats(chat_id, polls)

def message_handler(update: Update, context: CallbackContext):
    """On message callback"""
    update.message.reply_text("I dont talk without a purpose, try one of the commands")

def stop(update: Update, context: CallbackContext):
    print("stop executed")
    pass

def stop2(update: Update, context: CallbackContext):
    print("stop executed")
    pass

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    global bot
    bot = telegram.Bot(token=open('token', 'r').read())
    # updater = Updater(open('token', 'r').read())

    bot.delete_my_commands()
    cmds = json.load(open('commands.json', 'r'))
    commands = []
    for cmd in cmds['commands']:
        commands.append(telegram.BotCommand(cmd['command'], cmd['description']))
    bot.set_my_commands(commands)

    updater = Updater(bot=bot)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on poll
    dispatcher.add_handler(PollHandler(poll_handler, pass_chat_data=True, pass_user_data=True))
    dispatcher.add_handler(PollAnswerHandler(poll_answer_handler, pass_chat_data=True, pass_user_data=True))

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("quizes", quizes))
    #dispatcher.add_handler(CommandHandler("test", test))
    #dispatcher.add_handler(CommandHandler("start_quiz", start_quiz))

    # on non command i.e message - handle the message on Telegram
    #dispatcher.add_handler(MessageHandler(Filters.text, message_handler))

    # on conversation
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start_quiz", start_quiz)],
        states={
            1 : [MessageHandler(Filters.text, quiz_id_response)],
        },
        fallbacks=[CommandHandler("stop", stop)],
    ))

    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler("show_stats", prompt_quiz_id)],
        states={
            1 : [MessageHandler(Filters.text, quiz_id_stats)],
        },
        fallbacks=[CommandHandler("stop", stop2)],
    ))

    dispatcher.add_handler(quiz().CCH())

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()