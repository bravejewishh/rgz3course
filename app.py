from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Employee
from config import Config
from datetime import datetime
import re

app = Flask(__name__)
app.config.from_object(Config)

# Инициализация
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Данные студента (должны быть на каждой странице)
STUDENT_INFO = {
    'full_name': 'Пенькова Полина Александровна',
    'group': 'ФБИ-34'
}

# ================== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ==================
def init_database():
    """Инициализация базы данных с тестовыми данными"""
    with app.app_context():
        # Создаём таблицы если их нет
        db.create_all()
        
        # Создаём администратора (для отчёта)
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('admin123')  # Пароль: admin123
            db.session.add(admin)
            print("Администратор создан: логин=admin, пароль=admin123")
        
        # Создаём 100+ тестовых сотрудников
        if Employee.query.count() < 100:
            # Простой способ создать тестовые данные
            positions = ['Программист', 'Тестировщик', 'Аналитик', 'Менеджер', 'Дизайнер']
            genders = ['муж', 'жен']
            
            import random
            from datetime import date, timedelta
            
            for i in range(120):
                # Генерируем тестовые данные
                gender = random.choice(genders)
                if gender == 'муж':
                    names = ['Иванов Иван', 'Петров Пётр', 'Сидоров Алексей', 'Кузнецов Дмитрий']
                else:
                    names = ['Иванова Анна', 'Петрова Мария', 'Сидорова Елена', 'Кузнецова Ольга']
                
                employee = Employee(
                    full_name=random.choice(names),
                    position=random.choice(positions),
                    gender=gender,
                    phone=f'+7{random.randint(900,999)}{random.randint(1000000,9999999)}',
                    email=f'employee{i}@company.com',
                    on_probation=random.choice([True, False]),
                    hire_date=date.today() - timedelta(days=random.randint(0, 365*3))
                )
                db.session.add(employee)
            
            db.session.commit()
            print(f"Создано {Employee.query.count()} тестовых сотрудников")

# ================== ГЛАВНЫЕ МАРШРУТЫ ==================

@app.route('/')
def index():
    """Главная страница - список сотрудников"""
    # Пагинация: показываем по 20 сотрудников
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Поиск
    search_query = request.args.get('search', '')
    search_field = request.args.get('field', 'full_name')
    
    if search_query:
        employees_query = Employee.search_by_field(search_field, search_query)
    else:
        employees_query = Employee.query
    
    # Сортировка
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('order', 'asc')
    
    if hasattr(Employee, sort_by):
        column = getattr(Employee, sort_by)
        if sort_order == 'asc':
            employees_query = employees_query.order_by(column.asc())
        else:
            employees_query = employees_query.order_by(column.desc())
    
    # Пагинация
    pagination = employees_query.paginate(page=page, per_page=per_page, error_out=False)
    employees = pagination.items
    
    return render_template('index.html',
                         employees=employees,
                         pagination=pagination,
                         student=STUDENT_INFO,
                         search_query=search_query,
                         search_field=search_field,
                         sort_by=sort_by,
                         sort_order=sort_order)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Вы успешно вошли в систему', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль', 'error')
    
    return render_template('login.html', student=STUDENT_INFO)

@app.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/employee/new', methods=['GET', 'POST'])
@login_required
def new_employee():
    """Добавление нового сотрудника"""
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            full_name = request.form.get('full_name')
            position = request.form.get('position')
            gender = request.form.get('gender')
            phone = request.form.get('phone')
            email = request.form.get('email')
            on_probation = 'on_probation' in request.form
            hire_date_str = request.form.get('hire_date')
            
            # Простая валидация
            errors = []
            if not full_name or len(full_name.strip()) < 2:
                errors.append("ФИО должно содержать минимум 2 символа")
            if not position:
                errors.append("Укажите должность")
            if gender not in ['муж', 'жен']:
                errors.append("Укажите пол")
            if not phone:
                errors.append("Укажите телефон")
            if not email or '@' not in email:
                errors.append("Некорректный email")
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('employee_form.html', student=STUDENT_INFO)
            
            # Парсим дату
            hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
            
            # Создаём сотрудника
            employee = Employee(
                full_name=full_name,
                position=position,
                gender=gender,
                phone=phone,
                email=email,
                on_probation=on_probation,
                hire_date=hire_date
            )
            
            db.session.add(employee)
            db.session.commit()
            
            flash('Сотрудник успешно добавлен', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении: {str(e)}', 'error')
    
    return render_template('employee_form.html', student=STUDENT_INFO, employee=None)

@app.route('/employee/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    """Редактирование сотрудника"""
    employee = Employee.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            employee.full_name = request.form.get('full_name')
            employee.position = request.form.get('position')
            employee.gender = request.form.get('gender')
            employee.phone = request.form.get('phone')
            employee.email = request.form.get('email')
            employee.on_probation = 'on_probation' in request.form
            
            hire_date_str = request.form.get('hire_date')
            if hire_date_str:
                employee.hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
            
            db.session.commit()
            flash('Данные сотрудника обновлены', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении: {str(e)}', 'error')
    
    return render_template('employee_form.html', student=STUDENT_INFO, employee=employee)

@app.route('/employee/<int:id>/delete', methods=['POST'])
@login_required
def delete_employee(id):
    """Удаление сотрудника"""
    employee = Employee.query.get_or_404(id)
    
    try:
        db.session.delete(employee)
        db.session.commit()
        flash('Сотрудник удалён', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'error')
    
    return redirect(url_for('index'))



# Инициализация базы данных при старте
with app.app_context():
    init_database()

if __name__ == '__main__':
    app.run(debug=True)