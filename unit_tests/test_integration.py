import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tkinter as tk
from app import App
from detect import KmExtractor
from km_analyzer import analyze_video, run_ai_analysis
from odm_defect_analyzer import analyze_segments_with_defects
from report_generator import generate_gost_report, generate_odm_report


class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.app = App(build_ui=False)
        self.app.roads = [{
            "road_name": tk.StringVar(value="Тестовая дорога"),
            "road_location": tk.StringVar(value="Тестовый район"),
            "sections": [{
                'start': "0+000", 'end': "3+000",
                'forward_videos': [], 'reverse_videos': []
            }]
        }]
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if hasattr(self.app, 'root') and self.app.root:
            self.app.root.destroy()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('cv2.VideoCapture')
    def test_i1_determine_video_type_black(self, mock_capture):
        """И1. Определение типа видео с чёрной шапкой (Preprocessing -> Video Processing)"""
        mock_cap_instance = mock_capture.return_value
        mock_cap_instance.isOpened.return_value = True
        mock_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        mock_cap_instance.read.return_value = (True, mock_frame)
        
        extractor = KmExtractor(video_path="", use_paddleocr=False)
        result = extractor.determine_video_type("dummy_path.mp4")
        
        self.assertEqual(result, "black_background", f"Ожидалось 'black_background', но получено {result}")

    @patch('cv2.VideoCapture')
    def test_i2_determine_video_type_overlay(self, mock_capture):
        """И2. Определение типа видео с текстом поверх изображения"""
        mock_cap_instance = mock_capture.return_value
        mock_cap_instance.isOpened.return_value = True
        mock_frame = np.full((720, 1280, 3), 128, dtype=np.uint8)
        mock_cap_instance.read.return_value = (True, mock_frame)
        
        extractor = KmExtractor(video_path="", use_paddleocr=False)
        result = extractor.determine_video_type("dummy_path.mp4")
        
        self.assertEqual(result, "overlay", f"Ожидалось 'overlay', но получено {result}")

    @patch('cv2.VideoCapture')
    def test_i3_determine_video_type_missing_file(self, mock_capture):
        """И3. Обработка несуществующего файла при определении типа видео"""
        mock_cap_instance = mock_capture.return_value
        mock_cap_instance.isOpened.return_value = False
        
        extractor = KmExtractor(video_path="", use_paddleocr=False)
        result = extractor.determine_video_type("missing.mp4")
        
        self.assertEqual(result, "overlay", f"Ожидалось 'overlay' (по умолчанию), но получено {result}")

    @patch('cv2.VideoCapture')
    def test_i18_determine_video_type_empty_frames(self, mock_capture):
        """И18. Обработка файла без кадров при определении типа видео"""
        mock_cap_instance = mock_capture.return_value
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (False, None)
        
        extractor = KmExtractor(video_path="", use_paddleocr=False)
        result = extractor.determine_video_type("empty.mp4")
        
        self.assertEqual(result, "overlay", "Для пустого файла должен вернуться тип по умолчанию")


    @patch('km_analyzer.analyze_video')
    @patch('km_analyzer.run_ai_analysis')
    def test_i4_app_analyze_video_forward(self, mock_run_ai, mock_analyze_video):
        """И4. Передача данных при извлечении километража (прямое направление)"""
        mock_analyze_video.return_value = ("0+000", "0+040", None)
        mock_run_ai.return_value = []
        
        self.app.analysis_results = {}
        result = self.app.analyze_video_file("test_video.mp4", "forward")
        
        mock_analyze_video.assert_called_once()
        self.assertEqual(result["start"], "0+000")
        self.assertEqual(result["end"], "0+040")
        self.assertFalse(result.get("is_mock", True), "Флаг is_mock должен быть False (заглушки нет)")

    @patch('km_analyzer.analyze_video')
    @patch('km_analyzer.run_ai_analysis')
    def test_i5_app_analyze_video_reverse(self, mock_run_ai, mock_analyze_video):
        """И5. Передача данных при извлечении километража (обратное направление)"""
        mock_analyze_video.return_value = ("0+040", "0+000", None)
        mock_run_ai.return_value = []
        
        self.app.analysis_results = {}
        result = self.app.analyze_video_file("test_video.mp4", "reverse")
        
        mock_analyze_video.assert_called_once_with("test_video.mp4", direction="reverse")
        self.assertEqual(result["start"], "0+040")
        self.assertEqual(result["end"], "0+000")
        self.assertFalse(result.get("is_mock", True), "Флаг is_mock должен быть False")

    @patch('km_analyzer.analyze_video')
    def test_i6_app_analyze_video_not_found(self, mock_analyze_video):
        """И6. Обработка ошибки при отсутствии распознанных километров"""
        mock_analyze_video.return_value = (None, None, "Километры не найдены")
        
        self.app.analysis_results = {}
        result = self.app.analyze_video_file("test_video.mp4", "forward")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Километры не найдены")

    @patch('km_analyzer.analyze_video')
    @patch('km_analyzer.run_ai_analysis')
    def test_i7_app_analyze_no_user_bounds(self, mock_run_ai, mock_analyze_video):
        """И7. Использование распознанных границ, если пользовательские не заданы"""
        mock_analyze_video.return_value = ("0+000", "0+300", None)
        mock_run_ai.return_value = []
        
        self.app.analysis_results = {}
        self.app.saved_settings = {}
        
        result = self.app.analyze_video_file("test_video.mp4", "forward")

        mock_run_ai.assert_called_once()
        args, kwargs = mock_run_ai.call_args
        self.assertEqual(args[3], 0, "start_m должен быть 0")
        self.assertEqual(args[4], 300, "end_m должен быть 300")
        self.assertEqual(result["start"], "0+000")
        self.assertEqual(result["end"], "0+300")

    @patch('km_analyzer.analyze_video')
    @patch('km_analyzer.km_to_meters')
    def test_i17_app_analyze_invalid_bounds(self, mock_km_to_meters, mock_analyze):
        """И17. Обработка некорректных границ (km_to_meters вернул None) в App"""
        mock_analyze.return_value = ("abc", "def", None)
        mock_km_to_meters.return_value = None
        
        self.app.analysis_results = {}
        result = self.app.analyze_video_file("test_video.mp4", "forward")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Некорректные значения границ километража")


    @patch('km_analyzer.get_defect_detector')
    @patch('cv2.VideoCapture')
    def test_i8_run_ai_analysis_success(self, mock_capture, mock_get_detector):
        """И8. Вызов анализа дефектов на прямом направлении"""
        mock_cap_instance = mock_capture.return_value
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.get.return_value = 10
        mock_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        mock_cap_instance.read.side_effect = [(True, mock_frame)] * 10 + [(False, None)]
        
        mock_detector = MagicMock()
        mock_detector.analyze_frame_with_details.return_value = {
            "code": 1, "position": 50, "class_name_ru": "Выбоина", "confidence": 0.9
        }
        mock_get_detector.return_value = mock_detector
        
        result = run_ai_analysis("dummy.mp4", "0+000", "0+300", 0, 300, "forward")
        
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0][2][0]["code"], 1)

    def test_i9_run_ai_analysis_invalid_forward(self):
        """И9. Некорректные границы для прямого направления (конец < начало)"""
        result = run_ai_analysis("dummy.mp4", "0+000", "0+300", 300, 0, "forward")
        self.assertEqual(result, [], "При end_m <= start_m должен вернуться пустой список")

    def test_i10_run_ai_analysis_invalid_reverse(self):
        """И10. Некорректные границы для обратного направления (начало < конец)"""
        result = run_ai_analysis("dummy.mp4", "0+300", "0+000", 0, 300, "reverse")
        self.assertEqual(result, [], "При start_m <= end_m (для reverse) должен вернуться пустой список")


    def test_i11_analyze_segments_mixed_formats(self):
        """И11. Передача сегментов с дефектами в разных форматах в Analysis"""
        segments_data = [
            (0, 100, [{"code": 1}]), 
            (100, 200, [{"type": "crack_grid"}]), 
            (200, 300, [4]), 
            (300, 400, ["6"])
        ]
        
        result = analyze_segments_with_defects(segments_data, segment_length=100)
        
        self.assertEqual(len(result), 4)
        for start, end, (code, score) in result:
            self.assertIsInstance(code, int)
            self.assertIsInstance(score, float)

    def test_i12_analyze_segments_empty(self):
        """И12. Передача пустого списка сегментов в Analysis"""
        result = analyze_segments_with_defects([])
        self.assertEqual(result, [], "Должен вернуться пустой список")


    def test_i13_generate_gost_report(self):
        """И13. Формирование отчёта по ГОСТ для одного направления"""
        forward = [(0, 100, [{"code": 1, "position": 50}])]
        reverse = None
        
        file_path = generate_gost_report(forward, reverse, "test_road", self.temp_dir)
        
        self.assertTrue(os.path.exists(file_path), "Файл отчета не создан")
        self.assertTrue(os.path.basename(file_path).startswith("ГОСТ_test_road_"))

    def test_i14_generate_odm_report(self):
        """И14. Формирование отчёта по ОДМ для двух направлений"""
        forward = [(0, 100, [{"code": 1, "position": 50}])]
        reverse = [(100, 200, [{"code": 4, "position": 150}])]
        
        file_path = generate_odm_report(forward, reverse, "test_road", self.temp_dir)
        
        self.assertTrue(os.path.exists(file_path), "Файл отчета не создан")
        self.assertTrue(os.path.basename(file_path).startswith("ОДМ_test_road_"))

    def test_i15_generate_gost_report_only_reverse(self):
        """И15. Формирование отчета по ГОСТ, когда есть только обратное направление"""
        forward = []
        reverse = [(0, 100, [{"code": 1, "position": 50}])]
        
        file_path = generate_gost_report(forward, reverse, "test_road", self.temp_dir)
        
        self.assertTrue(os.path.exists(file_path), "Файл отчета не создан")


    @patch('os.makedirs')
    def test_i16_generate_report_invalid_path(self, mock_makedirs):
        """И16. Обработка ошибки при недоступной директории для сохранения (ГОСТ)"""
        mock_makedirs.side_effect = OSError("Отказано в доступе")
        
        forward = [(0, 100, [{"code": 1, "position": 50}])]
        invalid_path = "/invalid_path_for_test_12345"

        with self.assertRaises(PermissionError):
            generate_gost_report(forward, None, "test_road", invalid_path)


class CustomTextTestResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        doc = (test._testMethodDoc or '').strip().split('\n')[0]
        self.stream.writeln(f"[ ПРОЙДЕН ] {doc}")
    def addFailure(self, test, err):
        super().addFailure(test, err)
        doc = (test._testMethodDoc or '').strip().split('\n')[0]
        self.stream.writeln(f"[ НЕ ПРОЙДЕН ] {doc} - Ошибка: {str(err[1]).split(chr(10))[0]}")
    def addError(self, test, err):
        super().addError(test, err)
        doc = (test._testMethodDoc or '').strip().split('\n')[0]
        self.stream.writeln(f"[ ОШИБКА ] {doc} - Ошибка: {str(err[1]).split(chr(10))[0]}")

if __name__ == '__main__':
    print("=" * 70)
    print("ЗАПУСК ИНТЕГРАЦИОННЫХ ТЕСТОВ (И1 - И18)")
    print("=" * 70)

    runner = unittest.TextTestRunner(resultclass=CustomTextTestResult, verbosity=0)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntegration)
    result = runner.run(suite)
    
    print("=" * 70)
    print(f"ИТОГО: Пройдено {result.testsRun - len(result.failures) - len(result.errors)} из {result.testsRun}")
    print("=" * 70)