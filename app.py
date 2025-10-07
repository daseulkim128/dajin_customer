
from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
import math

app = Flask(__name__)

# db 연결
engine = create_engine("mysql+pymysql://root:password@localhost:3306/dajin")

# db 연결 테스트 
#with engine.connect() as conn:
#    result = conn.execute(text("SELECT * FROM customer_info LIMIT 100"))
#    for row in result:
#        print(row)

# 한 페이지에 보여줄 데이터 수
PER_PAGE = 20

@app.route("/", methods=["GET"])
def index():
    query = request.args.get("query", "")
    field = request.args.get("field", "customer_nm")
    page = request.args.get("page", 1, type=int)
    PER_PAGE = 20
    offset = (page - 1) * PER_PAGE

    with engine.connect() as conn:
        if query:  # 검색어가 있으면 조건 추가
            count_sql = text(f"SELECT COUNT(*) FROM customer_info WHERE {field} LIKE :value")
            total_count = conn.execute(count_sql, {"value": f"%{query}%"}).scalar()
            sql = text(f"""
                SELECT customer_nm, customer_phone, customer_address 
                FROM customer_info 
                WHERE {field} LIKE :value 
                ORDER BY {field}
                LIMIT :limit OFFSET :offset
            """)
            results = conn.execute(sql, {"value": f"%{query}%", "limit": PER_PAGE, "offset": offset}).fetchall()
        else:  # 검색어 없으면 전체
            count_sql = text("SELECT COUNT(*) FROM customer_info")
            total_count = conn.execute(count_sql).scalar()
            sql = text("SELECT customer_nm, customer_phone, customer_address FROM customer_info ORDER BY customer_nm LIMIT :limit OFFSET :offset")
            results = conn.execute(sql, {"limit": PER_PAGE, "offset": offset}).fetchall()

    total_pages = math.ceil(total_count / PER_PAGE)
    start_page = max(1, page - 5)
    end_page = min(total_pages, page + 4)

    return render_template(
        "index.html",
        results=results,
        query=query,
        field=field,
        page=page,
        total_pages=total_pages,
        start_page=start_page,
        end_page=end_page
    )

# WSGI 서버용 진입점
if __name__ == "__main__":
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)

    
# exe 파일 사용시 
# if __name__ == "__main__":
#     import webbrowser
#     import threading

#     # 서버를 백그라운드에서 켜고 브라우저 자동 오픈
#     def open_browser():
#         webbrowser.open("http://127.0.0.1:5000")

#     threading.Timer(1, open_browser).start()
#     app.run(debug=False)  # 배포용은 debug=False