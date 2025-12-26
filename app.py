# app.py
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, session, jsonify, render_template

app = Flask(__name__)
app.secret_key = 'p_penkova_fbi34_secret'

# === подключение к БД — как на скриншоте ===
def get_db():
    conn = psycopg2.connect(
        host='127.0.0.1',
        database='hr_db',
        user='hr_user',
        password='hr_pass'
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cur

def close_db(conn, cur):
    conn.commit()
    cur.close()
    conn.close()

# === роуты ===
@app.route('/')
def index():
    return render_template('index.html', fio='пенькова полина александровна', group='фби-34')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')

    conn, cur = get_db()
    cur.execute('SELECT id FROM users WHERE login = %s AND password_hash = %s', 
                (login, f'plain:{password}'))
    user = cur.fetchone()
    close_db(conn, cur)

    if user:
        session['user_id'] = user['id']
        return jsonify({'ok': True})

    return jsonify({'error': 'неверный логин или пароль'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'ok': True})

@app.route('/api/employees')
def get_employees():
    search = request.args.get('search', '').lower()
    sort = request.args.get('sort', 'fio')
    order = request.args.get('order', 'asc')
    try:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 20))
    except:
        offset, limit = 0, 20

    if sort not in ['fio', 'position', 'gender', 'hire_date']:
        sort = 'fio'
    if order not in ['asc', 'desc']:
        order = 'asc'

    conn, cur = get_db()

    where, params = "", []
    if search:
        where = """WHERE
            LOWER(fio) LIKE %s OR
            LOWER(position) LIKE %s OR
            LOWER(phone) LIKE %s OR
            LOWER(email) LIKE %s"""
        term = f'%{search}%'
        params = [term] * 4

    query = f"SELECT * FROM employees {where} ORDER BY {sort} {order} LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    cur.execute(query, params)
    rows = cur.fetchall()
    close_db(conn, cur)

    return jsonify([dict(row) for row in rows])

@app.route('/api/employees', methods=['POST'])
def add_employee():
    if 'user_id' not in session:
        return jsonify({'error': 'не авторизован'}), 403

    data = request.get_json()
    fio = data.get('fio', '').strip()
    position = data.get('position', '').strip()
    gender = data.get('gender')
    hire_date = data.get('hire_date')

    if not fio or not position or not hire_date or gender not in ('м', 'ж'):
        return jsonify({'error': 'заполните фио, должность, дату; пол — м/ж'}), 400

    conn, cur = get_db()
    cur.execute('''
        INSERT INTO employees (fio, position, gender, phone, email, probation, hire_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (
        fio, position, gender,
        data.get('phone', ''),
        data.get('email', ''),
        data.get('probation', False),
        hire_date
    ))
    conn.commit()
    cur.execute("SELECT currval('employees_id_seq')")
    new_id = cur.fetchone()['currval']
    close_db(conn, cur)

    return jsonify({
        'id': new_id, 'fio': fio, 'position': position, 'gender': gender,
        'phone': data.get('phone', ''), 'email': data.get('email', ''),
        'probation': data.get('probation', False), 'hire_date': hire_date
    }), 201

@app.route('/api/employees/<int:id>', methods=['PUT'])
def update_employee(id):
    if 'user_id' not in session:
        return jsonify({'error': 'не авторизован'}), 403

    data = request.get_json()
    fio = data.get('fio', '').strip()
    position = data.get('position', '').strip()
    gender = data.get('gender')
    hire_date = data.get('hire_date')

    if not fio or not position or not hire_date or gender not in ('м', 'ж'):
        return jsonify({'error': 'заполните фио, должность, дату; пол — м/ж'}), 400

    conn, cur = get_db()
    cur.execute('''
        UPDATE employees SET
            fio = %s, position = %s, gender = %s, phone = %s, email = %s, probation = %s, hire_date = %s
        WHERE id = %s
    ''', (
        fio, position, gender,
        data.get('phone', ''),
        data.get('email', ''),
        data.get('probation', False),
        hire_date,
        id
    ))
    close_db(conn, cur)

    return jsonify({
        'id': id, 'fio': fio, 'position': position, 'gender': gender,
        'phone': data.get('phone', ''), 'email': data.get('email', ''),
        'probation': data.get('probation', False), 'hire_date': hire_date
    })

@app.route('/api/employees/<int:id>', methods=['DELETE'])
def delete_employee(id):
    if 'user_id' not in session:
        return jsonify({'error': 'не авторизован'}), 403

    conn, cur = get_db()
    cur.execute('DELETE FROM employees WHERE id = %s', (id,))
    close_db(conn, cur)
    return '', 204
