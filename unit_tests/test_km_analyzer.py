import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from km_analyzer import format_km, km_to_meters, meters_to_km

class TestKmAnalyzer(unittest.TestCase):
    
    def test_b18_format_km_invalid(self):
        """Б18. Проверка возврата None при некорректном вводе в format_km"""
        result = format_km("abc")
        self.assertIsNone(result, f"Ожидалось None, но получено {result}")

    def test_b19_format_km_valid_float(self):
        """Б19. Проверка форматирования 0.123 в '0+123'"""
        result = format_km(0.123)
        self.assertEqual(result, "0+123", f"Ожидалось '0+123', но получено {result}")

    def test_b20_format_km_zero(self):
        """Б20. Проверка форматирования 0.0 в '0+000'"""
        result = format_km(0.0)
        self.assertEqual(result, "0+000", f"Ожидалось '0+000', но получено {result}")


    def test_b21_km_to_meters_valid(self):
        """Б21. Проверка преобразования '1+234' в 1234"""
        result = km_to_meters("1+234")
        self.assertEqual(result, 1234, f"Ожидалось 1234, но получено {result}")

    def test_b22_km_to_meters_invalid_string(self):
        """Б22. Проверка возврата None при передаче 'abc' в km_to_meters"""
        result = km_to_meters("abc")
        self.assertIsNone(result, f"Ожидалось None, но получено {result}")

    def test_b23_km_to_meters_zero(self):
        """Б23. Проверка преобразования граничного значения 0"""
        result = km_to_meters(0)
        self.assertEqual(result, 0, f"Ожидалось 0, но получено {result}")


    def test_b24_meters_to_km_zero(self):
        """Б24. Проверка преобразования 0 в '0+000'"""
        result = meters_to_km(0)
        self.assertEqual(result, "0+000", f"Ожидалось '0+000', но получено {result}")

    def test_b25_meters_to_km_valid(self):
        """Б25. Проверка преобразования 1234 в '1+234'"""
        result = meters_to_km(1234)
        self.assertEqual(result, "1+234", f"Ожидалось '1+234', но получено {result}")

    def test_b26_meters_to_km_invalid_string(self):
        """Б26. Проверка обработки исключения при передаче строки 'abc'"""
        result = meters_to_km("abc")
        self.assertIsNone(result, f"Ожидалось None, но получено {result}")

    def test_b27_meters_to_km_float_rounding(self):
        """Б27. Проверка отбрасывания дробной части числа 1234.9"""
        result = meters_to_km(1234.9)
        self.assertEqual(result, "1+234", f"Ожидалось '1+234', но получено {result}")


class CustomTextTestResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        doc = (test._testMethodDoc or '').strip().split('\n')[0]
        self.stream.writeln(f"[ ПРОЙДЕН ] {doc}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        doc = (test._testMethodDoc or '').strip().split('\n')[0]
        error_msg = str(err[1]).split('\n')[0]
        self.stream.writeln(f"[ НЕ ПРОЙДЕН ] {doc} - Ошибка: {error_msg}")

    def addError(self, test, err):
        super().addError(test, err)
        doc = (test._testMethodDoc or '').strip().split('\n')[0]
        error_msg = str(err[1]).split('\n')[0]
        self.stream.writeln(f"[ ОШИБКА ] {doc} - Ошибка: {error_msg}")

if __name__ == '__main__':
    print("=" * 70)
    print("ЗАПУСК БЛОЧНЫХ ТЕСТОВ")
    print("=" * 70)

    runner = unittest.TextTestRunner(resultclass=CustomTextTestResult, verbosity=0)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKmAnalyzer)
    result = runner.run(suite)
    
    print("=" * 70)
    print(f"ИТОГО: Пройдено {result.testsRun - len(result.failures) - len(result.errors)} из {result.testsRun}")
    print("=" * 70)