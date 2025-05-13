import unittest
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import app, db
from models import User


class FunctionalTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Настройка Flask-приложения для тестирования
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SERVER_NAME'] = 'localhost:5000'
        cls.app_context = app.app_context()
        cls.app_context.push()
        
        # Создаем тестовую базу данных
        db.create_all()
        
        # Запускаем Flask-приложение в отдельном потоке
        import threading
        threading.Thread(target=app.run, kwargs={'use_reloader': False}).start()
        time.sleep(1)  # Даем время на запуск сервера
        
        # Настраиваем Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Запуск в безголовом режиме
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)
        
        # Создаем тестового пользователя
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def test_login_and_view_calendar(self):
        """Функциональный тест входа в систему и просмотра календаря"""
        # Открываем страницу входа
        self.driver.get('http://localhost:5000/login')
        
        # Проверяем заголовок страницы
        self.assertIn('Вход', self.driver.title)
        
        # Вводим данные для входа
        username_input = self.driver.find_element(By.NAME, 'username')
        password_input = self.driver.find_element(By.NAME, 'password')
        submit_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        
        username_input.send_keys('testuser')
        password_input.send_keys('password123')
        submit_button.click()
        
        # Ждем перенаправления на страницу календаря
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'calendar-container'))
        )
        
        # Проверяем, что мы на странице календаря
        self.assertIn('Календарь', self.driver.title)
        
        # Проверяем наличие элементов календаря
        calendar_container = self.driver.find_element(By.CLASS_NAME, 'calendar-container')
        self.assertIsNotNone(calendar_container)
        
        # Проверяем наличие выбора месяца и года
        month_select = self.driver.find_element(By.ID, 'month-select')
        year_select = self.driver.find_element(By.ID, 'year-select')
        self.assertIsNotNone(month_select)
        self.assertIsNotNone(year_select)

    def test_register_new_user(self):
        """Функциональный тест регистрации нового пользователя"""
        # Открываем страницу регистрации
        self.driver.get('http://localhost:5000/register')
        
        # Проверяем заголовок страницы
        self.assertIn('Регистрация', self.driver.title)
        
        # Вводим данные для регистрации
        username_input = self.driver.find_element(By.NAME, 'username')
        email_input = self.driver.find_element(By.NAME, 'email')
        password_input = self.driver.find_element(By.NAME, 'password')
        confirm_password_input = self.driver.find_element(By.NAME, 'confirm_password')
        submit_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
        
        username_input.send_keys('newuser')
        email_input.send_keys('new@example.com')
        password_input.send_keys('newpassword')
        confirm_password_input.send_keys('newpassword')
        submit_button.click()
        
        # Ждем перенаправления на страницу входа
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        
        # Проверяем, что мы на странице входа
        self.assertIn('Вход', self.driver.title)
        
        # Проверяем наличие сообщения об успешной регистрации
        flash_message = self.driver.find_element(By.CLASS_NAME, 'alert-success')
        self.assertIn('Регистрация успешна', flash_message.text)


# Примечание: для запуска этих тестов требуется установленный Selenium и ChromeDriver
# pip install selenium
# Также необходимо добавить selenium в requirements.txt
if __name__ == '__main__':
    unittest.main()