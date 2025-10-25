from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg://karan1:karan1@localhost:5432/karandb1")
chat_id = 6057675634

# To get chat_id
"""
1. open terminal -> psql -U karan1 -d karandb1 -h localhost
2. password: karan1
3. run the query:
SELECT chat_id, chat_type, title, user_id, created_at
FROM chats
ORDER BY created_at DESC
LIMIT 5;
4. To get Table schema:
\d
"""
with engine.connect() as conn:
    res = conn.execute(text("""
        SELECT role, content, created_at
        FROM chat_messages
        WHERE chat_id = :cid
        ORDER BY created_at DESC
        LIMIT 10
    """), {"cid": chat_id})
    for row in res:
        print(row)
