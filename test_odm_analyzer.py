"""
Полное тестирование всех кодов дефектов ОДМ
Проверка формул и вычислений для каждого типа дефекта
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odm_defect_analyzer import ODMDefectAnalyzer, ODM_DEFECTS


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(100)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*100}{Colors.END}")


def print_section(text: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*len(text)}{Colors.END}")


def print_formula(title: str, formula: str, calculation: str, result: str):
    """Вывод формулы расчета"""
    print(f"  {Colors.BLUE}📐 {title}:{Colors.END}")
    print(f"    {Colors.BOLD}Формула:{Colors.END} {formula}")
    print(f"    {Colors.BOLD}Расчет:{Colors.END} {calculation}")
    print(f"    {Colors.BOLD}Результат:{Colors.END} {result}")


def print_test_result(code: int, expected_score: float, actual_code: int, actual_score: float, passed: bool):
    """Вывод результата теста"""
    if passed:
        print(f"  {Colors.GREEN}✓ ТЕСТ ПРОЙДЕН: код {actual_code}, оценка {actual_score:.1f}{Colors.END}")
    else:
        print(f"  {Colors.RED}✗ ТЕСТ НЕ ПРОЙДЕН: получено код={actual_code}, оценка={actual_score:.1f}, ожидалось код={code}, оценка={expected_score:.1f}{Colors.END}")


def test_transverse_cracks():
    """Тест всех кодов поперечных трещин (коды 1-9)"""
    print_header("ТЕСТ 1: ПОПЕРЕЧНЫЕ ТРЕЩИНЫ (коды 1-9)")
    
    test_cases = [
        {
            "code": 1,
            "score": 5.0,
            "distance": 45,
            "range": ">40м",
            "formula": "d > 40",
            "description": "Одиночные трещины или расстояние более 40м"
        },
        {
            "code": 2,
            "score": 4.9,
            "distance": 30,
            "range": "20-40м",
            "formula": "20 ≤ d ≤ 40",
            "description": "Расстояние между трещинами 20-40м"
        },
        {
            "code": 3,
            "score": 4.6,
            "distance": 15,
            "range": "10-20м",
            "formula": "10 ≤ d < 20",
            "description": "Расстояние между трещинами 10-20м"
        },
        {
            "code": 4,
            "score": 4.3,
            "distance": 9,
            "range": "8-10м",
            "formula": "8 ≤ d < 10",
            "description": "Расстояние между трещинами 8-10м"
        },
        {
            "code": 5,
            "score": 3.9,
            "distance": 7,
            "range": "6-8м",
            "formula": "6 ≤ d < 8",
            "description": "Расстояние между трещинами 6-8м"
        },
        {
            "code": 6,
            "score": 3.6,
            "distance": 5,
            "range": "4-6м",
            "formula": "4 ≤ d < 6",
            "description": "Расстояние между трещинами 4-6м"
        },
        {
            "code": 7,
            "score": 3.2,
            "distance": 3.5,
            "range": "3-4м",
            "formula": "3 ≤ d < 4",
            "description": "Расстояние между трещинами 3-4м"
        },
        {
            "code": 8,
            "score": 2.9,
            "distance": 2.5,
            "range": "2-3м",
            "formula": "2 ≤ d < 3",
            "description": "Расстояние между трещинами 2-3м"
        },
        {
            "code": 9,
            "score": 2.6,
            "distance": 1.5,
            "range": "1-2м",
            "formula": "1 ≤ d < 2",
            "description": "Расстояние между трещинами 1-2м"
        }
    ]
    
    for test in test_cases:
        print_section(f"Код {test['code']}: {test['description']}")
        
        analyzer = ODMDefectAnalyzer(debug=False)
        analyzer.add_defect(0, "crack_transverse")
        analyzer.add_defect(test["distance"], "crack_transverse")
        
        print(f"  Позиции трещин: 0м и {test['distance']}м")
        
        print_formula(
            "Расстояние между трещинами",
            "d = |x₂ - x₁|",
            f"d = |{test['distance']} - 0| = {test['distance']}м",
            f"{test['distance']}м → {test['range']}"
        )
        
        print_formula(
            "Определение кода",
            test['formula'],
            f"{test['distance']}м {test['range']}",
            f"код {test['code']}, оценка {test['score']:.1f}"
        )
        
        code, score = analyzer.analyze_defects_on_segment(0, 100)
        
        passed = (code == test['code'] and abs(score - test['score']) < 0.1)
        print_test_result(test['code'], test['score'], code, score, passed)


def test_longitudinal_cracks():
    """Тест продольных трещин (коды 10-11)"""
    print_header("ТЕСТ 2: ПРОДОЛЬНЫЕ ТРЕЩИНЫ (коды 10-11)")
    
    test_cases = [
        {
            "code": 10,
            "score": 4.5,
            "type": "crack_longitudinal_center",
            "name": "Продольная центральная трещина",
            "formula": "Фиксированное значение по таблице ОДМ",
            "description": "Одиночная центральная трещина вдоль дороги"
        },
        {
            "code": 11,
            "score": 3.5,
            "type": "crack_longitudinal_side",
            "name": "Продольные боковые трещины",
            "formula": "Фиксированное значение по таблице ОДМ",
            "description": "Боковые трещины с одной или обеих сторон"
        }
    ]
    
    for test in test_cases:
        print_section(f"Код {test['code']}: {test['name']}")
        
        analyzer = ODMDefectAnalyzer(debug=False)
        analyzer.add_defect(50, test["type"])
        
        print(f"  Дефект: {test['description']}")
        
        print_formula(
            "Определение кода",
            test['formula'],
            f"Обнаружена {test['name']}",
            f"код {test['code']}, оценка {test['score']:.1f}"
        )
        
        code, score = analyzer.analyze_defects_on_segment(0, 100)
        
        passed = (code == test['code'] and abs(score - test['score']) < 0.1)
        print_test_result(test['code'], test['score'], code, score, passed)


def test_crack_grid():
    """Тест сетки трещин (коды 12-17)"""
    print_header("ТЕСТ 3: СЕТКА ТРЕЩИН (коды 12-17)")
    
    test_cases = [
        {
            "code": 12,
            "score": 3.0,
            "area": 8,
            "cell_size": 0.6,
            "segment": 100,
            "range": "до 10м²",
            "formula": "площадь ≤ 10м² И размер ячейки > 0.5м",
            "description": "Одиночная сетка до 10м² с крупными ячейками (>0.5м)"
        },
        {
            "code": 13,
            "score": 2.5,
            "area": 8,
            "cell_size": 0.4,
            "segment": 100,
            "range": "до 10м²",
            "formula": "площадь ≤ 10м² И размер ячейки ≤ 0.5м И не густая",
            "description": "Одиночная сетка до 10м² с мелкими ячейками (<0.5м) - обычная"
        },
        {
            "code": 13,
            "score": 2.5,
            "area": 7,
            "cell_size": 0.35,
            "segment": 100,
            "range": "до 10м²",
            "formula": "площадь ≤ 10м² И размер ячейки ≤ 0.5м (обычная)",
            "description": "Одиночная сетка с мелкими ячейками, площадь <9м²"
        },
        {
            "code": 14,
            "score": 2.0,
            "area": 10,
            "cell_size": 0.25,
            "segment": 100,
            "range": "до 10м²",
            "formula": "площадь ≥ 9м² И размер ячейки ≤ 0.3м (густая сетка)",
            "description": "Густая сетка трещин на площади до 10м²"
        },
        {
            "code": 14,
            "score": 2.0,
            "area": 9.5,
            "cell_size": 0.28,
            "segment": 100,
            "range": "до 10м²",
            "formula": "площадь ≥ 9м² И размер ячейки ≤ 0.3м (густая сетка)",
            "description": "Густая сетка трещин с большой площадью и мелкими ячейками"
        },
        {
            "code": 15,
            "score": 2.3,
            "area": 20,
            "cell_size": 0.5,
            "segment": 100,
            "range": ">10м²",
            "formula": "относительная площадь = (площадь / длина) × 100%, 10-30%",
            "description": "Сетка трещин на площади >10м², относительная площадь 10-30%"
        },
        {
            "code": 16,
            "score": 1.9,
            "area": 45,
            "cell_size": 0.5,
            "segment": 100,
            "range": ">10м²",
            "formula": "относительная площадь = (площадь / длина) × 100%, 30-60%",
            "description": "Сетка трещин на площади >10м², относительная площадь 30-60%"
        },
        {
            "code": 17,
            "score": 1.6,
            "area": 75,
            "cell_size": 0.5,
            "segment": 100,
            "range": ">10м²",
            "formula": "относительная площадь = (площадь / длина) × 100%, 60-90%",
            "description": "Сетка трещин на площади >10м², относительная площадь 60-90%"
        }
    ]
    
    for test in test_cases:
        print_section(f"Код {test['code']}: {test['description']}")
        
        analyzer = ODMDefectAnalyzer(debug=False)
        analyzer.add_defect(50, "crack_grid", {"area": test["area"], "cell_size": test["cell_size"]})
        
        print(f"  Площадь сетки: {test['area']}м²")
        print(f"  Размер ячейки: {test['cell_size']}м")
        print(f"  Длина сегмента: {test['segment']}м")
        
        if test["area"] > 10:
            relative_area = (test["area"] / test["segment"]) * 100
            print_formula(
                "Относительная площадь",
                "P = (площадь / длина сегмента) × 100%",
                f"P = ({test['area']} / {test['segment']}) × 100 = {relative_area:.1f}%",
                f"{relative_area:.1f}%"
            )
        
        print_formula(
            "Определение кода",
            test['formula'],
            f"площадь={test['area']}м², cell_size={test['cell_size']}м",
            f"код {test['code']}, оценка {test['score']:.1f}"
        )
        
        code, score = analyzer.analyze_defects_on_segment(0, test["segment"])
        
        passed = (code == test['code'] and abs(score - test['score']) < 0.1)
        print_test_result(test['code'], test['score'], code, score, passed)


def test_subsidence():
    """Тест просадок (коды 18-20)"""
    print_header("ТЕСТ 4: ПРОСАДКИ (коды 18-20)")
    
    test_cases = [
        {
            "code": 18,
            "score": 1.2,
            "area": 15,
            "segment": 100,
            "range": "10-20%",
            "formula": "относительная площадь = (площадь / длина) × 100%, 10-20%",
            "description": "Просадки с относительной площадью 10-20%"
        },
        {
            "code": 19,
            "score": 0.9,
            "area": 35,
            "segment": 100,
            "range": "20-50%",
            "formula": "относительная площадь = (площадь / длина) × 100%, 20-50%",
            "description": "Просадки с относительной площадью 20-50%"
        },
        {
            "code": 20,
            "score": 0.5,
            "area": 60,
            "segment": 100,
            "range": ">50%",
            "formula": "относительная площадь = (площадь / длина) × 100%, >50%",
            "description": "Просадки с относительной площадью более 50%"
        }
    ]
    
    for test in test_cases:
        print_section(f"Код {test['code']}: {test['description']}")
        
        analyzer = ODMDefectAnalyzer(debug=False)
        analyzer.add_defect(50, "subsidence", {"area": test["area"]})
        
        relative_area = (test["area"] / test["segment"]) * 100
        
        print(f"  Площадь просадок: {test['area']}м²")
        print(f"  Длина сегмента: {test['segment']}м")
        
        print_formula(
            "Относительная площадь просадок",
            "P = (площадь / длина сегмента) × 100%",
            f"P = ({test['area']} / {test['segment']}) × 100 = {relative_area:.1f}%",
            f"{relative_area:.1f}% → {test['range']}"
        )
        
        print_formula(
            "Определение кода",
            test['formula'],
            f"относительная площадь = {relative_area:.1f}%",
            f"код {test['code']}, оценка {test['score']:.1f}"
        )
        
        code, score = analyzer.analyze_defects_on_segment(0, test["segment"])
        
        passed = (code == test['code'] and abs(score - test['score']) < 0.1)
        print_test_result(test['code'], test['score'], code, score, passed)


def test_collapse():
    """Тест проломов (коды 21-23)"""
    print_header("ТЕСТ 5: ПРОЛОМЫ (коды 21-23)")
    
    test_cases = [
        {
            "code": 21,
            "score": 1.2,
            "area": 8,
            "segment": 100,
            "range": "5-10%",
            "formula": "относительная площадь = (площадь / длина) × 100%, 5-10%",
            "description": "Проломы с относительной площадью 5-10%"
        },
        {
            "code": 22,
            "score": 0.9,
            "area": 20,
            "segment": 100,
            "range": "10-30%",
            "formula": "относительная площадь = (площадь / длина) × 100%, 10-30%",
            "description": "Проломы с относительной площадью 10-30%"
        },
        {
            "code": 23,
            "score": 0.5,
            "area": 40,
            "segment": 100,
            "range": ">30%",
            "formula": "относительная площадь = (площадь / длина) × 100%, >30%",
            "description": "Проломы с относительной площадью более 30%"
        }
    ]
    
    for test in test_cases:
        print_section(f"Код {test['code']}: {test['description']}")
        
        analyzer = ODMDefectAnalyzer(debug=False)
        analyzer.add_defect(50, "collapse", {"area": test["area"]})
        
        relative_area = (test["area"] / test["segment"]) * 100
        
        print(f"  Площадь проломов: {test['area']}м²")
        print(f"  Длина сегмента: {test['segment']}м")
        
        print_formula(
            "Относительная площадь проломов",
            "P = (площадь / длина сегмента) × 100%",
            f"P = ({test['area']} / {test['segment']}) × 100 = {relative_area:.1f}%",
            f"{relative_area:.1f}% → {test['range']}"
        )
        
        print_formula(
            "Определение кода",
            test['formula'],
            f"относительная площадь = {relative_area:.1f}%",
            f"код {test['code']}, оценка {test['score']:.1f}"
        )
        
        code, score = analyzer.analyze_defects_on_segment(0, test["segment"])
        
        passed = (code == test['code'] and abs(score - test['score']) < 0.1)
        print_test_result(test['code'], test['score'], code, score, passed)


def test_potholes():
    """Тест выбоин (коды 24-27)"""
    print_header("ТЕСТ 6: ВЫБОИНЫ (коды 24-27)")
    
    test_cases = [
        {
            "code": 24,
            "score": 4.5,
            "distance": 25,
            "range": ">20м",
            "formula": "d > 20",
            "description": "Одиночные выбоины или расстояние более 20м"
        },
        {
            "code": 25,
            "score": 3.5,
            "distance": 15,
            "range": "10-20м",
            "formula": "10 ≤ d ≤ 20",
            "description": "Расстояние между выбоинами 10-20м"
        },
        {
            "code": 26,
            "score": 2.7,
            "distance": 7,
            "range": "4-10м",
            "formula": "4 ≤ d < 10",
            "description": "Расстояние между выбоинами 4-10м"
        },
        {
            "code": 27,
            "score": 2.2,
            "distance": 3,
            "range": "1-4м",
            "formula": "1 ≤ d < 4",
            "description": "Расстояние между выбоинами 1-4м"
        }
    ]
    
    for test in test_cases:
        print_section(f"Код {test['code']}: {test['description']}")
        
        analyzer = ODMDefectAnalyzer(debug=False)
        analyzer.add_defect(0, "pothole")
        analyzer.add_defect(test["distance"], "pothole")
        
        print(f"  Позиции выбоин: 0м и {test['distance']}м")
        
        print_formula(
            "Расстояние между выбоинами",
            "d = |x₂ - x₁|",
            f"d = |{test['distance']} - 0| = {test['distance']}м",
            f"{test['distance']}м → {test['range']}"
        )
        
        print_formula(
            "Определение кода",
            test['formula'],
            f"{test['distance']}м {test['range']}",
            f"код {test['code']}, оценка {test['score']:.1f}"
        )
        
        code, score = analyzer.analyze_defects_on_segment(0, 100)
        
        passed = (code == test['code'] and abs(score - test['score']) < 0.1)
        print_test_result(test['code'], test['score'], code, score, passed)


def test_other_defects():
    """Тест прочих дефектов (коды 28-29)"""
    print_header("ТЕСТ 7: ПРОЧИЕ ДЕФЕКТЫ (коды 28-29)")
    
    test_cases = [
        {
            "code": 28,
            "score": 3.0,
            "type": "sealed_crack",
            "name": "Заделанные выбоины, залитые трещины",
            "formula": "Фиксированное значение по таблице ОДМ",
            "description": "Участки с заделанными выбоинами или залитыми трещинами"
        },
        {
            "code": 29,
            "score": 2.4,
            "type": "wave",
            "name": "Поперечные волны, сдвиги",
            "formula": "Фиксированное значение по таблице ОДМ",
            "description": "Поперечные волны и сдвиги покрытия"
        }
    ]
    
    for test in test_cases:
        print_section(f"Код {test['code']}: {test['name']}")
        
        analyzer = ODMDefectAnalyzer(debug=False)
        analyzer.add_defect(50, test["type"])
        
        print(f"  Дефект: {test['description']}")
        
        print_formula(
            "Определение кода",
            test['formula'],
            f"Обнаружен {test['name']}",
            f"код {test['code']}, оценка {test['score']:.1f}"
        )
        
        code, score = analyzer.analyze_defects_on_segment(0, 100)
        
        passed = (code == test['code'] and abs(score - test['score']) < 0.1)
        print_test_result(test['code'], test['score'], code, score, passed)


def test_combined_scenarios():
    """Тест комбинированных сценариев (выбор минимальной оценки)"""
    print_header("ТЕСТ 8: КОМБИНИРОВАННЫЕ СЦЕНАРИИ (выбор минимальной оценки)")
    
    test_cases = [
        {
            "name": "Поперечные трещины (4.6) + Продольная центральная (4.5) → мин 4.5",
            "defects": [
                ("crack_transverse", 1),
                ("crack_transverse", 11),
                ("crack_longitudinal_center", 16)
            ],
            "expected_code": 10,
            "expected_score": 4.5,
            "formula": "min(4.6, 4.5) = 4.5",
            "description": "Выбирается наименьшая оценка из всех дефектов на сегменте"
        },
        {
            "name": "Выбоины (3.5) + Сетка трещин (2.5) → мин 2.5",
            "defects": [
                ("pothole", 10),
                ("pothole", 25),
                ("crack_grid", 50, {"area": 7, "cell_size": 0.4})  # area=7, не густая сетка
            ],
            "expected_code": 13,
            "expected_score": 2.5,
            "formula": "min(3.5, 2.5) = 2.5",
            "description": "Выбирается наименьшая оценка из всех дефектов на сегменте"
        },
        {
            "name": "Проломы (0.9) + Поперечные трещины (4.3) → мин 0.9",
            "defects": [
                ("collapse", 30, {"area": 15}),
                ("crack_transverse", 5),
                ("crack_transverse", 13)
            ],
            "expected_code": 22,
            "expected_score": 0.9,
            "formula": "min(4.3, 0.9) = 0.9",
            "description": "Выбирается наименьшая оценка из всех дефектов на сегменте"
        },
        {
            "name": "Выбоины (4.5) + Сетка трещин густая (2.0) → мин 2.0",
            "defects": [
                ("pothole", 10),  # одиночная выбоина -> код 24, оценка 4.5
                ("crack_grid", 50, {"area": 9.5, "cell_size": 0.25})  # густая сетка -> код 14, оценка 2.0
            ],
            "expected_code": 14,
            "expected_score": 2.0,
            "formula": "min(4.5, 2.0) = 2.0",
            "description": "Густая сетка имеет более низкую оценку"
        }
    ]
    
    for test in test_cases:
        print_section(test["name"])
        
        analyzer = ODMDefectAnalyzer(debug=False)
        
        for defect in test["defects"]:
            defect_type = defect[0]
            position = defect[1]
            data = defect[2] if len(defect) > 2 else {}
            analyzer.add_defect(position, defect_type, data)
            print(f"  Дефект: {defect_type} на {position}м" + (f", {data}" if data else ""))
        
        print(f"\n  {Colors.BOLD}Формула: {test['formula']}{Colors.END}")
        
        code, score = analyzer.analyze_defects_on_segment(0, 100)
        
        passed = (code == test['expected_code'] and abs(score - test['expected_score']) < 0.1)
        print_test_result(test['expected_code'], test['expected_score'], code, score, passed)


def print_odm_table():
    """Вывод полной таблицы ОДМ с формулами"""
    print_header("ТАБЛИЦА ДЕФЕКТОВ ОДМ С ФОРМУЛАМИ")
    
    categories = {
        "Поперечные трещины (коды 1-9)": {
            "formula": "Код определяется по минимальному расстоянию между трещинами",
            "ranges": [
                (1, ">40м", 5.0),
                (2, "20-40м", 4.9),
                (3, "10-20м", 4.6),
                (4, "8-10м", 4.3),
                (5, "6-8м", 3.9),
                (6, "4-6м", 3.6),
                (7, "3-4м", 3.2),
                (8, "2-3м", 2.9),
                (9, "1-2м", 2.6),
            ]
        },
        "Продольные трещины (коды 10-11)": {
            "formula": "Фиксированные значения по таблице",
            "ranges": [
                (10, "Продольная центральная трещина", 4.5),
                (11, "Продольные боковые трещины", 3.5),
            ]
        },
        "Сетка трещин (коды 12-17)": {
            "formula": "Код определяется по площади и размеру ячеек",
            "ranges": [
                (12, "Площадь ≤10м², ячейки >0.5м", 3.0),
                (13, "Площадь ≤10м², ячейки <0.5м (обычная)", 2.5),
                (14, "Площадь ≥8м², ячейки ≤0.4м (густая)", 2.0),
                (15, "Площадь >10м², относительная площадь 10-30%", 2.3),
                (16, "Площадь >10м², относительная площадь 30-60%", 1.9),
                (17, "Площадь >10м², относительная площадь 60-90%", 1.6),
            ]
        },
        "Просадки (коды 18-20)": {
            "formula": "Код определяется по относительной площади: P = (площадь / длина) × 100%",
            "ranges": [
                (18, "Относительная площадь 10-20%", 1.2),
                (19, "Относительная площадь 20-50%", 0.9),
                (20, "Относительная площадь >50%", 0.5),
            ]
        },
        "Проломы (коды 21-23)": {
            "formula": "Код определяется по относительной площади: P = (площадь / длина) × 100%",
            "ranges": [
                (21, "Относительная площадь 5-10%", 1.2),
                (22, "Относительная площадь 10-30%", 0.9),
                (23, "Относительная площадь >30%", 0.5),
            ]
        },
        "Выбоины (коды 24-27)": {
            "formula": "Код определяется по минимальному расстоянию между выбоинами",
            "ranges": [
                (24, "Расстояние >20м", 4.5),
                (25, "Расстояние 10-20м", 3.5),
                (26, "Расстояние 4-10м", 2.7),
                (27, "Расстояние 1-4м", 2.2),
            ]
        },
        "Прочие дефекты (коды 28-29)": {
            "formula": "Фиксированные значения по таблице",
            "ranges": [
                (28, "Карты заделанных выбоин, залитые трещины", 3.0),
                (29, "Поперечные волны, сдвиги", 2.4),
            ]
        }
    }
    
    for category, info in categories.items():
        print(f"\n{Colors.YELLOW}{Colors.BOLD}{category}{Colors.END}")
        print(f"  {Colors.CYAN}Формула: {info['formula']}{Colors.END}")
        print(f"  {'Код':<6} {'Оценка':<8} {'Условие'}")
        print(f"  {'-'*50}")
        
        for code, condition, score in info["ranges"]:
            if score >= 4.0:
                color = Colors.GREEN
            elif score >= 3.0:
                color = Colors.YELLOW
            else:
                color = Colors.RED
            
            print(f"  {color}{code:<6} {score:<8.1f} {condition}{Colors.END}")


def run_all_tests():
    """Запуск всех тестов"""
    print_header("ПОЛНОЕ ТЕСТИРОВАНИЕ ВСЕХ КОДОВ ДЕФЕКТОВ ОДМ")
    
    # Выводим таблицу с формулами
    print_odm_table()
    
    # Запускаем все тесты
    test_transverse_cracks()
    test_longitudinal_cracks()
    test_crack_grid()
    test_subsidence()
    test_collapse()
    test_potholes()
    test_other_defects()
    test_combined_scenarios()
    
    print_header("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")


if __name__ == "__main__":
    run_all_tests()