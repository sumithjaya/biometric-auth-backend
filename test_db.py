import os, psycopg
from dotenv import load_dotenv

load_dotenv()  # load .env file
url = os.environ.get("DATABASE_URL")
print("URL:", url)

try:
    dsn = url.replace("+psycopg", "")
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("select current_user, current_database(), inet_server_addr(), inet_server_port()")
            print("OK:", cur.fetchone())
except Exception as e:
    print("FAIL:", repr(e))
