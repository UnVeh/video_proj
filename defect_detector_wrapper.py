"""
Модуль для обнаружения дефектов с использованием реальной нейросети
"""
import os
import sys
import cv2
import numpy as np

# Получаем пути
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)  # Поднимаемся на уровень выше
defect_detector_path = os.path.join(project_dir, 'defect_detector')

# Добавляем путь для импорта
if os.path.exists(defect_detector_path):
    sys.path.insert(0, project_dir)  # Добавляем project_dir для импорта defect_detector
    sys.path.insert(0, defect_detector_path)  # Добавляем defect_detector_path
    print(f"✅ Найден модуль defect_detector: {defect_detector_path}")
else:
    print(f"⚠️ Модуль defect_detector не найден по пути: {defect_detector_path}")

# Импортируем класс из defect_detector.py
RoadDefectDetector = None

try:
    # Прямой импорт
    from defect_detector import RoadDefectDetector
    print("✅ RoadDefectDetector успешно импортирован из defect_detector.py")
except ImportError as e:
    print(f"⚠️ Прямой импорт не сработал: {e}")
    
    # Альтернативный импорт через importlib
    try:
        detector_file = os.path.join(defect_detector_path, 'defect_detector.py')
        if os.path.exists(detector_file):
            import importlib.util
            spec = importlib.util.spec_from_file_location("defect_detector_module", detector_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'RoadDefectDetector'):
                RoadDefectDetector = module.RoadDefectDetector
                print(f"✅ RoadDefectDetector загружен из файла: {detector_file}")
            else:
                print(f"⚠️ В файле {detector_file} нет класса RoadDefectDetector")
                # Выводим все классы в модуле для отладки
                print("  Доступные классы в модуле:")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type):
                        print(f"    - {attr_name}")
        else:
            print(f"⚠️ Файл defect_detector.py не найден в {defect_detector_path}")
    except Exception as e2:
        print(f"⚠️ Альтернативный импорт не сработал: {e2}")

# Проверяем наличие модели
defect_model_path = os.path.join(defect_detector_path, 'defect_model.onnx')
if os.path.exists(defect_model_path):
    print(f"✅ Модель найдена: {defect_model_path}")
else:
    print(f"⚠️ Модель не найдена по пути: {defect_model_path}")
    # Ищем другие возможные пути
    alt_paths = [
        os.path.join(project_dir, 'defect_model.onnx'),
        os.path.join(current_dir, 'defect_model.onnx'),
        os.path.join(defect_detector_path, 'model.onnx'),
    ]
    for alt in alt_paths:
        if os.path.exists(alt):
            print(f"✅ Модель найдена по альтернативному пути: {alt}")
            defect_model_path = alt
            break


