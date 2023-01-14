<<<<<<< Updated upstream
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

    def query(self, sql, params=None, prefix=True, simple=False, retry=True):
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
=======
from mysql.connector import connect, Error
from ENV import env


class DB:
    _instance = None

    class DBConnect:
        config = None
        connection = None
        success = False
        prefix = None

        def __init__(self, host, user, password, database, port, prefix):
            try:
                self.config = {
                    'host': host,
                    'user': user,
                    'password': password,
                    'database': database,
                    'port': port,
                    'prefix': prefix,
                }
                self.connection = connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database,
                    port=port,
                    autocommit=True,
                )
                self.success = True
                self.prefix = prefix
            except Error as e:
                print(e.msg)
                self.connection = None
                self.success = False

    def __init__(self, host, user, password, database, port='3306', prefix=None):
        if self._instance is None:
            self._instance = self.DBConnect(host, user, password, database, port, prefix)

    def __getattr__(self, an_attr):
        if an_attr == '_instance':
            return self._instance
        else:
            return getattr(self._instance, an_attr)

    def __setattr__(self, an_attr, a_value):
        if an_attr == '_instance':
            self._instance = a_value
        else:
            return setattr(self._instance, an_attr, a_value)

    def query(self, sql, params=None, prefix=True, retry=True):
        if prefix:
            sql = add_prefix(sql)

        try:
            cursor = self._instance.connection.cursor()
            cursor.execute(sql, params)
            res = cursor.fetchall()
            return res
        except Error as e:
            print(e.msg)
            if retry:
                config = self._instance.config
                self._instance = self.DBConnect(**config)
                if self._instance.success:
                    return self.query(sql, params, False)
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


def add_prefix(sql):
    return sql.replace('alliances', db.prefix + 'alliances') \
        .replace('tasks', db.prefix + 'tasks') \
        .replace('users', db.prefix + 'users')

>>>>>>> Stashed changes
