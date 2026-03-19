import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="jovin",
        password="jovin",
        database="hotelmanagement"
    )
    return conn
