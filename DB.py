from mysql.connector import connect, Error
from ENV import env


class DB:
    def __init__(self, host, user, password, db_name, port='3306'):
        try:
            self.connection = connect(
                host=host,
                user=user,
                password=password,
                database=db_name,
                port=port,
            )
            self.success = True
        except Error as e:
            print(e)
            self.connection = None
            self.success = False

    def query(self, sql, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
            res = cursor.fetchall()
            self.connection.commit()
            return res
        except Error as e:
            print(e.msg)
            return False


DB = DB(
    env.get('db_host'),
    env.get('db_user'),
    env.get('db_password'),
    env.get('db_name'),
    env.get('db_port'),
)
