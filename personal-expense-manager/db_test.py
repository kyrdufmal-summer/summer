# PostgreSQL 연결 테스트
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="personal_expense_db",
    user="postgres",
    password="MyPostgres123!"
)

# 지출 목록 조회
cursor = conn.cursor()

cursor.execute("""
    SELECT id, date, category, description, amount
    FROM expenses
    ORDER BY id;
""")

expenses = cursor.fetchall()

print("DB 연결 성공")
print("지출 건수:", len(expenses))

for expense in expenses[:5]:
    print(expense)

cursor.close()
conn.close()