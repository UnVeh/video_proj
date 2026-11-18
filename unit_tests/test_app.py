import unittest
import sys
import os
import shutil
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tkinter as tk
from app import App

class TestAppUtils(unittest.TestCase):

    def setUp(self):
        self.app = App(build_ui=False)

        self.app.roads = [{
            "road_name": tk.StringVar(value="Тестовая дорога"),
            "road_location": tk.StringVar(value="Тестовый район"),
            "sections": [{
                'start': "0+000",
                'end': "3+000",
                'forward_videos': ["test_forward.mp4"],
                'reverse_videos': ["test_reverse.mp4"]
            }]
        }]

    def tearDown(self):
        if hasattr(self.app, 'root') and self.app.root:
            self.app.root.destroy()

    def test_b48_get_video_direction_forward(self):
        """Б48. Проверка определения направления видео (прямое)"""
        result = self.app.get_video_direction("test_forward.mp4")
        self.assertEqual(result, "forward", f"Ожидалось 'forward', но получено {result}")

    def test_b49_get_video_direction_reverse(self):
        """Б49. Проверка определения направления видео (обратное)"""
        result = self.app.get_video_direction("test_reverse.mp4")
        self.assertEqual(result, "reverse", f"Ожидалось 'reverse', но получено {result}")

    def test_b54_get_reports_directory_create(self):
        """Б54. Проверка определения и создания директории для сохранения отчётов"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_reports")
        if os.path.exists(test_dir):
            try:
                shutil.rmtree(test_dir)
            except:
                pass 

        result = self.app.get_reports_directory()

        self.assertIn("app_reports", result, "Возвращаемый путь должен содержать 'app_reports'")
        self.assertTrue(os.path.exists(result), f"Директория {result} не была создана на диске")

    def test_b55_get_reports_directory_existing(self):
        """Б55. Проверка повторного вызова get_reports_directory()"""
        result1 = self.app.get_reports_directory()
        result2 = self.app.get_reports_directory()
        
        self.assertEqual(result1, result2, "Путь при повторном вызове не совпадает")

    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_b56_get_reports_directory_permission_error(self, mock_makedirs, mock_exists):
        """Б56. Проверка поведения метода при отсутствии прав на создание директории"""
        mock_exists.return_value = False
        mock_makedirs.side_effect = PermissionError("Отказано в доступе")

        with self.assertRaises(PermissionError):
            self.app.get_reports_directory()


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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAppUtils)
    result = runner.run(suite)
    
    print("=" * 70)
    print(f"ИТОГО: Пройдено {result.testsRun - len(result.failures) - len(result.errors)} из {result.testsRun}")
    print("=" * 70)