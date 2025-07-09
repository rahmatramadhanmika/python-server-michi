import mysql.connector
from mysql.connector import Error

def test():
    connection = None
    try:
        # Connect to the MySQL server
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='michi_robot',
            port=3310
        )

        if connection.is_connected():
            db_info = connection.get_server_info()
            print("Connected to MySQL Server version", db_info)

    except Error as e:
        print("Error while connecting to MySQL", e)
        
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("MySQL connection is closed")

if __name__ == "__main__":
    test()