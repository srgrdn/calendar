import pytest
import datetime
from app import app, db
from models import User, Message
from flask import url_for


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def auth_client(client):
    # Создаем тестового пользователя
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

    return client


@pytest.fixture
def logged_in_client(auth_client):
    # Входим в систему
    auth_client.post('/login', data={
        'username': 'testuser',
        'password': 'password123',
    }, follow_redirects=True)

    return auth_client


class TestAuth:
    def test_register(self, client):
        """Тест регистрации нового пользователя"""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword',
            'confirm_password': 'newpassword'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'\xd0\xa0\xd0\xb5\xd0\xb3\xd0\xb8\xd1\x81\xd1\x82\xd1\x80\xd0\xb0\xd1\x86\xd0\xb8\xd1\x8f \xd1\x83\xd1\x81\xd0\xbf\xd0\xb5\xd1\x88\xd0\xbd\xd0\xb0' in response.data  # 'Регистрация успешна' в UTF-8

        # Проверяем, что пользователь создан в базе
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.email == 'new@example.com'

    def test_login_success(self, auth_client):
        """Тест успешного входа в систему"""
        response = auth_client.post('/login', data={
            'username': 'testuser',
            'password': 'password123',
            'remember': 'checked'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'\xd0\x92\xd1\x8b \xd1\x83\xd1\x81\xd0\xbf\xd0\xb5\xd1\x88\xd0\xbd\xd0\xbe \xd0\xb2\xd0\xbe\xd1\x88\xd0\xbb\xd0\xb8 \xd0\xb2 \xd1\x81\xd0\xb8\xd1\x81\xd1\x82\xd0\xb5\xd0\xbc\xd1\x83' in response.data  # 'Вы успешно вошли в систему' в UTF-8

    def test_login_failure(self, auth_client):
        """Тест неудачного входа в систему"""
        response = auth_client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'\xd0\x9d\xd0\xb5\xd0\xb2\xd0\xb5\xd1\x80\xd0\xbd\xd0\xbe\xd0\xb5 \xd0\xb8\xd0\xbc\xd1\x8f \xd0\xbf\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xb7\xd0\xbe\xd0\xb2\xd0\xb0\xd1\x82\xd0\xb5\xd0\xbb\xd1\x8f \xd0\xb8\xd0\xbb\xd0\xb8 \xd0\xbf\xd0\xb0\xd1\x80\xd0\xbe\xd0\xbb\xd1\x8c' in response.data  # 'Неверное имя пользователя или пароль' в UTF-8

    def test_logout(self, logged_in_client):
        """Тест выхода из системы"""
        response = logged_in_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'\xd0\x92\xd1\x8b \xd0\xb2\xd1\x8b\xd1\x88\xd0\xbb\xd0\xb8 \xd0\xb8\xd0\xb7 \xd1\x81\xd0\xb8\xd1\x81\xd1\x82\xd0\xb5\xd0\xbc\xd1\x8b' in response.data  # 'Вы вышли из системы' в UTF-8


class TestCalendar:
    def test_calendar_display(self, logged_in_client):
        """Тест отображения календаря"""
        response = logged_in_client.get('/')
        assert response.status_code == 200
        assert b'calendar-container' in response.data

    def test_calendar_navigation(self, logged_in_client):
        """Тест навигации по календарю"""
        response = logged_in_client.get('/?month=5&year=2025')
        assert response.status_code == 200
        assert b'2025' in response.data

    def test_calendar_calculation(self):
        """Тест расчета рабочих дней по графику 2/2"""
        start_date = datetime.date(2025, 3, 17)  # Начальная дата цикла

        # Проверяем рабочие дни (первые 2 дня цикла)
        for i in range(2):
            test_date = start_date + datetime.timedelta(days=i)
            days_diff = (test_date - start_date).days
            cycle_position = days_diff % 4
            assert cycle_position < 2

        # Проверяем выходные дни (последние 2 дня цикла)
        for i in range(2, 4):
            test_date = start_date + datetime.timedelta(days=i)
            days_diff = (test_date - start_date).days
            cycle_position = days_diff % 4
            assert cycle_position >= 2


class TestMessage:
    def test_send_message(self, logged_in_client):
        """Тест отправки сообщения"""
        # Создаем второго пользователя
        with app.app_context():
            user2 = User(username='testuser2', email='test2@example.com')
            user2.set_password('password123')
            db.session.add(user2)
            db.session.commit()
            recipient_id = user2.id

        # Отправляем сообщение
        response = logged_in_client.post('/send_mur', data={
            'recipient_id': recipient_id
        })

        # Проверяем успешность отправки
        assert response.status_code == 200

        # Проверяем, что сообщение создано в базе
        with app.app_context():
            message = Message.query.filter_by(
                sender_id=User.query.filter_by(username='testuser').first().id,
                recipient_id=recipient_id
            ).first()
            assert message is not None


class TestModels:
    def test_user_model(self, client):
        """Тест модели пользователя"""
        with app.app_context():
            # Создаем пользователя
            user = User(username='testuser', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

            # Проверяем, что пользователь создан
            user = User.query.filter_by(username='testuser').first()
            assert user is not None
            assert user.email == 'test@example.com'

            # Проверяем проверку пароля
            assert user.check_password('password123')
            assert not user.check_password('wrongpassword')

    def test_message_model(self, client):
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
            assert message is not None
            assert message.sender_id == user1.id
            assert message.recipient_id == user2.id
