from mysql.connector import connect, Error
from ENV import env


class DB:
    _config = None
    _connection = None
    _cursor = None
    _dict_cursor = None
    prefix = None

    def __init__(self, host, user, password, database, port='3306', prefix=None):
        self._config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'port': port,
            'autocommit': True,
        }
        if self.__connect():
            self.prefix = prefix

    def __connect(self):
        try:
            self._connection = connect(**self._config)
            self._cursor = self._connection.cursor()
            self._dict_cursor = self._connection.cursor(dictionary=True)
            return True
        except Error:
            self._connection = None
            return False

    def query(self, sql, params=None, prefix=True, simple=True, retry=True):
        if prefix:
            sql = sql.replace('alliances', self.prefix + 'alliances') \
                .replace('tasks', self.prefix + 'tasks') \
                .replace('users', self.prefix + 'users')

        try:
            cursor = self._cursor if simple else self._dict_cursor
            cursor.execute(sql, params)
            return cursor.fetchall()
        except Error as e:
            print('Error occurred in MySQL', e.msg, 'Try to reconnect')
            if retry and self.__connect():
                return self.query(sql, params, False, simple, False)
            print('Reconnection failed! End sql and params: ', end='')
            print(sql)
            print(params)
            return False


db = DB(
    env.get('db_host'),
    env.get('db_user'),
    env.get('db_password'),
    env.get('db_name'),
    env.get('db_port'),
    env.get('db_prefix'),
)
