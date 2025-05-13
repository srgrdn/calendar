import unittest
import datetime
from app import app, db
from models import User, Message
import os
import tempfile


class IntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            # Создаем тестового пользователя
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def test_full_user_flow(self):
        """Интеграционный тест полного пользовательского сценария"""
        # 1. Регистрация нового пользователя
        response = self.app.post('/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword',
            'confirm_password': 'newpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xd0\xa0\xd0\xb5\xd0\xb3\xd0\xb8\xd1\x81\xd1\x82\xd1\x80\xd0\xb0\xd1\x86\xd0\xb8\xd1\x8f \xd1\x83\xd1\x81\xd0\xbf\xd0\xb5\xd1\x88\xd0\xbd\xd0\xb0', response.data)  # 'Регистрация успешна' в UTF-8

        # 2. Вход в систему
        response = self.app.post('/login', data={
            'username': 'newuser',
            'password': 'newpassword',
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xd0\x92\xd1\x8b \xd1\x83\xd1\x81\xd0\xbf\xd0\xb5\xd1\x88\xd0\xbd\xd0\xbe \xd0\xb2\xd0\xbe\xd1\x88\xd0\xbb\xd0\xb8 \xd0\xb2 \xd1\x81\xd0\xb8\xd1\x81\xd1\x82\xd0\xb5\xd0\xbc\xd1\x83', response.data)  # 'Вы успешно вошли в систему' в UTF-8

        # 3. Просмотр календаря
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'calendar-container', response.data)

        # 4. Переход на другой месяц
        response = self.app.get('/?month=5&year=2025')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'2025', response.data)

        # 5. Выход из системы
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'\xd0\x92\xd1\x8b \xd0\xb2\xd1\x8b\xd1\x88\xd0\xbb\xd0\xb8 \xd0\xb8\xd0\xb7 \xd1\x81\xd0\xb8\xd1\x81\xd1\x82\xd0\xb5\xd0\xbc\xd1\x8b', response.data)  # 'Вы вышли из системы' в UTF-8

    def test_calendar_and_chat_integration(self):
        """Интеграционный тест взаимодействия календаря и чата"""
        # Создаем второго пользователя для тестирования чата
        with app.app_context():
            user2 = User(username='testuser2', email='test2@example.com')
            user2.set_password('password123')
            db.session.add(user2)
            db.session.commit()

        # 1. Вход в систему
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password123',
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 2. Просмотр календаря
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'calendar-container', response.data)

        # 3. Переход в чат
        response = self.app.get('/chat')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'chat-container', response.data)

        # 4. Отправка сообщения
        with app.app_context():
            recipient_id = User.query.filter_by(username='testuser2').first().id

        response = self.app.post('/send_mur', data={
            'recipient_id': recipient_id
        })
        self.assertEqual(response.status_code, 200)

        # Проверяем, что сообщение создано в базе
        with app.app_context():
            message = Message.query.filter_by(
                sender_id=User.query.filter_by(username='testuser').first().id,
                recipient_id=recipient_id
            ).first()
            self.assertIsNotNone(message)


if __name__ == '__main__':
    unittest.main()
