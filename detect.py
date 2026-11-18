import cv2
import pytesseract
import re
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import Counter
import time


class KmExtractor:
    def __init__(self, video_path, use_paddleocr=True, frame_step=5, direction="forward"):
        self.video_path = video_path
        self.frame_step = frame_step
        self.direction = direction
        
        # Настройка Tesseract (для black_background)
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        self.tesseract_config = "--psm 6 --oem 1"
        
        # PaddleOCR (для overlay)
        self.use_paddleocr = use_paddleocr
        self.paddle_ocr = None
        if use_paddleocr:
            from paddleocr import PaddleOCR
            print("Инициализация PaddleOCR...")
            self.paddle_ocr = PaddleOCR(
                lang='ru',
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                # enable_mkldnn=False  # раскомментируйте, если PaddlePaddle 3.3.0
            )
            print("PaddleOCR инициализирован")
        
        # Храним историю километров
        self.km_history = []
        self.all_km_values = []
        self.raw_km_values = []
        
        # Для многопоточности
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.lock = threading.Lock()
        
        # Параметры ROI для overlay (PaddleOCR)
        self.roi_config_overlay = {
            'x_start': 0.0,
            'x_end': 0.15,
            'y_start': 0.0,
            'y_end': 0.05,
            'pre_scale': 3.0,
        }
        
        # Параметры ROI для black_background (Tesseract)
        self.roi_config_black = {
            'y_end_ratio': 0.15,
        }
        
        # Определенный шаг
        self.step = 0.010
        self.step_determined = False
        
        # Статистика
        self.stats = {
            'frames_processed': 0,
            'frames_skipped': 0,
            'ocr_calls': 0,
            'cache_hits': 0,
            'processing_time': 0,
            'paddle_frames': 0,
            'tesseract_frames': 0
        }
        
        self.last_processed_frame = -1
        
        # Тип видео
        self.video_type = None
        self.video_type_determined = False
    
    # ===== ОПРЕДЕЛЕНИЕ ТИПА ВИДЕО =====
    
    def determine_video_type(self, video_path, sample_frames=30):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return "overlay"
        
        black_bg_count = 0
        overlay_count = 0
        frame_count = 0
        
        while cap.isOpened() and frame_count < sample_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            video_type = self._detect_single_frame_type(frame)
            if video_type == "black_background":
                black_bg_count += 1
            else:
                overlay_count += 1
            
            frame_count += 1
        
        cap.release()
        
        total_frames_checked = black_bg_count + overlay_count
        
        # Защита от деления на ноль, если видео пустое или кадры не прочитались
        if total_frames_checked == 0:
            return "overlay"
            
        if black_bg_count / total_frames_checked > 0.6:
            return "black_background"
        else:
            return "overlay"
    
    def _detect_single_frame_type(self, frame):
        h, w = frame.shape[:2]
        roi = frame[0:int(h * 0.25), 0:w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        mean_brightness = np.mean(gray)
        dark_pixels = np.sum(gray < 50) / gray.size
        
        if mean_brightness < 80 and dark_pixels > 0.4:
            return "black_background"
        if mean_brightness < 60:
            return "black_background"
        
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist / hist.sum()
        
        if np.sum(hist[:30]) > 0.5:
            return "black_background"
        
        return "overlay"
    
    # ===== ROI МЕТОДЫ =====
    
    def get_roi_overlay(self, frame):
        h, w = frame.shape[:2]
        x_start = int(w * self.roi_config_overlay['x_start'])
        x_end = int(w * self.roi_config_overlay['x_end'])
        y_start = int(h * self.roi_config_overlay['y_start'])
        y_end = int(h * self.roi_config_overlay['y_end'])
        
        x_start = max(0, min(x_start, w-1))
        x_end = max(x_start+1, min(x_end, w))
        y_start = max(0, min(y_start, h-1))
        y_end = max(y_start+1, min(y_end, h))

        print(f"ROI: x={x_start}-{x_end} ({x_end-x_start}px), "
          f"y={y_start}-{y_end} ({y_end-y_start}px), "
          f"размер кадра: {w}x{h}")
        
        return frame[y_start:y_end, x_start:x_end]
    
    def get_roi_black_background(self, frame):
        h, w = frame.shape[:2]
        return frame[0:int(h * self.roi_config_black['y_end_ratio']), :]
    
    # ===== ПРЕДОБРАБОТКА =====
    
    def preprocess_black_background(self, roi):
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh
    
    def preprocess_scale(self, roi):
        scale = self.roi_config_overlay['pre_scale']
        if scale != 1.0:
            return cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        return roi
    
    def preprocess_hsv_orange(self, roi):
        scale = self.roi_config_overlay['pre_scale']
        if scale != 1.0:
            enlarged = cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        else:
            enlarged = roi.copy()
        
        hsv = cv2.cvtColor(enlarged, cv2.COLOR_BGR2HSV)
        lower_orange = np.array([10, 100, 100])
        upper_orange = np.array([35, 255, 255])
        mask = cv2.inRange(hsv, lower_orange, upper_orange)
        
        kernel = np.ones((2, 2), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask_inv = cv2.bitwise_not(mask)
        
        return cv2.cvtColor(mask_inv, cv2.COLOR_GRAY2BGR)
    
    def preprocess_clahe(self, roi):
        scale = self.roi_config_overlay['pre_scale']
        if scale != 1.0:
            enlarged = cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        else:
            enlarged = roi.copy()
        
        lab = cv2.cvtColor(enlarged, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    # ===== OCR МЕТОДЫ =====
    
    def ocr_black_background(self, image):
        if image is None or image.size == 0:
            return ""
        
        try:
            text = pytesseract.image_to_string(
                image,
                lang="rus+eng",
                config=self.tesseract_config
            )
            text = re.sub(r"\s+", " ", text.strip())
            return text
        except Exception as e:
            return ""
    
    def run_paddle_ocr(self, image):
        if self.paddle_ocr is None:
            return ""
        
        try:
            result = self.paddle_ocr.predict(input=image)
            texts = []
            for res in result:
                if isinstance(res, dict):
                    rec_texts = res.get('rec_texts', [])
                else:
                    rec_texts = res.get('rec_texts', []) if hasattr(res, 'get') else []
                texts.extend(rec_texts)
            text = " ".join(texts)
            return re.sub(r"\s+", " ", text.strip())
        except Exception as e:
            return ""
    
    # ===== ИЗВЛЕЧЕНИЕ КИЛОМЕТРОВ =====
    
    def fix_ocr_digits(self, text):
        """Исправляет типичные OCR-ошибки в числовых фрагментах"""
        if not text:
            return text
        
        def replace_in_match(m):
            s = m.group(0)
            # Заменяем буквы, похожие на цифры, ТОЛЬКО в начале числа
            s = re.sub(r'^[DdOoCcСс]', '0', s)
            s = re.sub(r'^[lIiІі]', '1', s)
            return s
        
        return re.sub(r'[DdOoCcСсIiLlІі]?[.,]?\d+[.,]\d{3}', replace_in_match, text)
    
    def extract_kilometer(self, text):
        if not text:
            return None
        
        text_lower = text.lower()
        
        # 1. Приоритет: число + "км"/"km"/"mm"/"hm"
        km_patterns = [
            r'(\d+[.,]\d{3})\s*[кk][мm]',
            r'(\d+[.,]\d{3})\s*[кk][мm]\b',
            r'(\d+[.,]\d{3})\s*[mм][mм]',
            r'(\d+[.,]\d{3})\s*[hн][мm]',
        ]
        
        for pattern in km_patterns:
            match = re.search(pattern, text_lower)
            if match:
                val = match.group(1).replace(",", ".")
                try:
                    num = float(val)
                    if 0 <= num <= 10:
                        return val
                except:
                    pass
        
        # 2. Без "км" — ищем число 0.000-10.0
        all_matches = list(re.finditer(r'(\d+[.,]\d{3})(?!\d)', text_lower))
        
        for m in all_matches:
            val_str = m.group(1)
            val = val_str.replace(",", ".")
            try:
                num = float(val)
                if not (0 <= num <= 10):
                    continue
                
                idx = m.start()
                before = text_lower[max(0, idx-25):idx]
                
                # Проверяем ТОЛЬКО before на координатные символы
                if '°' in before or "'" in before or '"' in before:
                    continue
                
                # Проверяем ТОЛЬКО before на "Широта"/"Долгота"
                if re.search(r'[шш]ирот|[дд]олгот|1iap|llp0|wpor|шир|долг|1mp0|шpoт|kapp|кстa',
                            before, re.IGNORECASE):
                    continue
                
                # Принимаем любое число 0.000-10.0, если before чист
                return val
                
            except:
                pass
        
        return None
    
    def extract_kilometer_smart(self, text, current_frame):
        """Умное извлечение с сохранением в историю"""
        text_fixed = self.fix_ocr_digits(text)
        km = self.extract_kilometer(text_fixed)
        
        if km:
            try:
                val = float(km)
                if 0 <= val <= 10:
                    with self.lock:
                        self.raw_km_values.append((current_frame, val, km))
                    return km
            except:
                pass
        
        return None
    
    # ===== КОМБИНИРОВАННЫЙ ПАЙПЛАЙН ДЛЯ OVERLAY =====
    
    def process_overlay_frame(self, frame, frame_num):
        """
        Комбинированный пайплайн для overlay:
        scale → hsv_orange → clahe (первое валидное значение)
        """
        roi = self.get_roi_overlay(frame)
        
        # A: scale
        text_scale = self.run_paddle_ocr(self.preprocess_scale(roi))
        km_scale = self.extract_kilometer(self.fix_ocr_digits(text_scale))
        if km_scale is not None:
            self.stats['paddle_frames'] += 1
            return {'text': text_scale, 'km': km_scale, 'variant': 'scale'}
        
        # B: hsv_orange
        text_hsv = self.run_paddle_ocr(self.preprocess_hsv_orange(roi))
        km_hsv = self.extract_kilometer(self.fix_ocr_digits(text_hsv))
        if km_hsv is not None:
            self.stats['paddle_frames'] += 1
            return {'text': text_hsv, 'km': km_hsv, 'variant': 'hsv_orange'}
        
        # C: clahe
        text_clahe = self.run_paddle_ocr(self.preprocess_clahe(roi))
        km_clahe = self.extract_kilometer(self.fix_ocr_digits(text_clahe))
        if km_clahe is not None:
            self.stats['paddle_frames'] += 1
            return {'text': text_clahe, 'km': km_clahe, 'variant': 'clahe'}
        
        self.stats['paddle_frames'] += 1
        return {
            'text': text_scale or text_hsv or text_clahe,
            'km': None,
            'variant': 'none'
        }
    
    # ===== ФИЛЬТРАЦИЯ И ВОССТАНОВЛЕНИЕ =====
    
    def determine_step_from_values(self, values):
        if len(values) < 2:
            return 0.010 * (-1 if self.direction == "reverse" else 1)
        
        sorted_values = sorted(values)
        diffs = []
        
        for i in range(1, len(sorted_values)):
            diff = sorted_values[i] - sorted_values[i-1]
            if 0.001 < abs(diff) < 0.1:
                diffs.append(abs(diff))  # берём модуль
        
        if not diffs:
            return 0.010 * (-1 if self.direction == "reverse" else 1)
        
        step_groups = {'0.005': [], '0.010': []}
        
        for diff in diffs:
            if abs(diff - 0.005) <= 0.002:
                step_groups['0.005'].append(diff)
            elif abs(diff - 0.010) <= 0.003:
                step_groups['0.010'].append(diff)
        
        max_count = 0
        best_step = 0.010
        
        for step_name, step_diffs in step_groups.items():
            if len(step_diffs) > max_count:
                max_count = len(step_diffs)
                best_step = float(step_name)
        
        if max_count < 2:
            avg_diff = sum(diffs) / len(diffs)
            best_step = 0.005 if abs(avg_diff - 0.005) < abs(avg_diff - 0.010) else 0.010
        
        # Знак зависит от направления
        return best_step * (-1 if self.direction == "reverse" else 1)
    
    def filter_km_values(self):
        if len(self.raw_km_values) < 2:
            return
        
        self.raw_km_values.sort(key=lambda x: x[0])
        
        all_km_values = [km for _, km, _ in self.raw_km_values]
        self.step = self.determine_step_from_values(all_km_values)
        self.step_determined = True
        
        print(f"  Определен шаг: {self.step:.3f} км/кадр (direction={self.direction})")
        
        filtered_values = [self.raw_km_values[0]]
        
        for i in range(1, len(self.raw_km_values)):
            frame, km, raw_str = self.raw_km_values[i]
            prev_frame, prev_km, _ = self.raw_km_values[i-1]
            
            frame_diff = frame - prev_frame
            if frame_diff > 0:
                expected_km_diff = frame_diff * self.step  # для reverse — отрицательный
                actual_km_diff = km - prev_km
                
                # Для forward и reverse проверка симметрична через abs
                if abs(actual_km_diff - expected_km_diff) <= abs(self.step) * 2.5:
                    filtered_values.append(self.raw_km_values[i])
                # Особый случай: переход через 0 (для forward) или через начало (для reverse)
                elif self.direction == "forward" and km < 0.01 and prev_km > 0.1:
                    filtered_values.append(self.raw_km_values[i])
                elif self.direction == "reverse" and km > 0.1 and prev_km < 0.01:
                    filtered_values.append(self.raw_km_values[i])
                else:
                    expected_km = prev_km + expected_km_diff
                    if abs(km - expected_km) <= abs(self.step) * 1.5:
                        filtered_values.append(self.raw_km_values[i])
        
        with self.lock:
            self.km_history = [(frame, km) for frame, km, _ in filtered_values]
            self.all_km_values = [km for _, km, _ in filtered_values]
        
        return filtered_values
    
    def restore_sequence(self, results, total_frames):
        self.filter_km_values()
        step = self.step  # для reverse — отрицательный
        
        if len(self.km_history) < 2:
            return results
        
        confident = {}
        for frame, km in self.km_history:
            confident[frame] = km
        
        confident_frames = sorted(confident.keys())
        
        if confident_frames:
            first_frame = confident_frames[0]
            first_val = confident[first_frame]
            
            # Для forward: до первого кадра — вычитаем step (уходим в прошлое)
            # Для reverse: до первого кадра — вычитаем step (но step отрицательный, значит прибавляем)
            for frame in range(first_frame - 1, -1, -1):
                if frame < len(results):
                    frame_diff = first_frame - frame
                    restored_val = round(first_val - frame_diff * step, 3)
                    
                    if self.direction == "forward":
                        # Для forward: если ушли в минус — стоп
                        if restored_val < 0:
                            if abs(restored_val) <= abs(step) * 2:
                                restored_val = 0.000
                            else:
                                if restored_val < -abs(step) * 3:
                                    break
                    else:
                        # Для reverse: если ушли выше максимума — стоп
                        if restored_val > 10:
                            break
                    
                    results[frame]['restored'] = restored_val
        
        for idx in range(len(confident_frames) - 1):
            frame1 = confident_frames[idx]
            frame2 = confident_frames[idx + 1]
            val1 = confident[frame1]
            
            for frame in range(frame1 + 1, frame2):
                if frame < len(results):
                    frame_offset = frame - frame1
                    restored_val = round(val1 + frame_offset * step, 3)
                    results[frame]['restored'] = restored_val
        
        if confident_frames:
            last_frame = confident_frames[-1]
            last_val = confident[last_frame]
            
            for frame in range(last_frame + 1, len(results)):
                frame_diff = frame - last_frame
                restored_val = round(last_val + frame_diff * step, 3)
                results[frame]['restored'] = restored_val
        
        return results
    
    def extract_km_fast(self, video_path, debug=False):
        """
        Анализ всего видео с шагом 5 (при неудаче — +1).
        Оба крайних кадра (0 и total_frames-1) анализируются обязательно
        для любого направления (forward или reverse).
        """
        if not self.video_type_determined:
            print("\nОпределение типа видео...")
            self.video_type = self.determine_video_type(video_path, sample_frames=30)
            self.video_type_determined = True
            print(f"Тип видео определен как: {self.video_type}")
        
        FRAME_STEP = 5
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None, None
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"\nВсего кадров: {total_frames}")
        print(f"Шаг после успеха: +{FRAME_STEP}, при неудаче: +1")
        print(f"Направление: {self.direction}")
        print(f"Анализ ВСЕГО видео (оба крайних кадра обязательны)")
        
        km_values = []
        analyzed_frames = set()
        
        # === ОБЯЗАТЕЛЬНЫЙ АНАЛИЗ ОБОИХ КРАЙНИХ КАДРОВ ===
        required_frames = [0, total_frames - 1]
        
        for req_frame in required_frames:
            if 0 <= req_frame < total_frames:
                analyzed_frames.add(req_frame)
                cap.set(cv2.CAP_PROP_POS_FRAMES, req_frame)
                ret, frame = cap.read()
                if ret:
                    print(f"\n--- КАДР {req_frame} (обязательный) ---")
                    result = self.process_frame(frame, req_frame)
                    print(f"  Текст: '{result['text'][:100]}'")
                    print(f"  КМ: {result['km']}")
                    
                    if result['km'] is not None:
                        try:
                            km = float(result['km'])
                            km_values.append((req_frame, km))
                            print(f"  ✓ ОБЯЗАТЕЛЬНЫЙ кадр {req_frame}: найдено {km}")
                        except:
                            pass
                    else:
                        print(f"  ✗ ОБЯЗАТЕЛЬНЫЙ кадр {req_frame}: не распознано")
        
        # === ОСНОВНОЙ ЦИКЛ ПО ВИДЕО ===
        frame_idx = 0
        
        while frame_idx < total_frames:
            if frame_idx in analyzed_frames:
                frame_idx += 1
                continue
            
            analyzed_frames.add(frame_idx)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break
            
            print(f"\n--- КАДР {frame_idx} ---")
            result = self.process_frame(frame, frame_idx)
            print(f"  Текст: '{result['text'][:100]}'")
            print(f"  КМ: {result['km']}")
            
            if result['km'] is not None:
                try:
                    km = float(result['km'])
                    km_values.append((frame_idx, km))
                    print(f"  ✓ Найдено {km} (всего: {len(km_values)})")
                    frame_idx += FRAME_STEP
                except:
                    frame_idx += 1
            else:
                print(f"  ✗ Не распознано, переходим к следующему")
                frame_idx += 1
        
        if debug:
            print("\n" + "=" * 60)
            print("ИТОГОВАЯ ДИАГНОСТИКА")
            print("=" * 60)
            print(f"Проанализировано кадров: {len(analyzed_frames)}")
            print(f"Всего найдено значений: {len(km_values)}")
            print("\nВсе найденные значения:")
            for f, k in sorted(km_values):
                print(f"  Кадр {f}: {k:.3f}")
        
        if len(km_values) < 2:
            print("Недостаточно значений для восстановления")
            cap.release()
            return None, None
        
        km_values.sort(key=lambda x: x[0])
        
        self.raw_km_values = [(frame, km, str(km)) for frame, km in km_values]
        self.filter_km_values()
        
        if not self.step_determined:
            self.step = 0.010 * (-1 if self.direction == "reverse" else 1)
            print(f"Шаг не определен, стандартный: {self.step}")
        else:
            print(f"Определен шаг: {self.step}")
        
        # Первый кадр (0)
        first_frame_real = next((km for f, km in km_values if f == 0), None)
        if first_frame_real is not None:
            first_restored = first_frame_real
            print(f"Первый кадр — РЕАЛЬНОЕ: {first_restored:.3f}")
        else:
            first_frame = km_values[0][0]
            first_km = km_values[0][1]
            first_restored = round(first_km - first_frame * self.step, 3)
            print(f"Первый кадр — ВОССТАНОВЛЕННОЕ: {first_restored:.3f}")
        
        # Последний кадр
        last_frame_real = next((km for f, km in km_values if f == total_frames - 1), None)
        if last_frame_real is not None:
            last_restored = last_frame_real
            print(f"Последний кадр — РЕАЛЬНОЕ: {last_restored:.3f}")
        else:
            last_frame = km_values[-1][0]
            last_km = km_values[-1][1]
            last_restored = round(last_km + (total_frames - 1 - last_frame) * self.step, 3)
            print(f"Последний кадр — ВОССТАНОВЛЕННОЕ: {last_restored:.3f}")
        
        print(f"\nРезультат:")
        print(f"  Первый кадр (0): {first_restored:.3f}")
        print(f"  Последний кадр ({total_frames-1}): {last_restored:.3f}")
        print(f"  Шаг: {self.step} (direction={self.direction})")
        
        cap.release()
        return first_restored, last_restored
    
    # ===== ОСНОВНЫЕ МЕТОДЫ =====
    
    def process_frame(self, frame, frame_num):
        if self.video_type == "black_background":
            # Tesseract для черной шапки
            roi = self.get_roi_black_background(frame)
            processed = self.preprocess_black_background(roi)
            
            text = self.ocr_black_background(processed)
            
            self.last_processed_frame = frame_num
            self.stats['tesseract_frames'] += 1
            ocr_used = "Tesseract"
            
            km = self.extract_kilometer_smart(text, frame_num)
            
            return {
                'text': text if text else "Текст не распознан",
                'km': km,
                'video_type': self.video_type,
                'ocr_used': ocr_used
            }
        else:
            # PaddleOCR (combined) для overlay
            result = self.process_overlay_frame(frame, frame_num)
            
            km = self.extract_kilometer_smart(result['text'], frame_num)
            
            return {
                'text': result['text'] if result['text'] else "Текст не распознан",
                'km': km,
                'video_type': self.video_type,
                'ocr_used': f"PaddleOCR ({result['variant']})"
            }
    
    def reset_history(self):
        with self.lock:
            self.km_history = []
            self.all_km_values = []
            self.raw_km_values = []
            self.step_determined = False
            self.last_processed_frame = -1
    
    def process_video_full(self, video_path, frame_interval=None, max_frames=None):
        if not self.video_type_determined:
            print("\nОпределение типа видео...")
            self.video_type = self.determine_video_type(video_path, sample_frames=30)
            self.video_type_determined = True
            print(f"Тип видео определен как: {self.video_type}")
        
        if frame_interval is None:
            frame_interval = 1
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        self.reset_history()
        frame_count = 0
        results = []
        processed_count = 0
        start_time = time.time()
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"\nВсего кадров: {total_frames}")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            result = self.process_frame(frame, frame_count)
            result['frame'] = frame_count
            result['restored'] = None
            results.append(result)
            processed_count += 1
            
            if processed_count % 50 == 0:
                print(f"Обработано кадров: {processed_count}")
            
            if max_frames and processed_count >= max_frames:
                break
            
            frame_count += 1
        
        cap.release()
        
        self.stats['processing_time'] = time.time() - start_time
        self.stats['frames_processed'] = processed_count
        
        self.filter_km_values()
        results = self.restore_sequence(results, len(results))
        
        print(f"\nОбработка завершена за {self.stats['processing_time']:.2f} сек")
        print(f"Обработано кадров: {processed_count}")
        print(f"PaddleOCR кадров: {self.stats['paddle_frames']}")
        print(f"Tesseract кадров: {self.stats['tesseract_frames']}")
        
        return results
    
    def set_roi(self, x_start=None, x_end=None, y_start=None, y_end=None, 
                use_percentage=True, pre_scale=2.0, ocr_max_height=200):
        """Настройка ROI для overlay"""
        if x_start is not None:
            self.roi_config_overlay['x_start'] = x_start
        if x_end is not None:
            self.roi_config_overlay['x_end'] = x_end
        if y_start is not None:
            self.roi_config_overlay['y_start'] = y_start
        if y_end is not None:
            self.roi_config_overlay['y_end'] = y_end
        if pre_scale is not None:
            self.roi_config_overlay['pre_scale'] = pre_scale
    
    def get_stats(self):
        return {
            'frames_processed': self.stats['frames_processed'],
            'frames_skipped': self.stats['frames_skipped'],
            'ocr_calls': self.stats['ocr_calls'],
            'cache_hits': self.stats['cache_hits'],
            'processing_time': self.stats['processing_time'],
            'fps': self.stats['frames_processed'] / self.stats['processing_time'] if self.stats['processing_time'] > 0 else 0,
            'step': self.step,
            'paddle_frames': self.stats['paddle_frames'],
            'tesseract_frames': self.stats['tesseract_frames'],
            'video_type': self.video_type
        }
    
    def __del__(self):
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)