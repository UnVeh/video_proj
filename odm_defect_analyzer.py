from collections import defaultdict
from typing import List, Dict, Tuple, Optional, Any

# Коды и баллы дефектов по ОДМ
ODM_DEFECTS = {
    1: {"name": "Без дефектов и поперечные одиночные трещины > 40 м", "score": 5.0},
    2: {"name": "Поперечные одиночные трещины 20-40 м", "score": 4.9},
    3: {"name": "Поперечные одиночные трещины 10-20 м", "score": 4.6},
    4: {"name": "Поперечные редкие трещины 8-10 м", "score": 4.3},
    5: {"name": "Поперечные трещины 6-8 м", "score": 3.9},
    6: {"name": "Поперечные трещины 4-6 м", "score": 3.6},
    7: {"name": "Поперечные частые трещины 3-4 м", "score": 3.2},
    8: {"name": "Поперечные частые трещины 2-3 м", "score": 2.9},
    9: {"name": "Поперечные частые трещины 1-2 м", "score": 2.6},
    10: {"name": "Продольная центральная трещина", "score": 4.5},
    11: {"name": "Продольные боковые трещины", "score": 3.5},
    12: {"name": "Одиночная сетка трещин до 10 м с крупными ячейками >0.5 м", "score": 3.0},
    13: {"name": "Одиночная сетка трещин до 10 м с мелкими ячейками <0.5 м", "score": 2.5},
    14: {"name": "Густая сетка трещин до 10 м", "score": 2.0},
    15: {"name": "Сетка трещин >10 м, площадь 10-30%", "score": 2.3},
    16: {"name": "Сетка трещин >10 м, площадь 30-60%", "score": 1.9},
    17: {"name": "Сетка трещин >10 м, площадь 60-90%", "score": 1.6},
    18: {"name": "Просадки, площадь 10-20%", "score": 1.2},
    19: {"name": "Просадки, площадь 20-50%", "score": 0.9},
    20: {"name": "Просадки, площадь >50%", "score": 0.5},
    21: {"name": "Проломы, площадь 5-10%", "score": 1.2},
    22: {"name": "Проломы, площадь 10-30%", "score": 0.9},
    23: {"name": "Проломы, площадь >30%", "score": 0.5},
    24: {"name": "Одиночные выбоины >20 м", "score": 4.5},
    25: {"name": "Отдельные выбоины 10-20 м", "score": 3.5},
    26: {"name": "Редкие выбоины 4-10 м", "score": 2.7},
    27: {"name": "Частые выбоины 1-4 м", "score": 2.2},
    28: {"name": "Карты заделанных выбоин, залитые трещины", "score": 3.0},
    29: {"name": "Поперечные волны, сдвиги", "score": 2.4},
}


