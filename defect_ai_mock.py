import random



DEFECT_CODES = {
    1: "выбоина",
    2: "пролом",
    3: "просадка",
    4: "сдвиг волна",
    5: "гребенки",
    6: "колея",
    7: "необработанные места выпотевания вяжущего"
}

# Маппинг кодов ГОСТ к типам дефектов ОДМ
GOST_TO_ODM_TYPE = {
    1: "pothole",           # выбоина
    2: "collapse",          # пролом
    3: "subsidence",        # просадка
    4: "wave",              # сдвиг волна
    5: "crack_grid",        # гребенки -> сетка трещин
    6: "crack_transverse",  # колея -> поперечная трещина
    7: "sealed_crack",      # выпотевание -> залитая трещина
}

# Дополнительные параметры для разных типов дефектов (для имитации)
DEFECT_PARAMETERS = {
    "crack_grid": {
        "area_range": (5, 15),      # площадь в м²
        "cell_size_range": (0.2, 0.8)  # размер ячейки в м
    },
    "collapse": {
        "area_range": (5, 25)       # площадь в м²
    },
    "subsidence": {
        "area_range": (10, 30)      # площадь в м²
    }
}


class DefectAIMock:
    """
    Мок нейросети для распознавания дефектов
    В реальном приложении здесь будет вызов обученной модели
    """
    
    def __init__(self, detection_probability=0.1):
        """
        Args:
            detection_probability: вероятность обнаружения дефекта (0-1)
        """
        self.detection_probability = detection_probability
        
        
    def analyze_frame(self, frame, km_meter):
        """
        Анализирует кадр и возвращает код обнаруженного дефекта
        
        Args:
            frame: кадр видео (numpy array)
            km_meter: текущий метраж в метрах
            
        Returns:
            int: код дефекта (1-7) или None если дефект не обнаружен
        """
        # имитируем случайное обнаружение
        if random.random() < self.detection_probability:
            return random.randint(1, 7)
        return None
    
    def analyze_frame_with_params(self, frame, km_meter):
        """
        Анализирует кадр и возвращает дефект с параметрами для ОДМ
        
        Args:
            frame: кадр видео
            km_meter: текущий метраж
            
        Returns:
            dict: {
                "code": int,           # код дефекта ГОСТ
                "type": str,           # тип дефекта ОДМ
                "position": float,     # позиция в метрах
                "area": float,         # площадь (для некоторых дефектов)
                "cell_size": float     # размер ячейки (для сетки трещин)
            } или None
        """
        code = self.analyze_frame(frame, km_meter)
        
        if code is None:
            return None

        
        # Преобразуем в тип ОДМ
        odm_type = GOST_TO_ODM_TYPE.get(code, "unknown")
        
        result = {
            "code": code,
            "type": odm_type,
            "position": km_meter
        }
        
        # Добавляем дополнительные параметры для некоторых типов
        if odm_type in DEFECT_PARAMETERS:
            params = DEFECT_PARAMETERS[odm_type]
            
            if "area_range" in params:
                area_range = params["area_range"]
                result["area"] = random.uniform(*area_range)
            
            if "cell_size_range" in params:
                cell_size_range = params["cell_size_range"]
                result["cell_size"] = random.uniform(*cell_size_range)
        
        return result
    
    def analyze_sequence(self, frames_data):
        """
        Анализирует последовательность кадров и группирует одинаковые дефекты
        
        Args:
            frames_data: [(frame, meter), ...]
            
        Returns:
            list: [(start_m, end_m, defect_code), ...] - сгруппированные участки
        """
        results = []
        current_defect = None
        start_m = None
        
        for frame, meter in frames_data:
            defect = self.analyze_frame(frame, meter)
            
            if defect != current_defect:
                # закрываем предыдущий участок
                if current_defect is not None:
                    results.append((start_m, meter, current_defect))
                
                # начинаем новый
                if defect is not None:
                    start_m = meter
                
                current_defect = defect
        
        # закрываем последний
        if current_defect is not None and frames_data:
            results.append((start_m, frames_data[-1][1], current_defect))
        
        return results
    
    def analyze_sequence_with_params(self, frames_data):
        """
        Анализирует последовательность кадров с параметрами для ОДМ
        
        Args:
            frames_data: [(frame, meter), ...]
            
        Returns:
            list: список словарей с параметрами дефектов
        """
        results = []
        
        for frame, meter in frames_data:
            defect = self.analyze_frame_with_params(frame, meter)
            if defect:
                results.append(defect)
        
        return results
    
    @staticmethod
    def get_defect_name(code):
        """Возвращает название дефекта по коду"""
        return DEFECT_CODES.get(code, "неизвестно")
    
