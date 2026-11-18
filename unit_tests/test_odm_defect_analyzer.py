import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from odm_defect_analyzer import ODMDefectAnalyzer, merge_overlapping_segments, analyze_segments_with_defects

class TestODMDefectAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = ODMDefectAnalyzer(debug=False)

    def test_b28_add_defect_and_grouping(self):
        """Б28. Проверка добавления дефекта и его группировки по расстоянию"""
        distance_meters = 150.4
        defect_type = "pothole"
        defect_data = {"position": 150, "code": 1}
        
        self.analyzer.add_defect(distance_meters, defect_type, defect_data)
        
        self.assertIn(150, self.analyzer.defects_by_distance, "Дефект не добавлен по ключу 150")
        self.assertEqual(len(self.analyzer.defects_by_distance[150]), 1, "Список дефектов должен содержать один элемент")

    def test_b29_add_defect_rounding(self):
        """Б29. Проверка округления расстояния при добавлении дефекта"""
        distance_meters = 150.6
        defect_type = "pothole"
        defect_data = {"position": 150, "code": 1}
        
        self.analyzer.add_defect(distance_meters, defect_type, defect_data)

        self.assertIn(151, self.analyzer.defects_by_distance, "Дефект не добавлен по ключу 151")
        self.assertNotIn(150, self.analyzer.defects_by_distance, "Дефект ошибочно добавлен по ключу 150")

    def test_b30_get_defects_in_range_boundaries(self):
        """Б30. Проверка выборки дефектов в заданном диапазоне на граничных значениях"""
        self.analyzer.add_defect(100, "pothole", {"code": 1})
        self.analyzer.add_defect(200, "pothole", {"code": 2})
        self.analyzer.add_defect(300, "pothole", {"code": 3})
        
        result = self.analyzer.get_defects_in_range(start=100, end=200)
        
        self.assertEqual(len(result), 2, f"Ожидалось 2 дефекта, но получено {len(result)}")
        codes = [d["data"]["code"] for d in result]
        self.assertIn(1, codes, "Дефект на границе 100 не попал в выборку")
        self.assertIn(2, codes, "Дефект на границе 200 не попал в выборку")
        self.assertNotIn(3, codes, "Дефект вне диапазона попал в выборку")

    def test_b31_get_defects_in_range_empty(self):
        """Б31. Проверка поведения метода при отсутствии дефектов в заданном диапазоне"""
        self.analyzer.add_defect(100, "pothole", {"code": 1})
        self.analyzer.add_defect(200, "pothole", {"code": 1})
        
        result = self.analyzer.get_defects_in_range(start=300, end=400)
        
        self.assertEqual(result, [], f"Ожидался пустой список, но получено {result}")
        self.assertIsInstance(result, list, "Возвращаемое значение должно быть списком")

    def test_b32_analyze_empty_segment(self):
        """Б32. Проверка присвоения кода и оценки для пустого сегмента"""
        result = self.analyzer.analyze_defects_on_segment(segment_start=0, segment_end=100)

        self.assertEqual(result, (1, 5.0), f"Ожидалось (1, 5.0), но получено {result}")

    def test_b33_analyze_pothole_segment(self):
        """Б33. Проверка присвоения кода и оценки для сегмента с одиночной выбоиной"""
        self.analyzer.add_defect(distance_meters=50, defect_type="pothole", defect_data={"code": 1})
        
        result = self.analyzer.analyze_defects_on_segment(segment_start=0, segment_end=100)

        self.assertEqual(result, (24, 4.5), f"Ожидалось (24, 4.5), но получено {result}")

    def test_b34_clear_with_data(self):
        """Б34. Проверка очистки данных анализа"""
        self.analyzer.add_defect(150, "pothole", {"code": 1})
        self.analyzer.clear()
        
        self.assertEqual(len(self.analyzer.defects_by_distance), 0, "Словарь должен быть пустым после очистки")

    def test_b35_clear_empty_analyzer(self):
        """Б35. Проверка очистки данных пустого анализатора"""
        try:
            self.analyzer.clear()
        except Exception as e:
            self.fail(f"Вызов clear() на пустом анализаторе вызвал исключение: {e}")
            
        self.assertEqual(len(self.analyzer.defects_by_distance), 0, "Словарь должен оставаться пустым")

    def test_b36_merge_overlapping_segments(self):
        """Б36. Проверка объединения перекрывающихся сегментов и удаления дубликатов дефектов"""
        segments_data = [
            (0, 150, [{"position": 50}]),
            (100, 200, [{"position": 50}, {"position": 180}])
        ]
        original_data = [(s, e, list(d)) for s, e, d in segments_data]
        
        result = merge_overlapping_segments(segments_data)

        self.assertEqual(len(result), 1, f"Ожидался 1 объединенный сегмент, но получено {len(result)}")
        self.assertEqual(result[0][0], 0)
        self.assertEqual(result[0][1], 200)
        
        defects = result[0][2]
        self.assertEqual(len(defects), 2, f"Ожидалось 2 уникальных дефекта, но получено {len(defects)}")
        
        positions = [d["position"] for d in defects]
        self.assertIn(50, positions)
        self.assertIn(180, positions)
        self.assertEqual(segments_data, original_data, "Функция изменила входной список сегментов!")

    def test_b37_merge_empty_list(self):
        """Б37. Проверка поведения функции при передаче пустого списка сегментов"""
        result = merge_overlapping_segments([])
        
        self.assertEqual(result, [], f"Ожидался пустой список, но получено {result}")

    def test_b53_analyze_segments_isolation(self):
        """Б53. Проверка изоляции направлений при вызове analyze_segments_with_defects"""
        segments_data_1 = [(0, 100, [{"code": 1, "position": 50}])]
        result_1 = analyze_segments_with_defects(segments_data_1, segment_length=100)

        segments_data_2 = [(0, 100, [])]
        result_2 = analyze_segments_with_defects(segments_data_2, segment_length=100)
 
        self.assertEqual(len(result_1), 1, "Первый вызов должен вернуть 1 сегмент")
        start_1, end_1, (code_1, score_1) = result_1[0]
        self.assertEqual(code_1, 24, f"Первый вызов должен вернуть код 24 (выбоина), но получен {code_1}")

        self.assertEqual(len(result_2), 1, "Второй вызов должен вернуть 1 сегмент")
        start_2, end_2, (code_2, score_2) = result_2[0]
        self.assertEqual(code_2, 1, f"Второй вызов должен вернуть код 1 (без дефектов), но получен {code_2}")


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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestODMDefectAnalyzer)
    result = runner.run(suite)
    
    print("=" * 70)
    print(f"ИТОГО: Пройдено {result.testsRun - len(result.failures) - len(result.errors)} из {result.testsRun}")
    print("=" * 70)