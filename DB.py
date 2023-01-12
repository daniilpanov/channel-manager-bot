from mysql.connector import connect, Error
from ENV import env


class DB:
    def __init__(self, host, user, password, database, port='3306', prefix=None):
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
            )
            self.success = True
            self.prefix = prefix
        except Error as e:
            print(e.msg)
            self.connection = None
            self.success = False

    def query(self, sql, params=None, prefix=True, retry=True):
        if prefix:
            sql = add_prefix(sql)

        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
            res = cursor.fetchall()
            self.connection.commit()
            return res
        except Error as e:
            print(e.msg)
            if retry:
                new_inst = reconnect(DB(**self.config))
                if new_inst.success:
                    return new_inst.query(sql, params, False)
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


def reconnect(inst):
    global db
    db = inst
    return inst
