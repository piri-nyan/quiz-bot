import sqlite3, logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def db_con(function):
    def wrapper_db_con(*args, **kwargs):
        logging.info('Opening connection to db')
        cnn = sqlite3.connect("database.db")
        cur = cnn.cursor()
        logging.info('Opened connection to db')
        try:
            logging.info('Executing db operation')
            result = function(cnn, cur, *args, **kwargs)
        except Exception as e:
            logging.warning('Exception occured')
            print(e)
        else:
            logging.info('Operation on db executed successfully')
            cnn.commit()
        finally:
            logging.info('Closing connection to db')
            cnn.close()
        return result
    return wrapper_db_con

@db_con
def create_db(cnn, cur):
    print(cnn, cur)
    cur.executescript(open("database.sql").read())

def main():
    pass

if __name__ == "__main__":
    create_db()