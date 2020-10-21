import sqlite3
from sqlite3 import Error

def post_sql_query(sql_query):
    with sqlite3.connect('my.db') as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(sql_query)
        except Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print('SQLite traceback: ')
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))
            pass
        result = cursor.fetchall()
        return result


def create_orders_table():
    orders_query = '''CREATE TABLE IF NOT EXISTS ORDERS
                        (order_id INTEGER PRIMARY KEY,
                        username TEXT,
                        startpoint TEXT,
                        endpoint TEXT,
                        weight TEXT,
                        cargo_type TEXT,
                        start_date TEXT,
                        price TEXT,
                        payment_type TEXT,
                        carrier_username TEXT,
                        status TEXT,
                        weight_limitations TEXT,
                        mileage TEXT,
                        reg_date TEXT);'''
    post_sql_query(orders_query)


def create_users_table():
    users_query = '''CREATE TABLE IF NOT EXISTS USERS
                        (username TEXT,
                        full_name TEXT,
                        role TEXT,
                        ownership TEXT,
                        company_name TEXT,
                        id_code TEXT,
                        phone TEXT,
                        reg_date TEXT,
                        chat_id TEXT);'''
    post_sql_query(users_query)


def register_user(username, full_name, role, ownership,
                    company_name, id_code, phone, chat_id, reg_date):
    user_check_query = f'SELECT * FROM USERS WHERE username = "{username}";'
    user_check_data = post_sql_query(user_check_query)

    if not user_check_data:
        insert_to_db_query = f'INSERT INTO USERS (username, full_name, role, '\
                            f'ownership, company_name, id_code, phone, chat_id, '\
                            f'reg_date) VALUES ("{username}", "{full_name}", '\
                            f'"{role}", "{ownership}", "{company_name}", '\
                            f'"{id_code}", "{phone}", "{chat_id}", "{reg_date}");'
        post_sql_query(insert_to_db_query)


def register_order(username, startpoint, endpoint, weight,
                    cargo_type, start_date, price, payment_type,
                    carrier_username, status, weight_limitations,
                    mileage, reg_date):
    insert_to_db_query = f'INSERT INTO ORDERS (username, startpoint, '\
                        f'endpoint, weight, cargo_type, start_date, price, '\
                        f'payment_type, carrier_username, status, '\
                        f'weight_limitations, mileage, reg_date) '\
                        f'VALUES ("{username}", '\
                        f'"{startpoint}", "{endpoint}", "{weight}", '\
                        f'"{cargo_type}", "{start_date}", "{price}", '\
                        f'"{payment_type}", "{carrier_username}", "{status}", '\
                        f'"{weight_limitations}", "{mileage}", "{reg_date}");'
    post_sql_query(insert_to_db_query)