class ODMDefectAnalyzer:
    """
    Анализирует частоту появления дефектов и их размеры
    """
    
    def __init__(self, debug=False):
        self.defects_by_distance = defaultdict(list)  # {position: [defect_dict, ...]}
        self.debug = debug
        
    def log(self, message):
        if self.debug:
            print(f"    {message}")
    
    def clear(self):
        """Очищает данные анализа"""
        self.defects_by_distance.clear()
    
    def add_defect(self, distance_meters: float, defect_type: str, 
                   defect_data: Optional[Dict] = None):
        """
        Добавляет обнаруженный дефект для анализа
        
        Args:
            distance_meters: расстояние в метрах от начала
            defect_type: тип дефекта (crack_transverse, pothole, etc.)
            defect_data: дополнительные данные (area, cell_size и т.д.)
        """
        self.defects_by_distance[distance_meters].append({
            "type": defect_type,
            "data": defect_data or {}
        })
    
    def analyze_defects_on_segment(self, segment_start: float, segment_end: float) -> Tuple[Optional[int], float]:
        """
        Анализирует дефекты на заданном сегменте
        
        Формулы анализа:
        - Поперечные трещины: по минимальному расстоянию между трещинами
        - Сетка трещин: по площади и размеру ячеек
        - Выбоины: по минимальному расстоянию между выбоинами
        - Проломы/просадки: по относительной площади
        """
        segment_length = segment_end - segment_start
        
        # Собираем все дефекты на сегменте
        defects_in_segment = []
        for dist, defects in self.defects_by_distance.items():
            if segment_start <= dist <= segment_end:
                defects_in_segment.extend(defects)
        
        if not defects_in_segment:
            return 1, 5.0
        
        # Группируем дефекты по типу
        defects_by_type = defaultdict(list)
        for defect in defects_in_segment:
            defects_by_type[defect["type"]].append(defect)
        
        segment_scores = []
        segment_codes = []
        
        # 1. Анализ поперечных трещин (частота появления)
        if "crack_transverse" in defects_by_type:
            crack_positions = sorted([dist for dist, defects in self.defects_by_distance.items() 
                                     if any(d["type"] == "crack_transverse" for d in defects)])
            
            if len(crack_positions) >= 2:
                # Находим минимальное расстояние между трещинами
                min_distance = float('inf')
                for i in range(len(crack_positions) - 1):
                    dist_between = crack_positions[i+1] - crack_positions[i]
                    if dist_between < min_distance:
                        min_distance = dist_between
                
                self.log(f"Поперечные трещины: мин. расстояние = {min_distance:.1f}м")
                code, score = self._get_transverse_crack_code(min_distance)
                segment_codes.append(code)
                segment_scores.append(score)
            elif len(crack_positions) == 1:
                # Одиночная трещина
                code, score = 1, 5.0
                segment_codes.append(code)
                segment_scores.append(score)
        
        # 2. Анализ продольных трещин (фиксированные оценки)
        if "crack_longitudinal_center" in defects_by_type:
            segment_codes.append(10)
            segment_scores.append(4.5)
            self.log("Продольная центральная трещина → код 10, оценка 4.5")
        
        if "crack_longitudinal_side" in defects_by_type:
            segment_codes.append(11)
            segment_scores.append(3.5)
            self.log("Продольные боковые трещины → код 11, оценка 3.5")
        
        # 3. Анализ сетки трещин (площадь и размер ячеек)
        if "crack_grid" in defects_by_type:
            for defect in defects_by_type["crack_grid"]:
                data = defect.get("data", {})
                area = data.get("area", 0)
                cell_size = data.get("cell_size", 0.5)
                
                self.log(f"Сетка трещин: площадь={area:.1f}м², cell_size={cell_size:.2f}м")
                code, score = self._get_crack_grid_code(area, segment_length, cell_size)
                segment_codes.append(code)
                segment_scores.append(score)
        
        # 4. Анализ выбоин (частота появления)
        if "pothole" in defects_by_type:
            pothole_positions = sorted([dist for dist, defects in self.defects_by_distance.items() 
                                       if any(d["type"] == "pothole" for d in defects)])
            
            if len(pothole_positions) >= 2:
                min_distance = float('inf')
                for i in range(len(pothole_positions) - 1):
                    dist_between = pothole_positions[i+1] - pothole_positions[i]
                    if dist_between < min_distance:
                        min_distance = dist_between
                
                self.log(f"Выбоины: мин. расстояние = {min_distance:.1f}м")
                code, score = self._get_pothole_code(min_distance)
                segment_codes.append(code)
                segment_scores.append(score)
            elif len(pothole_positions) == 1:
                code, score = 24, 4.5  # Одиночная выбоина
                segment_codes.append(code)
                segment_scores.append(score)
        
        # 5. Анализ проломов (относительная площадь)
        if "collapse" in defects_by_type:
            collapse_area = sum(d.get("data", {}).get("area", 0) for d in defects_by_type["collapse"])
            if collapse_area > 0:
                relative_area = (collapse_area / segment_length) * 100
                self.log(f"Проломы: площадь={collapse_area:.1f}м² ({relative_area:.1f}%)")
                code, score = self._get_collapse_code(collapse_area, segment_length)
                segment_codes.append(code)
                segment_scores.append(score)
        
        # 6. Анализ просадок (относительная площадь)
        if "subsidence" in defects_by_type:
            subsidence_area = sum(d.get("data", {}).get("area", 0) for d in defects_by_type["subsidence"])
            if subsidence_area > 0:
                relative_area = (subsidence_area / segment_length) * 100
                self.log(f"Просадки: площадь={subsidence_area:.1f}м² ({relative_area:.1f}%)")
                code, score = self._get_subsidence_code(subsidence_area, segment_length)
                segment_codes.append(code)
                segment_scores.append(score)
        
        # 7. Волны/сдвиги (фиксированная оценка)
        if "wave" in defects_by_type:
            segment_codes.append(29)
            segment_scores.append(2.4)
            self.log("Поперечные волны/сдвиги → код 29, оценка 2.4")
        
        # 8. Заделанные выбоины/залитые трещины
        if "patched_pothole" in defects_by_type or "sealed_crack" in defects_by_type:
            segment_codes.append(28)
            segment_scores.append(3.0)
            self.log("Заделанные выбоины/залитые трещины → код 28, оценка 3.0")
        
        self.log(f"Все оценки: {[f'{s:.1f}' for s in segment_scores]}")
        
        # Выбираем минимальную оценку (наихудшее состояние)
        if not segment_scores:
            return 1, 5.0

        min_score = min(segment_scores)
        min_index = segment_scores.index(min_score)
        worst_code = segment_codes[min_index]
        
        self.log(f"Выбрана минимальная: {min_score:.1f} (код {worst_code})")
        
        return worst_code, min_score
    
    def _get_transverse_crack_code(self, distance_meters: float) -> Tuple[int, float]:
        """Поперечные трещины: код по расстоянию между трещинами"""
        if distance_meters > 40:
            return 1, 5.0
        elif 20 <= distance_meters <= 40:
            return 2, 4.9
        elif 10 <= distance_meters < 20:
            return 3, 4.6
        elif 8 <= distance_meters < 10:
            return 4, 4.3
        elif 6 <= distance_meters < 8:
            return 5, 3.9
        elif 4 <= distance_meters < 6:
            return 6, 3.6
        elif 3 <= distance_meters < 4:
            return 7, 3.2
        elif 2 <= distance_meters < 3:
            return 8, 2.9
        else:
            return 9, 2.6
    
    def _get_crack_grid_code(self, grid_area: float, segment_length: float, 
                        cell_size: float) -> Tuple[int, float]:
        """
        Определяет код для сетки трещин
        Формула: 
        - Если площадь <= 10м²:
            - Густая сетка (код 14, 2.0) если:
                * Площадь >= 8м² И cell_size <= 0.3м (более строгое условие)
                * ИЛИ это явно густая сетка с высокой плотностью
            - Если cell_size > 0.5м → код 12 (3.0)
            - Если cell_size <= 0.5м и не густая → код 13 (2.5)
        - Если площадь > 10м²:
            - relative_area = (grid_area / segment_length) * 100
            - Если 10-30% → код 15 (2.3)
            - Если 30-60% → код 16 (1.9)
            - Если 60-90% → код 17 (1.6)
        """
        self.log(f"[DEBUG] _get_crack_grid_code: area={grid_area}, cell_size={cell_size}")
        
        if grid_area <= 10:
            # Одиночная сетка до 10м²
            # Густая сетка (код 14) - более строгое условие
            if grid_area >= 9 and cell_size <= 0.3:
                self.log(f"[DEBUG] Густая сетка: area={grid_area}>=9 и cell_size={cell_size}<=0.3 → код 14")
                return 14, 2.0
            # Крупные ячейки (код 12)
            elif cell_size > 0.5:
                self.log(f"[DEBUG] Крупные ячейки: cell_size={cell_size}>0.5 → код 12")
                return 12, 3.0
            # Мелкие ячейки (код 13) - обычная сетка
            else:
                self.log(f"[DEBUG] Мелкие ячейки: cell_size={cell_size}<=0.5 → код 13")
                return 13, 2.5
        else:
            # Сетка на площади более 10м²
            relative_area = (grid_area / segment_length) * 100
            self.log(f"[DEBUG] Относительная площадь: {relative_area:.1f}%")
            if 10 <= relative_area < 30:
                return 15, 2.3
            elif 30 <= relative_area < 60:
                return 16, 1.9
            else:  # >= 60
                return 17, 1.6
    
    def _get_pothole_code(self, distance_meters: float) -> Tuple[int, float]:
        """Выбоины: код по расстоянию между выбоинами"""
        if distance_meters > 20:
            return 24, 4.5
        elif 10 <= distance_meters <= 20:
            return 25, 3.5
        elif 4 <= distance_meters < 10:
            return 26, 2.7
        else:
            return 27, 2.2
    
    def _get_collapse_code(self, collapse_area: float, segment_length: float) -> Tuple[int, float]:
        """Проломы: код по относительной площади"""
        if segment_length == 0:
            return 21, 1.2
        
        relative_area = (collapse_area / segment_length) * 100
        if 5 <= relative_area < 10:
            return 21, 1.2
        elif 10 <= relative_area < 30:
            return 22, 0.9
        else:
            return 23, 0.5
    
    def _get_subsidence_code(self, subsidence_area: float, segment_length: float) -> Tuple[int, float]:
        """Просадки: код по относительной площади"""
        if segment_length == 0:
            return 18, 1.2
        
        relative_area = (subsidence_area / segment_length) * 100
        if 10 <= relative_area < 20:
            return 18, 1.2
        elif 20 <= relative_area < 50:
            return 19, 0.9
        else:
            return 20, 0.5


def analyze_segments_with_defects(segments_data, segment_length=100):
    """
    Анализирует сегменты с дефектами
    
    Args:
        segments_data: список кортежей (start, end, defects_list)
        segment_length: длина сегмента в метрах
    
    Returns:
        список кортежей (start, end, (defect_code, score))
    """
    analyzer = ODMDefectAnalyzer(debug=False)
    
    for start, end, defects in segments_data:
        for defect in defects:
            if isinstance(defect, dict):
                position = defect.get("position", (start + end) / 2)
                defect_type = defect.get("type", "unknown")
                analyzer.add_defect(position, defect_type, defect)
    
    if not segments_data:
        return []
    
    total_start = min(s[0] for s in segments_data)
    total_end = max(s[1] for s in segments_data)
    
    result_segments = []
    current = total_start
    
    while current < total_end:
        segment_end = min(current + segment_length, total_end)
        defect_code, score = analyzer.analyze_defects_on_segment(current, segment_end)
        result_segments.append((int(current), int(segment_end), (defect_code, score)))
        current = segment_end
    
    return result_segments