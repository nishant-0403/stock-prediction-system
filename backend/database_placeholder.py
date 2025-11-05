import os
import mysql.connector

def get_conn():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'mysql'),
        user=os.getenv('MYSQL_USER', 'stockuser'),
        password=os.getenv('MYSQL_PASSWORD', 'stockpass'),
        database=os.getenv('MYSQL_DATABASE', 'stockapp'),
    )


