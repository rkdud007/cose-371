import psycopg2

connect = psycopg2.connect("dbname=tutorial user=postgres password=_____")
cur = connect.cursor()  # create cursor

cur.execute("CREATE TABLE users (id varchar(20) not null, password varchar(20) not null, primary key(id));")
cur.execute("INSERT INTO users VALUES('dbstudent0', '0000');")

id = 'database'
password = 'postgres'
cur.execute("INSERT INTO users VALUES('{}', '{}');".format(id, password))

connect.commit()  # you must use connect.commit() when write data to PostgreSQL

