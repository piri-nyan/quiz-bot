import telegram
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, PollHandler, PollAnswerHandler, Filters, CallbackContext, ConversationHandler
import logging
import json

from db_worker import db_con
from creation_handler import quiz

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

class statifier:
    def __init__(self) -> None:
        pass

class questioner:
    def __init__(self, quest_gen, update) -> None:
        self.update=update
        self.quest_gen=quest_gen
    
    def ask_next_question(self):
        try:
            question = next(self.quest_gen)
            self.update.message.reply_poll(is_anonymous=False, type="quiz", question=question[2], options=question[3].split(";"), correct_option_id=question[3].split(";").index(question[4]))
        except:
            self.update.message.reply_text("Thats all questions")

def get_answer(update):
    answers = update.poll.options

    for answer in answers:
        if answer.voter_count == 1:
            # found it
            ret = answer.text
            break
    return ret

def is_answer_correct(update):
  answers = update.poll.options

  ret = False
  counter = 0

  for answer in answers:
    if answer.voter_count == 1 and update.poll.correct_option_id == counter:
      ret = True
      break
    
    counter = counter + 1
  return ret

@db_con
def get_quiz_list(cnn, cur):
    cur.execute("select * from quizes")
    res = cur.fetchall()
    return res

@db_con
def get_questions(cnn, cur, quiz_id):
    cur.execute(f"select * from questions where quiz_id = '{quiz_id}'")
    res = cur.fetchall()
    return res

def start(update: Update, context: CallbackContext):
    """Start the chat"""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!'
    )

def help(update: Update, context: CallbackContext):
    """Display help"""
    update.message.reply_text('You can view all commands by typing / or pressing commands button on the right side of the input field')

def message_handler(update: Update, context: CallbackContext):
    """On message callback"""
    update.message.reply_text("I dont talk without a purpose, try one of the commands")

def question_generator(quiz_id):
    questions = get_questions(quiz_id)
    for question in questions:
        yield(question)

def poll_handler(update: Update, context: CallbackContext):
    print(context)
    print(update)
    print(get_answer(update))
    print(is_answer_correct(update))
    quizer.ask_next_question()

def poll_answer_handler(update: Update, context: CallbackContext):
    print(update)

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
    answer = update.message.text
    global quizer 
    quizer = questioner(question_generator(answer), update)
    quizer.ask_next_question()
    return ConversationHandler.END

def stop(update: Update, context: CallbackContext):
    print("stop executed")
    pass

def test(update: Update, context: CallbackContext):
    print(update)

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
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
    dispatcher.add_handler(CommandHandler("test", test))
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

    dispatcher.add_handler(quiz().CCH())

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()