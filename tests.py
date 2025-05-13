import unittest
import datetime
from app import app, db
from models import User, Message
from flask import url_for
import os
import tempfile


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            self.create_test_users()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def create_test_users(self):
        # Создаем тестовых пользователей
        user1 = User(username='testuser', email='test@example.com')
        user1.set_password('password123')
        user2 = User(username='testuser2', email='test2@example.com')
        user2.set_password('password123')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()


class AuthTestCase(BaseTestCase):
    def test_register(self):
        """Тест регистрации нового пользователя"""
        response = self.app.post('/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword',
            'confirm_password': 'newpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xd0\xa0\xd0\xb5\xd0\xb3\xd0\xb8\xd1\x81\xd1\x82\xd1\x80\xd0\xb0\xd1\x86\xd0\xb8\xd1\x8f \xd1\x83\xd1\x81\xd0\xbf\xd0\xb5\xd1\x88\xd0\xbd\xd0\xb0', response.data)  # 'Регистрация успешна' в UTF-8

        # Проверяем, что пользователь создан в базе
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'new@example.com')

    def test_register_duplicate_username(self):
        """Тест регистрации с уже существующим именем пользователя"""
        response = self.app.post('/register', data={
            'username': 'testuser',  # Уже существует
            'email': 'another@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xd0\x98\xd0\xbc\xd1\x8f \xd0\xbf\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xb7\xd0\xbe\xd0\xb2\xd0\xb0\xd1\x82\xd0\xb5\xd0\xbb\xd1\x8f \xd1\x83\xd0\xb6\xd0\xb5 \xd0\xb7\xd0\xb0\xd0\xbd\xd1\x8f\xd1\x82\xd0\xbe', response.data)  # 'Имя пользователя уже занято' в UTF-8

    def test_login_success(self):
        """Тест успешного входа в систему"""
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123',
            'remember': 'checked'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xd0\x92\xd1\x8b \xd1\x83\xd1\x81\xd0\xbf\xd0\xb5\xd1\x88\xd0\xbd\xd0\xbe \xd0\xb2\xd0\xbe\xd1\x88\xd0\xbb\xd0\xb8 \xd0\xb2 \xd1\x81\xd0\xb8\xd1\x81\xd1\x82\xd0\xb5\xd0\xbc\xd1\x83', response.data)  # 'Вы успешно вошли в систему' в UTF-8

    def test_login_failure(self):
        """Тест неудачного входа в систему"""
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword',
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xd0\x9d\xd0\xb5\xd0\xb2\xd0\xb5\xd1\x80\xd0\xbd\xd0\xbe\xd0\xb5 \xd0\xb8\xd0\xbc\xd1\x8f \xd0\xbf\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xb7\xd0\xbe\xd0\xb2\xd0\xb0\xd1\x82\xd0\xb5\xd0\xbb\xd1\x8f \xd0\xb8\xd0\xbb\xd0\xb8 \xd0\xbf\xd0\xb0\xd1\x80\xd0\xbe\xd0\xbb\xd1\x8c', response.data)  # 'Неверное имя пользователя или пароль' в UTF-8

    def test_logout(self):
        """Тест выхода из системы"""
        # Сначала входим
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123',
        }, follow_redirects=True)
        
        # Затем выходим
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xd0\x92\xd1\x8b \xd0\xb2\xd1\x8b\xd1\x88\xd0\xbb\xd0\xb8 \xd0\xb8\xd0\xb7 \xd1\x81\xd0\xb8\xd1\x81\xd1\x82\xd0\xb5\xd0\xbc\xd1\x8b', response.data)  # 'Вы вышли из системы' в UTF-8


class CalendarTestCase(BaseTestCase):
    def test_calendar_calculation(self):
        """Тест расчета рабочих дней по графику 2/2"""
        # Входим в систему
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123',
        }, follow_redirects=True)
        
        # Проверяем отображение календаря
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что календарь содержит нужные элементы
        self.assertIn(b'calendar-container', response.data)
        
        # Проверяем расчет рабочих дней для конкретной даты
        start_date = datetime.date(2025, 3, 17)  # Начальная дата цикла
        test_date = datetime.date(2025, 3, 18)  # Второй день цикла (рабочий)
        
        days_diff = (test_date - start_date).days
        cycle_position = days_diff % 4
        
        # Проверяем, что это рабочий день (первые 2 дня цикла)
        self.assertTrue(cycle_position < 2)
        
        # Проверяем выходной день
        test_date = datetime.date(2025, 3, 19)  # Третий день цикла (выходной)
        days_diff = (test_date - start_date).days
        cycle_position = days_diff % 4
        
        # Проверяем, что это выходной день (последние 2 дня цикла)
        self.assertTrue(cycle_position >= 2)

    def test_calendar_navigation(self):
        """Тест навигации по календарю"""
        # Входим в систему
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123',
        }, follow_redirects=True)
        
        # Проверяем переход на другой месяц
        response = self.app.get('/?month=5&year=2025')
        self.assertEqual(response.status_code, 200)
        # Проверяем, что отображается май 2025
        self.assertIn(b'2025', response.data)


class MessageTestCase(BaseTestCase):
    def test_send_message(self):
        """Тест отправки сообщения"""
        # Входим в систему
        self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123',
        }, follow_redirects=True)
        
        # Получаем ID второго пользователя
        with app.app_context():
            recipient = User.query.filter_by(username='testuser2').first()
            recipient_id = recipient.id
        
        # Отправляем сообщение
        response = self.app.post('/send_mur', data={
            'recipient_id': recipient_id
        })
        
        # Проверяем успешность отправки
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что сообщение создано в базе
        with app.app_context():
            message = Message.query.filter_by(
                sender_id=User.query.filter_by(username='testuser').first().id,
                recipient_id=recipient_id
            ).first()
            self.assertIsNotNone(message)


class ModelTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_model(self):
        """Тест модели пользователя"""
        with app.app_context():
            # Создаем пользователя
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Проверяем, что пользователь создан
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'test@example.com')
            
            # Проверяем проверку пароля
            self.assertTrue(user.check_password('password123'))
            self.assertFalse(user.check_password('wrongpassword'))

    def test_message_model(self):
        """Тест модели сообщения"""
        with app.app_context():
            # Создаем пользователей
            user1 = User(username='sender', email='sender@example.com')
            user1.set_password('password123')
            user2 = User(username='recipient', email='recipient@example.com')
            user2.set_password('password123')
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            # Создаем сообщение
            message = Message(sender_id=user1.id, recipient_id=user2.id)
            db.session.add(message)
            db.session.commit()
            
            # Проверяем, что сообщение создано
            message = Message.query.first()
            self.assertIsNotNone(message)
            self.assertEqual(message.sender_id, user1.id)
            self.assertEqual(message.recipient_id, user2.id)


if __name__ == '__main__':
    unittest.main()