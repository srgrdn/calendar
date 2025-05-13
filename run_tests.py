import unittest
import sys
from tests import AuthTestCase, CalendarTestCase, MessageTestCase, ModelTestCase
from integration_tests import IntegrationTestCase


def run_tests():
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
    
    # Возвращаем код завершения для CI/CD
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())