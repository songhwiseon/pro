import pymysql

def get_db_connection():
    return pymysql.connect(
        host='5gears.iptime.org',
        port=3306,
        user='manufacture_user',
        password='andong1234',
        database='manufacture',
    )

def get_db_connection2():
    return pymysql.connect(
        host='5gears.iptime.org',
        port=3306,
        user='root',
        password='andong1234',
        database='analysis',
    )