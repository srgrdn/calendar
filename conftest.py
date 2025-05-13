import pytest
from app import app, db
from models import User


@pytest.fixture(scope='session')
def app_context():
    """Создает контекст приложения для тестов"""
    with app.app_context():
        yield


@pytest.fixture(scope='function')
def test_app():
    """Настраивает приложение для тестирования"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture(scope='function')
def test_db(test_app, app_context):
    """Создает тестовую базу данных"""
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()


@pytest.fixture(scope='function')
def test_user(test_db):
    """Создает тестового пользователя"""
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def test_client(test_app):
    """Создает тестовый клиент Flask"""
    with test_app.test_client() as client:
        yield client