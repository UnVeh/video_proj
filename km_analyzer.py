import cv2
import numpy as np
import subprocess

from detect2 import KmExtractor
from defect_ai_mock import DefectAIMock


def format_km(value):
    try:
        value = float(value)
        km = int(value)
        m = int(round((value - km) * 1000))
        return f"{km}+{m:03d}"
    except:
        return None

def get_first_frame(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, frame = cap.read()
    cap.release()

    return frame if ret else None

def get_last_frame(video_path):
    try:
        cmd = [
            "ffmpeg",
            "-sseof", "-0.1",
            "-i", video_path,
            "-vframes", "1",
            "-f", "image2pipe",
            "-vcodec", "png",
            "-"
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        data = proc.stdout.read()

        if data:
            return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)

    except:
        pass

    # fallback 
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cap.set(cv2.CAP_PROP_POS_FRAMES, max(total - 1, 0))
    ret, frame = cap.read()
    cap.release()

    return frame if ret else None

def analyze_video(video_path):
    extractor = KmExtractor(video_path)

    first = get_first_frame(video_path)
    last = get_last_frame(video_path)

    if first is None or last is None:
        return None, None, "Не удалось получить кадры"

    km1 = extractor.extract_kilometer(extractor.ocr_multi(first))
    km2 = extractor.extract_kilometer(extractor.ocr_multi(last))
    print("FIRST FRAME OK:", first is not None)
    print("LAST FRAME OK:", last is not None)

    text1 = extractor.ocr_multi(first)
    text2 = extractor.ocr_multi(last)

    print("OCR FIRST:", repr(text1))
    print("OCR LAST:", repr(text2))

    km1 = extractor.extract_kilometer(text1)
    km2 = extractor.extract_kilometer(text2)

    print("KM1:", km1)
    print("KM2:", km2)

    if not km1 or not km2:
        return None, None, "Километры не найдены"

    start = format_km(km1)
    end = format_km(km2)

    if not start or not end:
        return None, None, "Ошибка форматирования"

    return start, end, None

def run_ai_analysis(video_path, start, end):
    """
    Запускает AI анализ видео и возвращает данные для отчета
    
    Args:
        video_path: путь к видео
        start: начало в формате "км+ммм"
        end: конец в формате "км+ммм"
    
    Returns:
        list: список кортежей (start_m, end_m, defects_list)
        где defects_list содержит словари с информацией о дефектах:
        {
            "code": код дефекта (1-7),
            "position": положение в метрах,
            "type": тип дефекта (опционально),
            "area": площадь для сетки трещин (опционально),
            "cell_size": размер ячейки для сетки (опционально)
        }
    """
    def km_to_meters(value):
        km, m = map(int, value.split("+"))
        return km * 1000 + m

    ai = DefectAIMock()

    start_m = km_to_meters(start)
    end_m = km_to_meters(end)

    if end_m <= start_m:
        print("Ошибка: конец меньше начала")
        return []

    cap = cv2.VideoCapture(video_path)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        total_frames = 1

    # Собираем все дефекты с их позициями
    all_defects = []  # [(position, defect_dict), ...]
    
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Вычисляем текущую позицию в метрах
        meter = start_m + (end_m - start_m) * (frame_index / total_frames)
        meter = int(meter)

        # Получаем дефект от AI
        defect_code = ai.analyze_frame(frame, meter)

        if defect_code is not None:
            # Создаем информацию о дефекте
            defect_info = {
                "code": defect_code,
                "position": meter,
                "type": _get_defect_type(defect_code)
            }
            
            # Добавляем дополнительные данные для специфических дефектов
            if defect_code == 5:  # гребенки -> сетка трещин
                # Имитируем данные о площади и размере ячейки
                defect_info["area"] = np.random.uniform(5, 15)  # площадь в м²
                defect_info["cell_size"] = np.random.uniform(0.3, 0.7)  # размер ячейки в м
            
            elif defect_code in [2, 3]:  # проломы и просадки
                # Имитируем площадь дефекта
                defect_info["area"] = np.random.uniform(2, 20)  # площадь в м²
            
            all_defects.append((meter, defect_info))

        frame_index += 1

    cap.release()
    
    # Группируем дефекты в сегменты по 100 метров для совместимости с существующим кодом
    STEP = 100
    segments = {}
    
    for m in range(start_m, end_m, STEP):
        segment_end = min(m + STEP, end_m)
        segments[(m, segment_end)] = []
    
    # Распределяем дефекты по сегментам
    for position, defect_info in all_defects:
        segment_index = (position - start_m) // STEP
        key = (start_m + segment_index * STEP,
               min(start_m + (segment_index + 1) * STEP, end_m))
        
        if key in segments:
            segments[key].append(defect_info)
    
    # Возвращаем сегменты с дефектами
    # Формат: [(start_m, end_m, [defect_infos]), ...]
    return [(s, e, defects) for (s, e), defects in segments.items()]


def _get_defect_type(defect_code):
    """Преобразует код дефекта в тип для ОДМ анализа"""
    type_mapping = {
        1: "pothole",           # выбоина
        2: "collapse",          # пролом
        3: "subsidence",        # просадка
        4: "wave",              # сдвиг волна
        5: "crack_grid",        # гребенки -> сетка трещин
        6: "crack_transverse",  # колея -> поперечная трещина
        7: "sealed_crack",      # выпотевание -> залитая трещина
    }
    return type_mapping.get(defect_code, "unknown")