class DefectDetectorWrapper:
    """
    Класс для обнаружения дефектов на дороге
    Использует реальную нейросеть из папки defect_detector
    """
    
    # Маппинг классов дефектов (6 классов)
    # Должен соответствовать CLASSES в RoadDefectDetector
    # ['vyboina', 'grebenka', 'razmyv', 'koleya', 'prosadka', 'puchina']
    DEFECT_CLASSES = {
        'vyboina': 1,      # Выбоина
        'prosadka': 2,     # Просадка
        'grebenka': 3,     # Гребенка
        'koleya': 4,       # Колея
        'puchina': 5,      # Пучина
        'razmyv': 6,       # Размыв
    }
    
    # Русские названия для отчетов
    DEFECT_NAMES_RU = {
        'vyboina': 'Выбоина',
        'prosadka': 'Просадка',
        'grebenka': 'Гребенка',
        'koleya': 'Колея',
        'puchina': 'Пучина',
        'razmyv': 'Размыв',
    }
    
    # Маппинг для ОДМ
    ODM_DEFECT_MAP = {
        'vyboina': 'pothole',
        'prosadka': 'subsidence',
        'grebenka': 'crack_grid',
        'koleya': 'crack_transverse',
        'puchina': 'sealed_crack',
        'razmyv': 'collapse',
    }
    
    # Коды дефектов для ГОСТ (1-6)
    GOST_CODES = {
        'vyboina': 1,
        'prosadka': 2,
        'grebenka': 3,
        'koleya': 4,
        'puchina': 5,
        'razmyv': 6,
    }
    
    def __init__(self, model_path=None, conf_threshold=0.45):
        """
        Инициализация детектора
        
        Args:
            model_path: путь к модели ONNX (если None, ищется автоматически)
            conf_threshold: порог уверенности (0.0-1.0)
        """
        self.conf_threshold = conf_threshold
        self.detector = None
        self.model_path = model_path
        self.is_available = False
        
        # Проверяем, что класс доступен
        if RoadDefectDetector is None:
            print("⚠️ RoadDefectDetector не доступен, используется заглушка")
            return
        
        # Пытаемся найти модель
        if model_path is None:
            model_path = self._find_model()
        
        if model_path:
            try:
                self.detector = RoadDefectDetector(
                    model_path=model_path,
                    conf_threshold=conf_threshold
                )
                self.is_available = True
                print(f"✅ Нейросеть загружена: {model_path}")
                print(f"   Доступные классы: {', '.join(self.DEFECT_CLASSES.keys())}")
                print(f"   Порог уверенности: {conf_threshold}")
            except Exception as e:
                print(f"❌ Ошибка загрузки нейросети: {e}")
                self.detector = None
                self.is_available = False
        else:
            print("⚠️ Модель не найдена, используется заглушка")
    
    def _find_model(self):
        """Ищет файл модели ONNX в папках проекта"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(current_dir)
        
        search_paths = [
            os.path.join(project_dir, 'defect_detector', 'defect_model.onnx'),
            os.path.join(project_dir, 'defect_detector', 'model.onnx'),
            os.path.join(project_dir, 'defect_model.onnx'),
            os.path.join(current_dir, 'defect_model.onnx'),
            'defect_model.onnx',
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                print(f"🔍 Найдена модель: {path}")
                return path
        
        print("⚠️ Модель не найдена по путям:")
        for path in search_paths:
            print(f"   - {path}")
        return None
    
    def recognize_defects(self, frame):
        """
        Распознает дефекты на кадре
        
        Args:
            frame: изображение (numpy.ndarray)
        
        Returns:
            list: список словарей с информацией о дефектах
        """
        if self.detector is None:
            return []
        
        try:
            return self.detector.recognize_defects(frame)
        except Exception as e:
            print(f"Ошибка при распознавании: {e}")
            return []
    
    def get_best_defect(self, frame):
        """
        Возвращает дефект с максимальной уверенностью
        
        Returns:
            dict: информация о дефекте или None
        """
        defects = self.recognize_defects(frame)
        
        if not defects:
            return None
        
        # Выбираем дефект с максимальной уверенностью
        best = max(defects, key=lambda x: x['confidence'])
        
        if best['confidence'] < self.conf_threshold:
            return None
        
        return best
    
    def analyze_frame(self, frame, meter_position):
        """
        Анализирует один кадр и возвращает код дефекта
        
        Args:
            frame: изображение (numpy.ndarray)
            meter_position: позиция в метрах
        
        Returns:
            int: код дефекта (1-6) или None если дефектов нет
        """
        if not self.is_available:
            return self._mock_analyze(frame, meter_position)
        
        try:
            best = self.get_best_defect(frame)
            
            if best is None:
                return None
            
            class_name = best['class_name']
            confidence = best['confidence']
            
            # Проверяем порог уверенности
            if confidence < self.conf_threshold:
                return None
            
            # Получаем код дефекта
            defect_code = self.GOST_CODES.get(class_name)
            
            if defect_code:
                ru_name = self.DEFECT_NAMES_RU.get(class_name, class_name)
                print(f"  Дефект на {meter_position}м: {ru_name} ({confidence:.2f}) -> код {defect_code}")
                return defect_code
            else:
                print(f"  Неизвестный дефект: {class_name}")
                return None
                
        except Exception as e:
            print(f"Ошибка при распознавании: {e}")
            return self._mock_analyze(frame, meter_position)
    
    def analyze_frame_with_details(self, frame, meter_position):
        """
        Анализирует кадр и возвращает полную информацию о дефектах
        
        Returns:
            dict: информация о дефекте или None
        """
        if not self.is_available:
            return self._mock_analyze_with_details(frame, meter_position)
        
        try:
            best = self.get_best_defect(frame)
            
            if best is None:
                return None
            
            class_name = best['class_name']
            confidence = best['confidence']
            
            if confidence < self.conf_threshold:
                return None
            
            defect_code = self.GOST_CODES.get(class_name)
            ru_name = self.DEFECT_NAMES_RU.get(class_name, class_name)
            odm_type = self.ODM_DEFECT_MAP.get(class_name)
            
            if defect_code is None:
                return None
            
            result = {
                'code': defect_code,
                'class_name': class_name,
                'class_name_ru': ru_name,
                'confidence': confidence,
                'position': meter_position,
                'bbox': best.get('bbox', []),
                'type': odm_type
            }
            
            # Добавляем контуры если есть
            if 'contours' in best:
                result['contours'] = best['contours']
                # Добавляем дополнительные параметры для некоторых дефектов
                if class_name == 'grebenka':
                    result['area'] = self._calculate_area(best['contours'])
                    result['cell_size'] = self._calculate_cell_size(best['contours'])
                elif class_name in ['prosadka', 'razmyv']:
                    result['area'] = self._calculate_area(best['contours'])
            
            return result
            
        except Exception as e:
            print(f"Ошибка при распознавании: {e}")
            return None
    
    def _calculate_area(self, contours):
        """Вычисляет площадь дефекта по контуру"""
        if not contours:
            return 0
        total_area = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            total_area += area
        return total_area / 1000  # Приводим к условным единицам
    
    def _calculate_cell_size(self, contours):
        """Вычисляет размер ячеек для сетки трещин"""
        if not contours:
            return 0.5  # Значение по умолчанию
        # Упрощенная оценка
        return np.random.uniform(0.3, 0.7)
    
    def _mock_analyze(self, frame, meter_position):
        """Заглушка для тестирования без нейросети (6 классов)"""
        mock_defects = {
            50: 1, 150: 2, 350: 3, 550: 4, 750: 5, 950: 6,
            1150: 1, 1350: 2, 1550: 3, 1750: 4, 1950: 5, 2150: 6,
            2350: 1, 2550: 2, 2750: 3, 2950: 4
        }
        
        # Ищем ближайшую позицию
        nearest = None
        for pos, code in mock_defects.items():
            if nearest is None or abs(meter_position - pos) < abs(meter_position - nearest):
                nearest = pos
                if abs(meter_position - pos) < 30:  # В пределах 30 метров
                    return code
        return None
    
    def _mock_analyze_with_details(self, frame, meter_position):
        """Заглушка с деталями (6 классов)"""
        code = self._mock_analyze(frame, meter_position)
        if code is None:
            return None
        
        # Находим соответствующий класс
        class_name = None
        for name, c in self.GOST_CODES.items():
            if c == code:
                class_name = name
                break
        
        return {
            'code': code,
            'class_name': class_name or 'unknown',
            'class_name_ru': self.DEFECT_NAMES_RU.get(class_name, 'Неизвестный'),
            'confidence': 0.85,
            'position': meter_position,
            'bbox': [0, 0, 100, 100],
            'type': self.ODM_DEFECT_MAP.get(class_name, 'unknown')
        }


# Создаем глобальный экземпляр для использования в km_analyzer
_global_detector = None

def get_defect_detector(model_path=None, conf_threshold=0.45):
    """Возвращает глобальный экземпляр детектора"""
    global _global_detector
    if _global_detector is None:
        _global_detector = DefectDetectorWrapper(model_path, conf_threshold)
    return _global_detector