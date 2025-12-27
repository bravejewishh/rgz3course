from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Модель пользователя (кадровика) - только логин и пароль"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    def set_password(self, password):
        # Простая валидация: только латинские буквы и цифры
        # ИСПРАВЛЕНО: убрали лишнюю переменную 'c'
        valid_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?'
        
        # Проверяем каждый символ
        for char in password:
            if char not in valid_chars:
                raise ValueError("Пароль должен содержать только латинские буквы, цифры и знаки препинания")
        
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employee(db.Model):
    """Модель сотрудника"""
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # "муж" или "жен"
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    on_probation = db.Column(db.Boolean, default=False)
    hire_date = db.Column(db.Date, nullable=False, default=datetime.date.today)
    
    # Для поиска (простой LIKE поиск)
    @staticmethod
    def search_by_field(field, query):
        if field == 'full_name':
            return Employee.query.filter(Employee.full_name.ilike(f'%{query}%'))
        elif field == 'position':
            return Employee.query.filter(Employee.position.ilike(f'%{query}%'))
        elif field == 'phone':
            return Employee.query.filter(Employee.phone.ilike(f'%{query}%'))
        elif field == 'email':
            return Employee.query.filter(Employee.email.ilike(f'%{query}%'))
        elif field == 'gender':
            return Employee.query.filter(Employee.gender.ilike(f'%{query}%'))
        elif field == 'on_probation':
            # Для поиска по испытательному сроку
            # Пользователь может ввести "да", "yes", "true", "1" или "нет", "no", "false", "0"
            query_lower = query.lower()
            if query_lower in ['да', 'yes', 'true', '1']:
                return Employee.query.filter(Employee.on_probation == True)
            elif query_lower in ['нет', 'no', 'false', '0']:
                return Employee.query.filter(Employee.on_probation == False)
            return Employee.query
        return Employee.query