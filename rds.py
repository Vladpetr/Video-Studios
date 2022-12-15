import pymysql
import config as config
conn = pymysql.connect(
    host= config.RDS_HOST, 
    port = config.RDS_PORT, 
    user = config.RDS_USER, 
    password = config.RDS_PASSWORD, 
    db = config.RDS_DB)

#Table Creation
def create_table():
    cursor=conn.cursor()
    table="""
    create table Users (name varchar(200),email varchar(200), password varchar(200))
    """
    cursor.execute(table)


def insert_user(name, email, password):
    cur=conn.cursor()
    cur.execute("INSERT INTO Users (name,email,password) VALUES (%s,%s,%s)", (name,email,password))
    conn.commit()

def get_users():
    cur=conn.cursor()
    cur.execute("SELECT * FROM Users")
    users = cur.fetchall()
    return users