import cv2
import numpy as np
import subprocess
import os

from detect import KmExtractor
from defect_detector_wrapper import get_defect_detector


def format_km(value):
    """
    Форматирование километража в формат "км+м" (например, 0.177 -> "0+177")
    """
    try:
        value = float(value)
        km = int(value)
        m = int(round((value - km) * 1000))
        return f"{km}+{m:03d}"
    except:
        return None


def km_to_meters(value):
    """
    Преобразование километража в метры
    """
    try:
        if isinstance(value, (int, float)):
            return int(value * 1000) if value < 1000 else int(value)
        if isinstance(value, str):
            if '+' in value:
                km, m = map(int, value.split("+"))
                return km * 1000 + m
            else:
                return int(float(value) * 1000)
        return 0
    except:
        return None


def meters_to_km(value):
    """
    Преобразование метров в формат "км+м"
    """
    try:
        value = int(value)
        return f"{value // 1000}+{value % 1000:03d}"
    except (ValueError, TypeError):
        return None


def get_first_frame(video_path):
    """Получение первого кадра видео"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, frame = cap.read()
    cap.release()

    return frame if ret else None


def get_last_frame(video_path):
    """Получение последнего кадра видео"""
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

    if total > 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(total - 1, 0))
        ret, frame = cap.read()
        cap.release()
        return frame if ret else None
    
    cap.release()
    return None


def analyze_video(video_path, use_paddleocr=True, tesseract_step=5, direction="forward"):
    """
    Анализ видео для определения начального и конечного километража.
    Анализируется ВСЁ видео (шаг +5 после успеха, +1 при неудаче).
    Для forward обязательно проверяется последний кадр,
    для reverse — первый кадр.
    """
    try:
        print(f"\nАнализ видео: {video_path}")
        print(f"  Направление: {direction}")
        
        extractor = KmExtractor(
            video_path,
            use_paddleocr=use_paddleocr,
            frame_step=tesseract_step,
            direction=direction
        )
        
        video_type = extractor.determine_video_type(video_path, sample_frames=30)
        extractor.video_type = video_type
        extractor.video_type_determined = True
        print(f"  Тип видео: {video_type}")
        
        first_km, last_km = extractor.extract_km_fast(video_path)
        
        print(f"  Первый км: {first_km}")
        print(f"  Последний км: {last_km}")
        
        if first_km is None or last_km is None:
            return None, None, f"Километры не найдены (first_km={first_km}, last_km={last_km})"
        
        start = format_km(first_km)
        end = format_km(last_km)
        
        if not start or not end:
            return None, None, "Ошибка форматирования"
        
        print(f"  Результат: start={start}, end={end}")
        
        return start, end, None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, None, f"Ошибка при анализе: {str(e)}"

def get_first_km_from_video(video_path, use_paddleocr=True, tesseract_step=5):
    """Получение километража на первом кадре через прямое распознавание"""
    try:
        # Получаем первый кадр
        frame = get_first_frame(video_path)
        if frame is None:
            return None
        
        # Создаем экстрактор
        extractor = KmExtractor(
            video_path,
            use_paddleocr=use_paddleocr,
            frame_step=tesseract_step
        )
        
        # Определяем тип видео
        video_type = extractor.determine_video_type(video_path, sample_frames=30)
        extractor.video_type = video_type
        extractor.video_type_determined = True
        
        # Обрабатываем кадр
        result = extractor.process_frame(frame, 0)
        
        if result['km'] is not None:
            try:
                return float(result['km'])
            except:
                pass
        
        return None
        
    except Exception as e:
        print(f"Ошибка при получении первого км: {e}")
        return None


def get_last_km_from_video(video_path, use_paddleocr=True, tesseract_step=5):
    """Получение километража на последнем кадре через прямое распознавание"""
    try:
        # Получаем последний кадр
        frame = get_last_frame(video_path)
        if frame is None:
            return None
        
        # Создаем экстрактор
        extractor = KmExtractor(
            video_path,
            use_paddleocr=use_paddleocr,
            frame_step=tesseract_step
        )
        
        # Определяем тип видео
        video_type = extractor.determine_video_type(video_path, sample_frames=30)
        extractor.video_type = video_type
        extractor.video_type_determined = True
        
        # Получаем общее количество кадров для правильного индекса
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if cap.isOpened() else 0
        cap.release()
        
        # Обрабатываем последний кадр
        result = extractor.process_frame(frame, max(total_frames - 1, 0))
        
        if result['km'] is not None:
            try:
                return float(result['km'])
            except:
                pass
        
        return None
        
    except Exception as e:
        print(f"Ошибка при получении последнего км: {e}")
        return None


def run_ai_analysis(video_path, start, end, video_start_meter=None, video_end_meter=None, direction="forward"):
    """
    Запускает AI анализ видео с использованием реальной нейросети.
    Поддерживает direction='forward' и 'reverse'.
    Для reverse start_m > end_m — это нормально, позиции идут от start_m к end_m.
    """
    try:
        detector = get_defect_detector(conf_threshold=0.45)

        if video_start_meter is not None and video_end_meter is not None:
            start_m = video_start_meter
            end_m = video_end_meter
        else:
            start_m = km_to_meters(start)
            end_m = km_to_meters(end)

        print(f"Анализ видео: {video_path}")
        print(f"start_m={start_m}, end_m={end_m}, direction={direction}")

        if start_m is None or end_m is None:
            print("Ошибка: некорректные значения границ километража")
            return []

        # Для forward end_m > start_m, для reverse end_m < start_m
        if direction == "forward" and end_m <= start_m:
            print("Ошибка: конец меньше начала (forward)")
            return []
        if direction == "reverse" and start_m <= end_m:
            print("Ошибка: начало меньше конца (reverse)")
            return []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Ошибка: не удалось открыть видео")
            return []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            total_frames = 1

        all_defects = []
        frame_index = 0
        step = max(1, total_frames // 100)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_index % step == 0:
                # Для forward: meter растёт от start_m к end_m
                # Для reverse: meter убывает от start_m к end_m
                ratio = frame_index / total_frames
                if direction == "forward":
                    meter = start_m + (end_m - start_m) * ratio
                else:  # reverse
                    meter = start_m - (start_m - end_m) * ratio
                meter = int(meter)

                defect_info = detector.analyze_frame_with_details(frame, meter)

                if defect_info is not None:
                    all_defects.append((meter, defect_info))
                    ru_name = defect_info.get('class_name_ru', defect_info.get('class_name', 'unknown'))
                    print(f"  Дефект на {meter}м: {ru_name} ({defect_info['confidence']:.2f})")

            frame_index += 1

        cap.release()

        print(f"Всего обнаружено дефектов: {len(all_defects)}")

        if not all_defects:
            return [(min(start_m, end_m), max(start_m, end_m), [])]

        # Сегментация по возрастанию
        seg_min = min(start_m, end_m)
        seg_max = max(start_m, end_m)
        STEP = 100

        segments = {}
        for m in range(seg_min, seg_max, STEP):
            segment_end = min(m + STEP, seg_max)
            segments[(m, segment_end)] = []

        for position, defect_info in all_defects:
            for (seg_start, seg_end) in segments.keys():
                if seg_start <= position < seg_end:
                    segments[(seg_start, seg_end)].append(defect_info)
                    break

        result = [(seg_start, seg_end, defects) for (seg_start, seg_end), defects in segments.items()]
        return result

    except Exception as e:
        print(f"Ошибка при AI анализе: {e}")
        import traceback
        traceback.print_exc()
        return []

def _get_defect_type(defect_code):
    """Преобразует код дефекта в тип для ОДМ анализа"""
    type_mapping = {
        1: "pothole",
        2: "subsidence",
        3: "crack_grid",
        4: "crack_transverse",
        5: "sealed_crack",
        6: "collapse",
    }
    return type_mapping.get(defect_code, "unknown")


def process_video_full(video_path, max_frames=None, use_paddleocr=True, tesseract_step=5):
    """
    Полная обработка видео с извлечением всех километров
    """
    try:
        extractor = KmExtractor(
            video_path,
            use_paddleocr=use_paddleocr,
            frame_step=tesseract_step
        )
        
        results = extractor.process_video_full(video_path, max_frames=max_frames)
        return results
    except Exception as e:
        print(f"Ошибка при обработке видео: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_video_info(video_path):
    """Получение информации о видео"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        info = {
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0
        }
        cap.release()
        return info
    except Exception as e:
        print(f"Ошибка при получении информации о видео: {e}")
        return None


def extract_km_from_frame(frame, use_paddleocr=True, tesseract_step=5):
    """Извлечение километража из одного кадра"""
    try:
        extractor = KmExtractor(
            "temp_video",
            use_paddleocr=use_paddleocr,
            frame_step=tesseract_step
        )
        
        video_type = extractor._detect_single_frame_type(frame)
        extractor.video_type = video_type
        extractor.video_type_determined = True
        
        result = extractor.process_frame(frame, 0)
        
        return {
            'km': result['km'],
            'text': result['text'],
            'video_type': video_type,
            'ocr_used': result['ocr_used']
        }
    except Exception as e:
        print(f"Ошибка при извлечении км из кадра: {e}")
        return {
            'km': None,
            'text': "",
            'video_type': "unknown",
            'ocr_used': "error"
        }