
import os 
from flask import Flask, render_template, request
from sqlalchemy import create_engine, text, Column, Integer, String, MetaData, Table
import math

app = Flask(__name__)

print("현재 작업 디렉토리:", os.getcwd())

# SQLite 경로 지정
sqlite_path = os.path.join(os.getcwd(), "dajin.db")

# 🔹 SQLite 파일이 없을 때만 MariaDB에서 복사
if not os.path.exists(sqlite_path):
    print(f"SQLite DB 없음 → MariaDB에서 데이터 복사 시작 ({sqlite_path})")

    # SQLite 엔진 (파일이 실제 생성되기 전)
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})

    # 테이블 정의
    metadata = MetaData()
    customer_info = Table(
        'customer_info', metadata,
        Column('id', Integer, primary_key=True),
        Column('customer_nm', String),
        Column('customer_phone', String),
        Column('customer_address', String)
    )
    metadata.create_all(sqlite_engine)

    # MariaDB → SQLite 데이터 복사
    from sqlalchemy import create_engine as create_mysql_engine
    mysql_engine = create_mysql_engine("mysql+pymysql://root:password@localhost:3306/dajin")
    
    with mysql_engine.connect() as src_conn, sqlite_engine.connect() as dest_conn:
        result = src_conn.execute(text(
            "SELECT customer_nm, customer_phone, customer_address FROM customer_info"
        ))
        for row in result:
            dest_conn.execute(
                customer_info.insert().values(
                    customer_nm=row[0],
                    customer_phone=row[1],
                    customer_address=row[2]
                )
            )
        dest_conn.commit()
    print("✅ 데이터 마이그레이션 완료")
else:
    print(f"SQLite DB 존재 → 마이그레이션 건너뜀 ({sqlite_path})")

# 이후에는 이 SQLite를 사용
sqlite_engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})

# 한 페이지에 보여줄 데이터 수
PER_PAGE = 20

@app.route("/", methods=["GET"])
def index():
    query = request.args.get("query", "")
    field = request.args.get("field", "customer_nm")
    page = request.args.get("page", 1, type=int)
    PER_PAGE = 20
    offset = (page - 1) * PER_PAGE

    with sqlite_engine.connect() as conn:
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
    import os
    port = int(os.environ.get("PORT", 5000))
    serve(app, host='0.0.0.0', port=port)


# exe 파일 사용시 
# if __name__ == "__main__":
#     import webbrowser
#     import threading

#     # 서버를 백그라운드에서 켜고 브라우저 자동 오픈
#     def open_browser():
#         webbrowser.open("http://127.0.0.1:5000")

#     threading.Timer(1, open_browser).start()
#     app.run(debug=False)  # 배포용은 debug=False