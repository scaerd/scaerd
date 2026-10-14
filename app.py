import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
# Секретный ключ для защиты сессии кассира
app.secret_key = "super_secret_school_key_123" 

# Логин и пароль кассира для входа в панель управления
ADMIN_LOGIN = "cashier"
ADMIN_PASSWORD = "super_password_2026"

def init_db():
    """Функция, которая автоматически создает базу данных при первом запуске сайта"""
    conn = sqlite3.connect("canteen.db")
    cursor = conn.cursor()
    # Создаем таблицу для меню столовой
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            count INTEGER NOT NULL,
            price REAL NOT NULL
        )
    """)
    # Создаем таблицу для очереди (сюда потом будет отправлять данные нейросеть)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY,
            people_count INTEGER NOT NULL,
            wait_time INTEGER NOT NULL
        )
    """)
    
    # Заполняем меню тестовыми блюдами, если сайт запускается впервые
    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone() == 0:
        dishes = [
            ("Медовик", 30, 85.0),
            ("Пицца школьная", 15, 70.0),
            ("Сосиска в тесте", 40, 65.0),
            ("Пюре с котлетой", 20, 120.0)
        ]
        cursor.executemany("INSERT INTO menu (name, count, price) VALUES (?, ?, ?)", dishes)
        cursor.execute("INSERT INTO queue (id, people_count, wait_time) VALUES (1, 0, 0)")
        conn.commit()
    conn.close()

# Запускаем создание базы данных при старте программы
init_db()

@app.route("/")
def index():
    """Главная страница сайта (для учеников)"""
    conn = sqlite3.connect("canteen.db")
    # Добавляем строку ниже, чтобы к данным можно было обращаться по именам (item['name']), а не по индексам (item[0])
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # Берем актуальное меню
    try:
        cursor.execute("SELECT id, name, count, price FROM menu")
        menu_items = cursor.fetchall()
    except sqlite3.OperationalError as e:
        # Если в вашей базе данных 'canteen.db' все еще нет колонки 'count', этот блок сам её создаст
        if "no such column: count" in str(e):
            cursor.execute("ALTER TABLE menu ADD COLUMN count INTEGER DEFAULT 0")
            conn.commit()
            cursor.execute("SELECT id, name, count, price FROM menu")
            menu_items = cursor.fetchall()
        else:
            menu_items = []
   
    # Берем данные об очереди
    cursor.execute("SELECT people_count, wait_time FROM queue WHERE id=1")
    queue_data = cursor.fetchone()
    conn.close()

    # ВАЖНО: Передаем данные в HTML-файл
    return render_template("index.html", menu=menu_items, queue=queue_data)





@app.route("/admin", methods=["GET", "POST"])
def admin():
    """Страница кассира (авторизация и изменение количества еды)"""
    if request.method == "POST":
        # Проверяем, если кассир пытается войти в систему
        if "login_button" in request.form:
            # 1. Получаем имя пользователя из формы
            username = request.form.get("username")
            
            # 2. Получаем пароль и безопасно убираем пробелы
            password_raw = request.form.get("password")
            password = password_raw.strip() if password_raw else ""
            
            if username == ADMIN_LOGIN and password == ADMIN_PASSWORD:
                session["logged_in"] = True
                return redirect(url_for("admin"))
            else:
                return "Неверный логин или пароль! Вернитесь назад и попробуйте снова."



        # Если кассир уже вошел и сохраняет новые остатки блюд
        if session.get("logged_in"):
            conn = sqlite3.connect("canteen.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM menu")
            all_ids = cursor.fetchall()
            for (dish_id,) in all_ids:
                new_count = request.form.get(f"count_{dish_id}")
                if new_count is not None:
                    cursor.execute("UPDATE menu SET count=? WHERE id=?", (int(new_count), dish_id))
            
            conn.commit()
            conn.close()
            return redirect(url_for("admin"))

    # Если кассир НЕ вошел, показываем ему окно ввода логина и пароля
    if not session.get("logged_in"):
        return render_template("admin.html", logged_in=False)

    # Если кассир успешно авторизован, показываем меню для редактирования
    conn = sqlite3.connect("canteen.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, count, price FROM menu")
    menu_items = cursor.fetchall()
    conn.close()
    
    return render_template("admin.html", logged_in=True, menu=menu_items)

@app.route("/logout")
def logout():
    """Кнопка выхода для кассира"""
    session.pop("logged_in", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    # host='0.0.0.0' открывает доступ к сайту по школьному Wi-Fi без интернета
    app.run(host="0.0.0.0", port=5000, debug=True)
