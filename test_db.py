import psycopg2
import config

# connect to db
conn = psycopg2.connect(host=config.DB_HOST, database=config.DB_NAME,
                        user=config.DB_USER, password=config.DB_PASSWORD)

print("Connected to database")
# cursor
cur = conn.cursor()

print("Cursor created")


cur.execute("insert into token_table values ('1', '10')")
conn.commit()

cur.execute("select * from token_table")
print("Executed query")

rows = cur.fetchall()
print(len(rows))
for r in rows:
    print(f'user_id {r[0]} access_token {r[1]}')

cur.close()

# close the connection
conn.close()
