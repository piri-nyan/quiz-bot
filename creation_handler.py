from logging import FileHandler
import telegram
from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram import message
from telegram.ext import Updater, CommandHandler, MessageHandler, PollHandler, Filters, CallbackContext, ConversationHandler
from telegram.replykeyboardremove import ReplyKeyboardRemove

from db_worker import db_con
from importer import from_docx
import os

class quiz:
    def __init__(self, **kwargs) -> None:
        pass

    def create_quiz(self, update: Update, context: CallbackContext):
        keyboard = [
            ['Документ', 'Голосования']
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)
        update.message.reply_text("Выбери тип создания:", reply_markup=reply_markup)

        return 2

    def choose_type(self, update: Update, context: CallbackContext):
        if update.message.text == "Документ":
            update.message.reply_text("Отправь мне документ или напиши /stop для отмены")
            return 1
        elif update.message.text == "Голосования":
            update.message.reply_text("Как будет называться тест?")
        return 3

    def document_parse(self, update: Update, context: CallbackContext):
        update.message.reply_text("Обрабатываю...")
        with open(f"import/{update.message.document.file_id}.docx", 'wb') as f:
            context.bot.get_file(update.message.document).download(out=f)
        quizes = from_docx(f"import/{update.message.document.file_id}.docx")
        for quiz in quizes:
            quiz_id = create_quiz_id(quizes[quiz]["name"], 1800)
            for question in quizes[quiz]["questions"]:
                options = parse_dict_options(quizes[quiz]["questions"][question]["variants"])
                try:
                    add_question(quiz_id, quizes[quiz]["questions"][question]["question"], options, quizes[quiz]["questions"][question]["variants"]["correct"])
                except Exception as e:
                    pass
        os.remove(f"import/{update.message.document.file_id}.docx")
        return ConversationHandler.END

    def name_quiz(self, update: Update, context: CallbackContext):
        self.name = update.message.text

        update.message.reply_text("Set time for test in minutes")
        return 4

    def set_time(self, update: Update, context: CallbackContext):
        self.time = int(update.message.text)*60
        self.id = create_quiz_id(self.name, self.time)

        keyboard = [
            ['Add question', 'Finish']
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard,
                                       #one_time_keyboard=True,
                                       resize_keyboard=True)
        update.message.reply_text("Select an action", reply_markup=reply_markup)
        return 5

    def prompt_poll(self, update: Update, context: CallbackContext):
        if update.message.text == "Add question":
            update.message.reply_text("Send me a poll to add to a quiz")
            return 6
        elif update.message.text == "Finish":
            update.message.reply_text("Saving quiz", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

    def parse_options(self, options):
        str_opts = ""
        for option in options:
            print(option)
            if options.index(option) == len(options)-1:
                str_opts += f"{option['text']}"
            else:
                str_opts += f"{option['text']};"
        return str_opts

    def read_poll(self, update: Update, context: CallbackContext):
        print("reading poll")
        print(update.message.poll)
        question = update.message.poll.question
        options = self.parse_options(update.message.poll.options)
        if update.message.poll.type == 'quiz':
            correct = update.message.poll.correct_option_id
        else:
            correct = "none"
        add_question(self.id, question, options, correct)
        
        return 5

    def finish(self, update: Update, context: CallbackContext):
        pass

    def CCH(self):
        handler = ConversationHandler(
            entry_points=[CommandHandler("create_quiz", self.create_quiz)],
            states={
                0 : [MessageHandler(Filters.text, self.finish)],
                1 : [MessageHandler(Filters.document, self.document_parse)],
                2 : [MessageHandler(Filters.text, self.choose_type)],
                3 : [MessageHandler(Filters.text, self.name_quiz)],
                4 : [MessageHandler(Filters.text, self.set_time)],
                5 : [MessageHandler(Filters.text, self.prompt_poll)],
                6 : [MessageHandler(Filters.poll, self.read_poll)]
            },
            fallbacks=[CommandHandler("stop", stop)],
        )
        return handler

def parse_dict_options(options):
    str_options = ""
    print(options)
    for option in options:
        print(option)
        if option != "correct":
            str_options+=f"{options[option]};"
    return str_options[:-1]

@db_con
def create_quiz_id(cnn, cur, quiz_name, time):
    cur.execute(f"insert into quizes(name, time) values('{quiz_name}', {time})")
    quiz_id = cur.lastrowid
    return quiz_id

@db_con
def add_question(cnn, cur, quiz_id, question, options, correct):
    cur.execute(f"insert into questions(quiz_id, question, answers, right_answer) values({quiz_id}, '{question}', '{options}', '{correct}')")

def stop():
    pass

if __name__ == "__main__":
    create_quiz_id("123")