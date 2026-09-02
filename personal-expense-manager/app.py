# Flask 웹서비스
from flask import Flask, render_template, request, redirect
# PostgreSQL 연결
import psycopg2
# matplotlib 연결
import matplotlib.pyplot as plt
#한글깨짐방지
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

app = Flask(__name__)


# DB 연결
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="personal_expense_db",
        user="postgres",
        password="MyPostgres123!"
    )

    return conn

    # 카테고리별 지출 그래프 생성
def create_category_chart(category_totals):

    categories = list(category_totals.keys())
    amounts = list(category_totals.values())

    plt.figure(figsize=(8, 4))

    plt.barh(categories, amounts)

    plt.xlabel("지출 금액")
    plt.ylabel("카테고리")
    plt.title("카테고리별 지출 순위")

    # 가장 큰 금액이 위로 오도록 정렬
    plt.gca().invert_yaxis()

    plt.tight_layout()

    # static 폴더에 이미지 저장
    plt.savefig("static/category_chart.png")

    plt.close()



# 대시보드 화면
# 대시보드 화면
@app.route("/")
def dashboard():

    conn = get_db_connection()
    cursor = conn.cursor()

    # 전체 지출 목록 조회
    cursor.execute("""
        SELECT id, date, category, description, amount
        FROM expenses
        ORDER BY id;
    """)

    expenses = cursor.fetchall()

    # 전체 합계 계산
    total = 0

    for expense in expenses:
        total += expense[4]

    # 지출 건수 계산
    count = len(expenses)

    # 가장 큰 지출 계산
    max_amount = 0

    for expense in expenses:
        if expense[4] > max_amount:
            max_amount = expense[4]

    # 카테고리별 합계 계산
    category_totals = {}

    for expense in expenses:
        category = expense[2]
        amount = expense[4]

        if category in category_totals:
            category_totals[category] += amount
        else:
            category_totals[category] = amount

    # 카테고리별 합계를 금액이 큰 순서로 정렬
    category_totals = dict(
        sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True
        )
    )

    # 카테고리별 지출 그래프 생성
    create_category_chart(category_totals)

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total=total,
        count=count,
        max_amount=max_amount,
        category_totals=category_totals
    )

# 지출 등록 화면
# 지출 등록
# 지출 등록
@app.route("/expense_add.html", methods=["GET", "POST"])
def expense_add():

    if request.method == "POST":

        date = request.form["date"].strip()
        category = request.form["category"].strip()
        description = request.form["description"].strip()
        amount_text = request.form["amount"].strip()

        # 빈 값 검증
        if not date or not category or not description:
            return "날짜, 카테고리, 내용은 비워 둘 수 없습니다."

        # 금액 정수 변환 검증
        try:
            amount = int(amount_text)
        except ValueError:
            return "금액은 정수로 입력해 주세요."

        # 금액 범위 검증
        if amount <= 0:
            return "금액은 0보다 큰 값으로 입력해 주세요."

        conn = get_db_connection()
        cursor = conn.cursor()

        # 지출 저장
        cursor.execute("""
            INSERT INTO expenses (
                date,
                category,
                description,
                amount
            )
            VALUES (%s, %s, %s, %s);
        """, (
            date,
            category,
            description,
            amount
        ))

        # DB에 실제 저장 확정
        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/expense_list.html")

    return render_template("expense_add.html")

# 지출 목록
# 지출 목록
@app.route("/expense_list.html")
def expense_list():

    selected_category = request.args.get("category", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # 카테고리별 조회
    if selected_category:
        cursor.execute("""
            SELECT id, date, category, description, amount
            FROM expenses
            WHERE category = %s
            ORDER BY id;
        """, (selected_category,))
    else:
        cursor.execute("""
            SELECT id, date, category, description, amount
            FROM expenses
            ORDER BY id;
        """)

    expenses = cursor.fetchall()

    # 전체 합계 계산
    total = 0

    for expense in expenses:
        total += expense[4]

    cursor.close()
    conn.close()

    return render_template(
        "expense_list.html",
        expenses=expenses,
        total=total,
        selected_category=selected_category
    )

    # 전체 합계 계산
    total = 0

    for expense in expenses:
        total += expense[4]

    cursor.close()
    conn.close()

    return render_template(
        "expense_list.html",
        expenses=expenses,
        total=total
    )

if __name__ == "__main__":
    app.run(debug=True)