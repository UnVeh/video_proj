import unittest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from detect import KmExtractor

class TestKmExtractorKilometerParsing(unittest.TestCase):

    def setUp(self):
        self.extractor = KmExtractor(video_path="", use_paddleocr=False)
        self.extractor.raw_km_values = []

    def test_b1_extract_kilometer_with_dot(self):
        """Б1. Проверка извлечения километража (точка как разделитель)"""
        text = "0.123 км"
        expected = "0.123"
        result = self.extractor.extract_kilometer(text)
        self.assertIsNotNone(result, "Метод вернул None вместо строки")
        self.assertEqual(result, expected, f"Ожидалось {expected}, но получено {result}")

    def test_b2_extract_kilometer_with_comma(self):
        """Б2. Проверка извлечения километража (запятая заменяется на точку)"""
        text = "0,123 км"
        expected = "0.123"
        result = self.extractor.extract_kilometer(text)
        self.assertIsNotNone(result, "Метод вернул None вместо строки")
        self.assertEqual(result, expected, f"Ожидалось {expected}, но получено {result}")

    def test_b3_extract_kilometer_invalid_format_two_digits(self):
        """Б3. Проверка возврата None при двух знаках после разделителя"""
        text = "0,01 км"
        result = self.extractor.extract_kilometer(text)
        self.assertIsNone(result, f"Ожидалось None, но получено {result}")

    def test_b4_extract_kilometer_no_separator(self):
        """Б4. Проверка возврата None при отсутствии разделителя"""
        text = "0 010 км"
        result = self.extractor.extract_kilometer(text)
        self.assertIsNone(result, f"Ожидалось None, но получено {result}")

    def test_b5_extract_kilometer_one_digit(self):
        """Б5. Проверка возврата None при одном знаке после разделителя"""
        text = "0,1 км"
        result = self.extractor.extract_kilometer(text)
        self.assertIsNone(result, f"Ожидалось None, но получено {result}")

    def test_b6_extract_kilometer_four_digits(self):
        """Б6. Проверка возврата None при четырех знаках после разделителя"""
        text = "0,1111 км"
        result = self.extractor.extract_kilometer(text)
        self.assertIsNone(result, f"Ожидалось None, но получено {result}")

    def test_b7_extract_kilometer_space_after_separator(self):
        """Б7. Проверка возврата None при пробеле после разделителя"""
        text = "0, 100 км"
        result = self.extractor.extract_kilometer(text)
        self.assertIsNone(result, f"Ожидалось None, но получено {result}")

    def test_b8_extract_kilometer_text_without_numbers(self):
        """Б8. Проверка возврата None при тексте без цифр"""
        text = "текст"
        result = self.extractor.extract_kilometer(text)
        self.assertIsNone(result, f"Ожидалось None, но получено {result}")

    def test_b9_extract_kilometer_empty_string(self):
        """Б9. Проверка возврата None при пустой строке"""
        text = ""
        result = self.extractor.extract_kilometer(text)
        self.assertIsNone(result, f"Ожидалось None, но получено {result}")

    def test_b10_detect_black_background_frame(self):
        """Б10. Проверка определения типа кадра (черная шапка)"""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        expected = "black_background"
        result = self.extractor._detect_single_frame_type(frame)
        self.assertEqual(result, expected, f"Ожидалось {expected}, но получено {result}")

    def test_b11_detect_overlay_frame(self):
        """Б11. Проверка определения типа кадра (текст поверх видео)"""
        frame = np.full((720, 1280, 3), 128, dtype=np.uint8)
        expected = "overlay"
        result = self.extractor._detect_single_frame_type(frame)
        self.assertEqual(result, expected, f"Ожидалось {expected}, но получено {result}")

    def test_b12_determine_step_insufficient_data(self):
        """Б12. Проверка шага при недостаточном количестве значений"""
        values = [0.000]
        expected = 0.010
        result = self.extractor.determine_step_from_values(values)
        self.assertEqual(result, expected, f"Ожидалось {expected}, но получено {result}")

    def test_b13_determine_step_forward_0005(self):
        """Б13. Проверка шага 0.005 для прямого направления"""
        values = [0.000, 0.005, 0.010, 0.015, 0.020]
        self.extractor.direction = "forward"
        result = self.extractor.determine_step_from_values(values)
        self.assertEqual(result, 0.005, f"Ожидалось 0.005, но получено {result}")

    def test_b14_determine_step_reverse(self):
        """Б14. Проверка шага -0.010 для обратного направления"""
        values = [0.040, 0.030, 0.020, 0.010, 0.000]
        self.extractor.direction = "reverse"
        result = self.extractor.determine_step_from_values(values)
        self.assertEqual(result, -0.010, f"Ожидалось -0.010, но получено {result}")

    def test_b15_determine_step_unknown(self):
        """Б15. Проверка шага по умолчанию при неизвестных разницах"""
        values = [0.000, 0.037, 0.081, 0.129]
        self.extractor.direction = "forward"
        result = self.extractor.determine_step_from_values(values)
        self.assertEqual(result, 0.010, f"Ожидалось 0.010, но получено {result}")

    def test_b16_extract_kilometer_smart_success(self):
        """Б16. Проверка добавления значения в историю"""
        text = "0.123 км"
        current_frame = 10
        expected_km = "0.123"
        result = self.extractor.extract_kilometer_smart(text, current_frame)
        self.assertEqual(result, expected_km, f"Ожидалось {expected_km}, но получено {result}")
        self.assertEqual(len(self.extractor.raw_km_values), 1, "В историю не добавлена запись")
        self.assertEqual(self.extractor.raw_km_values[0], (10, 0.123, "0.123"))

    def test_b17_extract_kilometer_smart_fail(self):
        """Б17. Проверка отсутствия записи при тексте без километража"""
        text = "текст"
        current_frame = 10
        result = self.extractor.extract_kilometer_smart(text, current_frame)
        self.assertIsNone(result, f"Ожидалось None, но получено {result}")
        self.assertEqual(len(self.extractor.raw_km_values), 0, "История должна оставаться пустой")


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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKmExtractorKilometerParsing)
    result = runner.run(suite)
    
    print("=" * 70)
    print(f"ИТОГО: Пройдено {result.testsRun - len(result.failures) - len(result.errors)} из {result.testsRun}")
    print("=" * 70)