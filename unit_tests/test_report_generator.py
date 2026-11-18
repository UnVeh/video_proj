import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from report_generator import (
    process_report_data, 
    extract_defect_codes_for_gost, 
    split_into_100m_segments, 
    meters_to_km_str
)

class TestReportGenerator(unittest.TestCase):

    def test_b38_process_data_no_reverse(self):
        """Б38. Проверка поведения функции при отсутствии обратного направления"""
        forward = [(0, 100, [{"position": 50}])]
        reverse = None
        
        fwd_sorted, rev_sorted, common_start, common_end = process_report_data(forward, reverse)
        
        self.assertEqual(len(fwd_sorted), 1, f"Ожидалось 1 элемент в fwd_sorted, но получено {len(fwd_sorted)}")
        self.assertEqual(len(rev_sorted), 0, f"Ожидалось 0 элементов в rev_sorted, но получено {len(rev_sorted)}")
        self.assertEqual(common_start, 0, f"Ожидалось common_start=0, но получено {common_start}")
        self.assertEqual(common_end, 100, f"Ожидалось common_end=100, но получено {common_end}")

    def test_b39_process_data_with_reverse(self):
        """Б39. Проверка поведения функции при наличии данных обратного направления"""
        forward = [(0, 100, [{"position": 50}])]
        reverse = [(200, 300, [{"position": 250}])]
        
        fwd_sorted, rev_sorted, common_start, common_end = process_report_data(forward, reverse)
        
        self.assertEqual(len(fwd_sorted), 1, f"Ожидалось 1 элемент в fwd_sorted, но получено {len(fwd_sorted)}")
        self.assertEqual(len(rev_sorted), 1, f"Ожидалось 1 элемент в rev_sorted, но получено {len(rev_sorted)}")
        self.assertEqual(common_start, 0, f"Ожидалось common_start=0, но получено {common_start}")
        self.assertEqual(common_end, 300, f"Ожидалось common_end=300, но получено {common_end}")


    def test_b40_extract_defect_codes_mixed_formats(self):
        """Б40. Проверка извлечения уникальных кодов дефектов из разных форматов данных"""
        defects_list = [{"code": 1}, {"type": "crack_grid"}, 4, "6"]
        
        result = extract_defect_codes_for_gost(defects_list)
        
        self.assertEqual(sorted(result), [1, 3, 4, 6], f"Ожидалось [1, 3, 4, 6], но получено {sorted(result)}")

    def test_b41_extract_defect_codes_empty(self):
        """Б41. Проверка поведения функции при передаче пустого списка"""
        result = extract_defect_codes_for_gost([])
        
        self.assertEqual(result, [], f"Ожидался пустой список, но получено {result}")


    def test_b42_split_into_100m_segments_valid(self):
        """Б42. Проверка разбиения сегментов на 100-метровые интервалы с распределением дефектов"""
        segments_data = [(0, 250, [{"position": 50}, {"position": 150}, {"position": 220}])]
        
        result = split_into_100m_segments(segments_data, common_start=0, common_end=250)
        
        self.assertEqual(len(result), 3, f"Ожидалось 3 интервала, но получено {len(result)}")

        self.assertIn((0, 100), result)
        self.assertEqual(len(result[(0, 100)]), 1)
        self.assertEqual(result[(0, 100)][0]["position"], 50, "Дефект 50 попал не в свой интервал")

        self.assertIn((100, 200), result)
        self.assertEqual(len(result[(100, 200)]), 1)
        self.assertEqual(result[(100, 200)][0]["position"], 150, "Дефект 150 попал не в свой интервал")

        self.assertIn((200, 250), result)
        self.assertEqual(len(result[(200, 250)]), 1)
        self.assertEqual(result[(200, 250)][0]["position"], 220, "Дефект 220 попал не в свой интервал")

    def test_b43_split_into_100m_segments_none_intervals(self):
        """Б43. Проверка возврата None для интервалов, которые не покрыты сегментами"""
        segments_data = [(0, 100, [{"position": 50}])]
        
        result = split_into_100m_segments(segments_data, common_start=0, common_end=300)
        
        self.assertEqual(len(result), 3, f"Ожидалось 3 интервала, но получено {len(result)}")
        
        self.assertIn((0, 100), result)
        self.assertEqual(len(result[(0, 100)]), 1)

        self.assertIn((100, 200), result)
        self.assertIsNone(result[(100, 200)], f"Ожидалось None для (100, 200), но получено {result[(100, 200)]}")
        
        self.assertIn((200, 300), result)
        self.assertIsNone(result[(200, 300)], f"Ожидалось None для (200, 300), но получено {result[(200, 300)]}")

    def test_b44_split_into_100m_segments_empty(self):
        """Б44. Проверка поведения функции при передаче пустого списка сегментов"""
        result = split_into_100m_segments([], common_start=None, common_end=None)
        self.assertEqual(len(result), 0, f"Ожидалась пустая коллекция, но получено {result}")


    def test_b45_meters_to_km_str_boundary(self):
        """Б45. Проверка преобразования метров в формат «км+м» на граничном значении 1000"""
        result = meters_to_km_str(1000)
        
        self.assertEqual(result, "1+000", f"Ожидалось '1+000', но получено {result}")

    def test_b46_meters_to_km_str_valid(self):
        """Б46. Проверка преобразования метров в формат «км+м» на произвольном значении 250"""
        result = meters_to_km_str(250)
        
        self.assertEqual(result, "0+250", f"Ожидалось '0+250', но получено {result}")

    def test_b47_meters_to_km_str_invalid(self):
        """Б47. Проверка поведения функции при передаче некорректной строки"""
        with self.assertRaises(ValueError):
            meters_to_km_str("abc")

    def test_b54_process_data_different_bounds(self):
        """Б54. Проверка вычисления общего диапазона при несовпадающих границах направлений"""
        forward = [(0, 1000, [])]
        reverse = [(5, 1200, [])]
        
        fwd_sorted, rev_sorted, common_start, common_end = process_report_data(forward, reverse)

        self.assertEqual(common_start, 0, f"Ожидалось common_start=0, но получено {common_start}")
        self.assertEqual(common_end, 1200, f"Ожидалось common_end=1200, но получено {common_end}")

    def test_b55_process_data_non_overlapping_bounds(self):
        """Б55. Проверка вычисления общего диапазона при непересекающихся диапазонах"""
        forward = [(0, 1000, [])]
        reverse = [(1200, 2000, [])]
        
        fwd_sorted, rev_sorted, common_start, common_end = process_report_data(forward, reverse)
        
        self.assertEqual(common_start, 0, f"Ожидалось common_start=0, но получено {common_start}")
        self.assertEqual(common_end, 2000, f"Ожидалось common_end=2000, но получено {common_end}")


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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestReportGenerator)
    result = runner.run(suite)
    
    print("=" * 70)
    print(f"ИТОГО: Пройдено {result.testsRun - len(result.failures) - len(result.errors)} из {result.testsRun}")
    print("=" * 70)