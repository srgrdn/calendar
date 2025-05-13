#!/usr/bin/env python
import unittest
import coverage
import sys
import os

# Настройка покрытия кода
cov = coverage.Coverage(
    branch=True,
    include=['app.py', 'models.py', 'config.py'],
    omit=['tests.py', 'test_*.py', 'integration_tests.py', 'functional_tests.py', 'run_tests*.py']
)

# Запуск измерения покрытия
cov.start()

# Импорт тестов
from tests import AuthTestCase, CalendarTestCase, MessageTestCase, ModelTestCase
from integration_tests import IntegrationTestCase


def run_tests_with_coverage():
    # Создаем загрузчик тестов
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Добавляем тесты в набор
    suite.addTests(loader.loadTestsFromTestCase(AuthTestCase))
    suite.addTests(loader.loadTestsFromTestCase(CalendarTestCase))
    suite.addTests(loader.loadTestsFromTestCase(MessageTestCase))
    suite.addTests(loader.loadTestsFromTestCase(ModelTestCase))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationTestCase))

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Останавливаем измерение покрытия
    cov.stop()
    cov.save()

    # Выводим отчет о покрытии
    print('\nПокрытие кода:')
    cov.report()

    # Создаем HTML-отчет
    if not os.path.exists('coverage_html'):
        os.makedirs('coverage_html')
    cov.html_report(directory='coverage_html')
    print('\nHTML-отчет о покрытии создан в директории coverage_html/')

    # Возвращаем код завершения для CI/CD
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests_with_coverage())
