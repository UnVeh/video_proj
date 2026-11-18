import tkinter as tk
from tkinter import filedialog, ttk
import os
import sys
import re
import threading
from report_generator import generate_gost_report, generate_odm_report
from road_data import ROAD_LOCATION_MAP, LOCATION_ROADS_MAP, ALL_ROADS, ALL_LOCATIONS
from ui_components import (
    RoundedButtonImage, 
    IconManager
)

class App:
    def __init__(self, root=None, build_ui=True):
        self.root = root or tk.Tk()

        self.root.title("Приложение")
        self.root.geometry("1300x600")
        self.BG_COLOR = "#FEFEFF"
        self.root.configure(bg=self.BG_COLOR)

        self.icon_manager = IconManager()

        
        self.road_location_map = ROAD_LOCATION_MAP
        self.location_roads_map = LOCATION_ROADS_MAP
        self.all_roads = ALL_ROADS
        self.all_locations = ALL_LOCATIONS

        
        self.saved_settings = {}
        self.temp_settings = {}
        self.video_bounds = {}
        
        self.analysis_results = {}  
        self.analysis_completed = False
        self.video_paths = {}

        self.roads = [
            {
                "road_name": tk.StringVar(value=""),
                "road_location": tk.StringVar(value=""),
                "sections": [
                    {
                        'forward_videos': [],
                        'reverse_videos': []
                    }
                ]
            }
        ]
        
        
        self.error_var = tk.StringVar(master=self.root)
        self.current_screen = None
        self.analysis_completed = False
        
        if build_ui:
            self.show_second_screen()

    # UTILS
    def km_to_meters(self, value):
        try:
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                if '+' in value:
                    km, m = map(int, value.split("+"))
                    return km * 1000 + m
                else:
                    return int(value)
            return 0
        except:
            return 0
        
    def meters_to_km(self, value):
        value = int(value)
        return f"{value // 1000}+{value % 1000:03d}"
    
    
    def add_logo(self, parent):
        logo_width = 310
        logo_height = 55
        
        logo_frame = tk.Frame(parent, bg=self.BG_COLOR, highlightthickness=0)
        logo_frame.place(x=10, y=10, width=logo_width, height=logo_height)
        logo_frame.lift()
        logo_frame.pack_propagate(False)
        
        logo_path = os.path.join("icons", "logo.png")
        if os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk

                original_img = Image.open(logo_path)
                orig_width, orig_height = original_img.size

                ratio = min(logo_width / orig_width, logo_height / orig_height)
                new_width = int(orig_width * ratio)
                new_height = int(orig_height * ratio)

                img = original_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logo_img = ImageTk.PhotoImage(img)

                logo_label = tk.Label(logo_frame, image=logo_img, bg=self.BG_COLOR)
                logo_label.image = logo_img
                logo_label.pack(expand=True)  
                logo_label.lift()
                
            except Exception as e:
                print(f"Ошибка загрузки логотипа: {e}")
                logo_label = tk.Label(
                    logo_frame,
                    text="ЛОГО",
                    font=("Arial", 16, "bold"),
                    fg="#085492",
                    bg=self.BG_COLOR
                )
                logo_label.pack(expand=True, fill="both")
        else:
            logo_label = tk.Label(
                logo_frame,
                text="ЛОГО",
                font=("Arial", 16, "bold"),
                fg="#085492",
                bg=self.BG_COLOR
            )
            logo_label.pack(expand=True, fill="both")
            
    def create_linked_comboboxes(self, parent, road_name_var, road_location_var, width=34):
        road_frame = tk.Frame(parent, bg="white")
        road_frame.pack(expand=True, fill="both", padx=2)
        
        # Фрейм для местоположения
        location_frame = tk.Frame(parent, bg="white")
        location_frame.pack(expand=True, fill="both", padx=2)
        
        # Создаем комбобоксы
        from tkinter import ttk
        
        road_combo = ttk.Combobox(
            road_frame,
            textvariable=road_name_var,
            values=ALL_ROADS,
            state="readonly",
            font=("Arial", 10),
            width=width
        )
        road_combo.pack(side="left", fill="x", expand=True)
        
        # Кнопка сброса для дороги
        road_reset_btn = tk.Button(
            road_frame, 
            text="✖", 
            font=("Arial", 8), 
            width=2, 
            relief="flat",
            bg="#F1F4F7",
            command=lambda: self.reset_combobox(road_name_var, road_combo, True)
        )
        road_reset_btn.pack(side="right", padx=(2, 0))
        
        location_combo = ttk.Combobox(
            location_frame,
            textvariable=road_location_var,
            values=ALL_LOCATIONS,
            state="readonly",
            font=("Arial", 10),
            width=width
        )
        location_combo.pack(side="left", fill="x", expand=True)
        
        # Кнопка сброса для местоположения
        location_reset_btn = tk.Button(
            location_frame, 
            text="✖", 
            font=("Arial", 8), 
            width=2, 
            relief="flat",
            bg="#F1F4F7",
            command=lambda: self.reset_combobox(road_location_var, location_combo, False)
        )
        location_reset_btn.pack(side="right", padx=(2, 0))
        
        def on_road_select(event):
            """При выборе дороги"""
            selected_road = road_name_var.get()
            if selected_road and selected_road in ROAD_LOCATION_MAP:
                # Устанавливаем соответствующее местонахождение
                location = ROAD_LOCATION_MAP[selected_road]
                road_location_var.set(location)
                # Обновляем список местоположений 
                location_combo['values'] = [location]
        
        def on_location_select(event):
            """При выборе местонахождения"""
            selected_location = road_location_var.get()
            if selected_location and selected_location in LOCATION_ROADS_MAP:
                roads = LOCATION_ROADS_MAP[selected_location]
                # Обновляем список дорог (только для этого местонахождения)
                road_combo['values'] = roads
                if len(roads) == 1:
                    # Если только одна дорога, заполняем автоматически
                    road_name_var.set(roads[0])
                else:
                    # Если несколько дорог, очищаем поле дороги
                    road_name_var.set('')
        
        # Привязываем события
        road_combo.bind('<<ComboboxSelected>>', on_road_select)
        location_combo.bind('<<ComboboxSelected>>', on_location_select)
        
        # Сохраняем ссылки на комбобоксы для сброса
        road_combo.original_values = ALL_ROADS
        location_combo.original_values = ALL_LOCATIONS
        
        return road_combo, location_combo

    def reset_combobox(self, string_var, combo, is_road):
        """Сбрасывает выбранное значение в комбобоксе"""
        string_var.set('')
        combo['values'] = combo.original_values
        
        # Если сбрасываем дорогу, очищаем и местоположение
        if is_road:
            pass
        
    def create_linked_comboboxes_inline(self, col1, col2, road_name_var, road_location_var, width=32):
        """Связанные выпадающие списки в двух колонках с поддержкой Backspace для сброса"""
        from tkinter import ttk
        
        # Комбобокс для дороги
        road_combo = ttk.Combobox(
            col1,
            textvariable=road_name_var,
            values=ALL_ROADS,
            state="readonly",
            font=("Arial", 10),
            width=width
        )
        road_combo.place(relx=0.5, rely=0.5, anchor="center")
        
        # Комбобокс для местоположения
        location_combo = ttk.Combobox(
            col2,
            textvariable=road_location_var,
            values=ALL_LOCATIONS,
            state="readonly",
            font=("Arial", 10),
            width=width
        )
        location_combo.place(relx=0.5, rely=0.5, anchor="center")

        road_combo.original_values = ALL_ROADS.copy()
        location_combo.original_values = ALL_LOCATIONS.copy()
        
        def reset_road():
            """Сброс дороги"""
            road_name_var.set('')
            road_combo['values'] = road_combo.original_values
            if len(location_combo['values']) == 1 and location_combo['values'][0] in LOCATION_ROADS_MAP:
                location_combo['values'] = location_combo.original_values
        
        def reset_location():
            """Сброс местоположения"""
            road_location_var.set('')
            location_combo['values'] = location_combo.original_values
            road_combo['values'] = road_combo.original_values
            road_name_var.set('')
        
        def reset_both():
            """Сброс обоих комбобоксов"""
            reset_road()
            reset_location()
        
        def on_road_select(event):
            """При выборе дороги"""
            selected_road = road_name_var.get()
            if selected_road and selected_road in ROAD_LOCATION_MAP:
                # Устанавливаем соответствующее местонахождение
                location = ROAD_LOCATION_MAP[selected_road]
                road_location_var.set(location)
                # Обновляем список местоположений 
                location_combo['values'] = [location]
        
        def on_location_select(event):
            """При выборе местонахождения"""
            selected_location = road_location_var.get()
            if selected_location and selected_location in LOCATION_ROADS_MAP:
                roads = LOCATION_ROADS_MAP[selected_location]
                # Обновляем список дорог 
                road_combo['values'] = roads
                if len(roads) == 1:
                    # Если только одна дорога, заполняем автоматически
                    road_name_var.set(roads[0])
                else:
                    # Если несколько дорог, очищаем поле дороги
                    road_name_var.set('')
        
        def on_road_key(event):
            """Обработка нажатия клавиш для дороги"""
            if event.keysym == 'BackSpace':
                reset_road()
            elif event.keysym == 'Delete' and event.state & 0x0004:  
                reset_both()
        
        def on_location_key(event):
            """Обработка нажатия клавиш для местоположения"""
            if event.keysym == 'BackSpace':
                reset_location()
            elif event.keysym == 'Delete' and event.state & 0x0004:  
                reset_both()
        
        # Привязываем события
        road_combo.bind('<<ComboboxSelected>>', on_road_select)
        location_combo.bind('<<ComboboxSelected>>', on_location_select)
        road_combo.bind('<KeyRelease>', on_road_key)
        location_combo.bind('<KeyRelease>', on_location_key)
        
        # Фокус на комбобокс при клике
        def on_road_focus(event):
            road_combo.focus_set()
        
        def on_location_focus(event):
            location_combo.focus_set()
        
        road_combo.bind('<Button-1>', on_road_focus)
        location_combo.bind('<Button-1>', on_location_focus)
        
        return road_combo, location_combo
    
    def analyze_video_file(self, video_path, direction, road_section=None):
        from km_analyzer import analyze_video, run_ai_analysis, km_to_meters
        
        print(f"\n=== Анализ видео: {os.path.basename(video_path)} ===")
        print(f"  Направление: {direction}")

        # 1. Определение километров
        start, end, error = analyze_video(video_path, direction=direction)
        print(f"  Распознанные границы: {start} - {end}")
        
        if error:
            return {"error": error, "video_path": video_path}
        
        # 2. Пользовательские границы — используем ТОЛЬКО если они есть в saved_settings
        video_key = os.path.basename(video_path)
        user_start = None
        user_end = None
        
        if video_key in self.saved_settings:
            saved = self.saved_settings[video_key]
            user_start = saved.get("start")
            user_end = saved.get("end")
            print(f"  Найдены пользовательские границы (из настроек): {user_start} - {user_end}")
        else:
            print(f"  Пользовательские границы не заданы — используем распознанные")
        
        if user_start and user_end:
            start_m = km_to_meters(user_start)
            end_m = km_to_meters(user_end)
            print(f"  Используем пользовательские границы: {start_m}м - {end_m}м")
        else:
            start_m = km_to_meters(start)
            end_m = km_to_meters(end)
            print(f"  Используем распознанные границы: {start_m}м - {end_m}м")

        if start_m is None or end_m is None:
            return {"error": "Некорректные значения границ километража", "video_path": video_path}
        
        # 3. Анализ кадров
        ai_segments = run_ai_analysis(video_path, start, end, start_m, end_m, direction=direction)
        print(f"  Найдено сегментов с дефектами: {len(ai_segments)}")
        
        return {
            "start": start,
            "end": end,
            "direction": direction,
            "segments": ai_segments,
            "video_path": video_path,
            "user_start": user_start,
            "user_end": user_end,
            "is_mock": False
        }


    def start_video_analysis(self):
        """Запускает анализ ВСЕХ загруженных видео (прямых и обратных)"""
        import threading
        
        videos_to_analyze = []
        
        for road in self.roads:
            road_name = road["road_name"].get()
            if not road_name:
                continue
            
            section = road["sections"][0]
            
            for video in section['forward_videos']:
                if video:
                    videos_to_analyze.append({
                        "video": video,
                        "direction": "forward",
                        "road_name": road_name,
                        "section": section
                    })
            
            for video in section['reverse_videos']:
                if video:
                    videos_to_analyze.append({
                        "video": video,
                        "direction": "reverse",
                        "road_name": road_name,
                        "section": section
                    })
        
        if not videos_to_analyze:
            self.error_var.set("Нет видео для анализа. Добавьте видео прямого или обратного направления")
            return
        
        self.start_analysis_btn.config(state="disabled")
        self.to_report_btn.config(state="disabled")
        self.error_var.set(f"Анализ {len(videos_to_analyze)} видео...")
        
        def analyze_all():
            results = {}
            errors = []
            
            print(f"\n=== Запуск анализа {len(videos_to_analyze)} видео ===")
            
            for idx, item in enumerate(videos_to_analyze):
                video_name = item["video"]
                direction = item["direction"]
                section = item["section"]
                
                self.root.after(0, lambda v=video_name: self.error_var.set(f"Анализ видео: {v}..."))
                
                video_path = self.get_video_full_path(video_name)
                if not video_path:
                    errors.append(f"{video_name}: файл не найден")
                    print(f"  [ОШИБКА] Файл не найден: {video_name}")
                    continue
                
                print(f"\n--- Анализ видео {idx+1}/{len(videos_to_analyze)}: {video_name} ({direction}) ---")
                
                try:
                    result = self.analyze_video_file(video_path, direction, section)
                    
                    if "error" in result:
                        errors.append(f"{video_name}: {result['error']}")
                        print(f"  ОШИБКА: {result['error']}")
                    else:
                        results[video_name] = result
                        
                        # self.saved_settings[video_name] = {
                        #     "start": result["start"],
                        #     "end": result["end"]
                        # }
                        
                        from km_analyzer import km_to_meters
                        start_m = km_to_meters(result["start"])
                        end_m = km_to_meters(result["end"])
                        if start_m is not None and end_m is not None:
                            self.video_bounds[video_name] = {"start": start_m, "end": end_m}
                        else:
                            self.video_bounds.pop(video_name, None)
                        
                        print(f"  Успешно: {video_name}")
                        print(f"    Границы: {result['start']} - {result['end']}")
                        print(f"    Сегментов: {len(result['segments'])}")
                
                except Exception as e:
                    errors.append(f"{video_name}: {str(e)}")
                    print(f"  [ОШИБКА] {str(e)}")
            
            self.root.after(0, lambda: self.on_analysis_complete(results, errors))
        
        threading.Thread(target=analyze_all, daemon=True).start()



    def on_analysis_complete(self, results, errors):
        self.analysis_results = results
        self.analysis_completed = True
        
        if errors:
            self.error_var.set(f"Анализ завершен с ошибками: {', '.join(errors[:3])}")
        else:
            self.error_var.set(f"Анализ завершен. Обработано {len(results)} видео")
        
        # Разблокируем кнопки
        self.start_analysis_btn.config(state="normal")
        self.update_buttons_state()


    def get_reports_directory(self):
        """Возвращает путь к папке для сохранения отчетов"""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        reports_dir = os.path.join(base_dir, "app_reports")
        
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        return reports_dir


    def store_video_path(self, video_name, full_path):
        if not hasattr(self, 'video_paths'):
            self.video_paths = {}
        self.video_paths[video_name] = full_path
        
    def get_video_direction(self, video_name):
        """Определяет направление видео (forward/reverse)"""
        for road in self.roads:
            section = road["sections"][0]
            if video_name in section['forward_videos']:
                return "forward"
            if video_name in section['reverse_videos']:
                return "reverse"
        return "forward"  # по умолчанию
    
    def get_reports_directory(self):
        if getattr(sys, 'frozen', False):
            # Запущено как exe
            base_dir = os.path.dirname(sys.executable)
        else:
            # Запущено как скрипт
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        reports_dir = os.path.join(base_dir, "app_reports")

        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            print(f"Создана папка для отчетов: {reports_dir}")
        
        return reports_dir
    
    def get_video_full_path(self, video_name):
        if not video_name:
            return None

        if hasattr(self, 'video_paths') and video_name in self.video_paths:
            path = self.video_paths[video_name]
            if os.path.exists(path):
                return path

        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        full_path = os.path.join(base_dir, video_name)
        if os.path.exists(full_path):
            return full_path

        if os.path.exists(video_name):
            return video_name

        user_dirs = [
            os.path.expanduser("~/Videos"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            os.getcwd(),
            base_dir
        ]
        
        for dir_path in user_dirs:
            full_path = os.path.join(dir_path, video_name)
            if os.path.exists(full_path):
                self.store_video_path(video_name, full_path)
                return full_path
        
        print(f"  [ОШИБКА] Файл не найден: {video_name}")
        return None

    def _is_allowed_directory(self, path):
        """Проверяет, разрешена ли директория для работы"""
        allowed = [
            os.path.expanduser("~/Videos"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            os.getcwd(),
            os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else ""
        ]
        return any(path.startswith(allowed_dir) for allowed_dir in allowed if allowed_dir)

    # экран с таблицей
    def show_second_screen(self):
        self.clear()
        self.current_screen = "second"
        
        # self.analysis_completed = False
        
        # Основной контейнер
        main_container = tk.Frame(self.root, bg=self.BG_COLOR)
        main_container.pack(fill="both", expand=True, padx=20, pady=(30,10))
        
        # Заголовок
        tk.Label(
            main_container,
            bg=self.BG_COLOR
        ).pack(pady=(0, 20))
        
        # Таблица
        self.table_frame = tk.Frame(main_container, bg=self.BG_COLOR)
        self.table_frame.pack(fill="both", expand=True)
        
        self.create_table()
        
        # Нижняя панель с кнопками
        bottom_frame = tk.Frame(main_container, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", fill="x", pady=20)
        
        button_container = tk.Frame(bottom_frame, bg=self.BG_COLOR)
        button_container.pack()
        
        self.start_analysis_btn = RoundedButtonImage(
            button_container,
            text="Начать анализ",
            command=self.start_analysis,
            width=150,
            height=45,
            radius=15,
            bg_color="#F1F4F7", 
            hover_color="#C6D6EB",
            text_color="#1E1D26",
            font=("Arial", 11, "bold"),
            border_width=2,           
            border_color="#085492"
        )
        self.start_analysis_btn.pack(side="left", padx=120)
        
        self.to_report_btn = RoundedButtonImage(
            button_container,
            text="Перейти к созданию отчета",
            
            command=self.show_report_screen,
            width=250,
            height=45,
            radius=15,
            bg_color="#5BB5FF", 
            hover_color="#4492F8",
            text_color="white",
            font=("Arial", 11, "bold"),
            border_width=2,           
            border_color="#085492"
        )
        self.to_report_btn.pack(side="left", padx=10)
        
        tk.Label(bottom_frame, bg=self.BG_COLOR, textvariable=self.error_var, fg="red", 
                font=("Arial", 9)).pack(pady=5)
        
        self.update_buttons_state()
        self.add_logo(self.root)
    

    
    def create_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()
            
        canvas = tk.Canvas(self.table_frame, bg=self.BG_COLOR, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.table_frame, orient="vertical", command=canvas.yview)
        
        # Создаем фрейм внутри canvas, который будет прокручиваться
        scrollable_frame = tk.Frame(canvas, bg=self.BG_COLOR)
        
        # Функция обновления scrollregion
        def update_scrollregion(event=None):
            """Обновляет область прокрутки"""
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", update_scrollregion)
        
        # Создаем окно в canvas для scrollable_frame
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Обновляем ширину окна при изменении размера canvas
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas_width)
        
        canvas.configure(yscrollcommand=scrollbar.set)

        headers_frame = tk.Frame(scrollable_frame, bg="#085492", height=40)
        headers_frame.pack(fill="x")
        headers_frame.pack_propagate(False)

        headers_inner = tk.Frame(headers_frame, bg="#5BB5FF")
        headers_inner.pack(fill="both", expand=True, padx=2, pady=(2,0))

        col_widths = [0.25, 0.25, 0.25, 0.25]

        headers = [
            "Наименование дороги",
            "Местонахождение дороги",
            "Прямое направление",
            "Обратное направление"
        ]

        for i, header in enumerate(headers):
            x_pos = sum(col_widths[:i])
            col_frame = tk.Frame(headers_inner, bg="#5BB5FF")
            col_frame.place(
                relx=x_pos,
                rely=0,
                relwidth=col_widths[i],
                relheight=1
            )

            if i < len(headers) - 1:
                sep = tk.Frame(headers_inner, bg="#085492", width=2)
                sep.place(
                    relx=x_pos + col_widths[i],
                    rely=0,
                    relheight=1
                )

            tk.Label(
                col_frame,
                text=header,
                font=("Arial", 11, "bold"),
                fg="white",
                bg="#5BB5FF",
                anchor="center"
            ).pack(expand=True, fill="both")

        for i in range(1, len(col_widths)):
            x_pos = sum(col_widths[:i])
            sep = tk.Frame(headers_inner, bg="#085492", width=2)
            sep.place(relx=x_pos, rely=0, relheight=1)
            sep.lift()

        header_bottom_border = tk.Frame(
            scrollable_frame,
            bg="#085492",
            height=2
        )
        header_bottom_border.pack(fill="x")

        self.rows_container = tk.Frame(scrollable_frame, bg="#085492")
        self.rows_container.pack(fill="both", expand=True)

        self.create_merged_table()

        add_road_btn = RoundedButtonImage(
            scrollable_frame,
            text="Добавить дорогу",
            command=self.add_road,
            width=200,
            height=40,
            radius=15,
            bg_color="#5BB5FF", 
            hover_color="#4492F8",
            text_color="white",
            font=("Arial", 11, "bold"),
            border_width=2,           
            border_color="#085492"
        )
        add_road_btn.pack(pady=15)
        
        # Размещаем canvas и scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Настраиваем прокрутку колесиком мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # Сохраняем ссылки для возможного использования
        self.table_canvas = canvas
        self.table_scrollbar = scrollbar
        self.scrollable_frame = scrollable_frame
        
        # Принудительно обновляем scrollregion после создания
        self.root.update_idletasks()
        update_scrollregion()

    def create_merged_table(self):
        row_height = 70
        # Удаляем старые виджеты, если есть
        if hasattr(self, 'rows_container'):
            for w in self.rows_container.winfo_children():
                w.destroy()

        total_rows = 0

        for road in self.roads:

            section = road["sections"][0]

            rows_count = max(1, len(section['forward_videos'])
            )

            total_rows += rows_count

        total_height = total_rows * row_height

        table_body = tk.Frame(
            self.rows_container,
            bg="#085492",
            height=total_height + 2
        )

        table_body.pack(fill="x")
        table_body.pack_propagate(False)

        content = tk.Frame(
            table_body,
            bg="white"
        )

        content.place(
            x=2,
            y=2,
            relwidth=1,
            width=-4,
            relheight=1,
            height=-4
        )

        current_y = 0


        for road in self.roads:

            section = road["sections"][0]

            rows_count = max(
                1,
                len(section['forward_videos'])
            )

            block_height = rows_count * row_height

            # Создаем контейнер для двух выпадающих списков
            col_container = tk.Frame(content, bg="white")
            col_container.place(
                relx=0,
                y=current_y,
                relwidth=0.5,
                height=block_height
            )

            # Создаем фреймы для каждой колонки внутри контейнера
            col1 = tk.Frame(col_container, bg="white")
            col1.place(relx=0, rely=0, relwidth=0.5, relheight=1)

            col2 = tk.Frame(col_container, bg="white")
            col2.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)

            # Создаем связанные выпадающие списки
            self.create_linked_comboboxes_inline(col1, col2, road["road_name"], road["road_location"], 32)

            for idx in range(rows_count):

                y = current_y + idx * row_height

                row_frame = tk.Frame(
                    content,
                    bg="white",
                    height=row_height
                )

                row_frame.place(
                    relx=0.5,
                    y=y,
                    relwidth=0.5
                )

                # 3 колонка
                col3 = tk.Frame(row_frame, bg="white")
                col3.place(
                    relx=0,
                    rely=0,
                    relwidth=0.5,
                    relheight=1
                )

                # Получаем видео для прямого направления по индексу
                forward_video = None
                if idx < len(section['forward_videos']):
                    forward_video = section['forward_videos'][idx]

                # Проверяем, есть ли кнопка "Добавить участок дороги" в этой строке
                has_add_button = (idx == len(section['forward_videos']) - 1 and len(section['forward_videos']) > 0)

                # Если нет видео для этой строки
                if forward_video is None:
                    RoundedButtonImage(
                        col3,
                        text="Выбрать видео",
                        command=lambda s=section, i=idx: self.select_forward_video_for_row(s, i),
                        width=170,
                        height=35,
                        radius=15,
                        bg_color="#5BB5FF",
                        hover_color="#4492F8",
                        text_color="white",
                        font=("Arial", 9, "bold"),
                        border_width=2,
                        border_color="#085492"
                    ).place(relx=0.5, rely=0.5, anchor="center")

                # Если видео есть для этой строки
                else:
                    # Создаем контейнер для имени видео и кнопки удаления
                    content_container = tk.Frame(col3, bg="white")
                    
                    # Выбираем позицию в зависимости от наличия кнопки "Добавить участок дороги"
                    if has_add_button:
                        # Если есть кнопка добавления, поднимаем выше
                        content_container.place(relx=0.5, rely=0.30, anchor="center")
                    else:
                        # Если нет кнопки, центрируем
                        content_container.place(relx=0.5, rely=0.5, anchor="center")
                    
                    tk.Label(
                        content_container,
                        text=forward_video,
                        font=("Arial", 10),
                        bg="white"
                    ).pack(side="left", padx=(0, 10))
                    
                    delete_btn = self.icon_manager.create_icon_button(
                        content_container,
                        icon_name="delete",
                        command=lambda s=section, i=idx: self.delete_forward_video_for_row(s, i),
                        size=(16, 16),
                        use_text_fallback=True
                    )
                    
                    if delete_btn:
                        delete_btn.pack(side="left")
                    
                    # Кнопка добавления нового видео только в последней строке
                    if has_add_button:
                        RoundedButtonImage(
                            col3,
                            text="Добавить участок дороги",
                            command=lambda s=section: self.add_forward_video(s),
                            width=170,
                            height=25,
                            radius=12,
                            bg_color="#5BB5FF",
                            hover_color="#4492F8",
                            text_color="white",
                            font=("Arial", 8, "bold"),
                            border_width=2,
                            border_color="#085492"
                        ).place(
                            relx=0.5,
                            rely=0.65,  # Фиксированная позиция для кнопки добавления
                            anchor="center"
                        )


                # 4 колонка
                col4 = tk.Frame(row_frame, bg="white")
                col4.place(
                    relx=0.5,
                    rely=0,
                    relwidth=0.5,
                    relheight=1
                )

                # Показываем кнопку выбора видео для обратного направления только если есть видео в прямом направлении
                if forward_video is not None:
                    # Получаем видео для обратного направления по индексу строки
                    reverse_video = None
                    if idx < len(section['reverse_videos']):
                        reverse_video = section['reverse_videos'][idx]
                    
                    # Если нет видео для этой строки
                    if reverse_video is None:
                        RoundedButtonImage(
                            col4,
                            text="Выбрать видео",
                            command=lambda s=section, i=idx: self.select_reverse_video_for_row(s, i),
                            width=170,
                            height=35,
                            radius=15,
                            bg_color="#5BB5FF",
                            hover_color="#4492F8",
                            text_color="white",
                            font=("Arial", 9, "bold"),
                            border_width=2,
                            border_color="#085492"
                        ).place(relx=0.5, rely=0.5, anchor="center")
                    
                    # Если видео есть для этой строки
                    else:
                        container = tk.Frame(col4, bg="white")
                        container.pack(expand=True)
                        
                        tk.Label(
                            container,
                            text=reverse_video,
                            font=("Arial", 10),
                            bg="white"
                        ).pack(side="left", padx=(0, 10))
                        
                        delete_btn = self.icon_manager.create_icon_button(
                            container,
                            icon_name="delete",
                            command=lambda s=section, i=idx: self.delete_reverse_video_for_row(s, i),
                            size=(16, 16),
                            use_text_fallback=True
                        )
                        
                        if delete_btn:
                            delete_btn.pack(side="left")

            current_y += block_height

        # линии
        for relx in [0.25, 0.5, 0.75]:

            line = tk.Frame(
                content,
                bg="#085492",
                width=2
            )

            line.place(
                relx=relx,
                rely=0,
                relheight=1
            )
            
        # горизонтальные линии между строками
        current_y = 0

        for road in self.roads:

            section = road["sections"][0]

            rows_count = max(
                1,
                len(section['forward_videos'])
            )

            block_height = rows_count * row_height

            # линия между дорогами
            if current_y > 0:

                line = tk.Frame(
                    content,
                    bg="#085492",
                    height=2
                )

                line.place(
                    relx=0,
                    y=current_y,
                    relwidth=1
                )

            # линии внутри правой части
            for idx in range(1, rows_count):

                y = current_y + idx * row_height

                line = tk.Frame(
                    content,
                    bg="#085492",
                    height=2
                )

                line.place(
                    relx=0.5,
                    y=y,
                    relwidth=0.5
                )

            current_y += block_height

    def delete_reverse_video(self, section, video_index):

        if 0 <= video_index < len(section['reverse_videos']):

            deleted = section['reverse_videos'].pop(video_index)

            if deleted in self.saved_settings:
                del self.saved_settings[deleted]

            if deleted in self.video_bounds:
                del self.video_bounds[deleted]

            self.refresh_table()

    def add_road(self):
        self.roads.append({
            "road_name": tk.StringVar(value=""),
            "road_location": tk.StringVar(value=""),
            "sections": [
                {
                    'forward_videos': [],
                    'reverse_videos': []
                }
            ]
        })
        self.refresh_table()

        
    def select_forward_video_for_row(self, section, row_index):
        """Выбор видео прямого направления для конкретной строки"""
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            filename = os.path.basename(path)
            
            # Сохраняем полный путь
            self.store_video_path(filename, path)
            
            # Расширяем список до нужного индекса
            while len(section['forward_videos']) <= row_index:
                section['forward_videos'].append(None)
            section['forward_videos'][row_index] = filename
            
            # Убеждаемся, что список обратных видео имеет ту же длину
            while len(section['reverse_videos']) <= row_index:
                section['reverse_videos'].append(None)
            
            self.refresh_table()

    def delete_forward_video_for_row(self, section, row_index):
        """Удаление видео прямого направления для конкретной строки"""
        if 0 <= row_index < len(section['forward_videos']):
            deleted = section['forward_videos'][row_index]
            if deleted in self.saved_settings:
                del self.saved_settings[deleted]
            if deleted in self.video_bounds:
                del self.video_bounds[deleted]
            section['forward_videos'][row_index] = None
            
            # Также удаляем соответствующее видео обратного направления
            if row_index < len(section['reverse_videos']):
                reverse_deleted = section['reverse_videos'][row_index]
                if reverse_deleted and reverse_deleted in self.saved_settings:
                    del self.saved_settings[reverse_deleted]
                if reverse_deleted and reverse_deleted in self.video_bounds:
                    del self.video_bounds[reverse_deleted]
                section['reverse_videos'][row_index] = None
            
            # Очищаем хвостовые None из обоих списков
            while section['forward_videos'] and section['forward_videos'][-1] is None:
                section['forward_videos'].pop()
                if section['reverse_videos'] and len(section['reverse_videos']) > len(section['forward_videos']):
                    section['reverse_videos'].pop()
            
            self.refresh_table()

    def add_forward_video(self, section):
        """Добавление нового видео прямого направления в конец списка"""
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            filename = os.path.basename(path)
            section['forward_videos'].append(filename)
            section['reverse_videos'].append(None)
            self.refresh_table()
    
    def select_forward_video(self, section):
        """Выбор первого видео прямого направления"""
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            filename = os.path.basename(path)
            section['forward_videos'].append(filename)
            # Добавляем соответствующее None для обратного направления
            section['reverse_videos'].append(None)
            self.refresh_table()
            
    def delete_forward_video(self, section, video_index):
        """Удаление видео прямого направления"""
        if 0 <= video_index < len(section['forward_videos']):
            # Удаляем видео
            deleted = section['forward_videos'].pop(video_index)
            
            # Удаляем настройки для видео
            if deleted in self.saved_settings:
                del self.saved_settings[deleted]
            if deleted in self.video_bounds:
                del self.video_bounds[deleted]
            
            # Также удаляем соответствующее видео обратного направления
            if video_index < len(section['reverse_videos']):
                reverse_deleted = section['reverse_videos'].pop(video_index)
                if reverse_deleted and reverse_deleted in self.saved_settings:
                    del self.saved_settings[reverse_deleted]
                if reverse_deleted and reverse_deleted in self.video_bounds:
                    del self.video_bounds[reverse_deleted]
            
            # Очищаем список обратных видео от None в конце
            while section['reverse_videos'] and section['reverse_videos'][-1] is None:
                section['reverse_videos'].pop()
            
            self.refresh_table()
    
    def select_reverse_video(self, section):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            filename = os.path.basename(path)
            section['reverse_videos'].append(filename)
            self.refresh_table()
    
    def add_reverse_video(self, section):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            filename = os.path.basename(path)
            section['reverse_videos'].append(filename)
            self.refresh_table()
            
    def select_reverse_video_for_row(self, section, row_index):
        """Выбор видео обратного направления для конкретной строки"""
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            filename = os.path.basename(path)
            # Расширяем список до нужного индекса, если необходимо
            while len(section['reverse_videos']) <= row_index:
                section['reverse_videos'].append(None)
            section['reverse_videos'][row_index] = filename
            self.refresh_table()

    def delete_reverse_video_for_row(self, section, row_index):
        """Удаление видео обратного направления для конкретной строки"""
        if 0 <= row_index < len(section['reverse_videos']):
            deleted = section['reverse_videos'][row_index]
            if deleted in self.saved_settings:
                del self.saved_settings[deleted]
            if deleted in self.video_bounds:
                del self.video_bounds[deleted]
            section['reverse_videos'][row_index] = None
            self.refresh_table()
    
    def refresh_table(self):
        """Обновляет таблицу и скролл"""
        self.create_table()
        # Обновляем scrollregion после пересоздания таблицы
        if hasattr(self, 'table_canvas') and self.table_canvas:
            self.root.update_idletasks()
            self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all"))
        # При изменении таблицы (добавлении/удалении видео) сбрасываем статус анализа
        self.analysis_completed = False
        self.update_buttons_state()
    
    def start_analysis(self):
        """Запускает анализ всех видео"""
        # Сбрасываем предыдущие результаты
        self.analysis_results = {}
        self.analysis_completed = False
        
        # Запускаем анализ
        self.start_video_analysis()
        
    def analysis_finished(self):
        """Вызывается после завершения анализа"""
        self.error_var.set("Анализ завершен")
        self.analysis_completed = True
        
        # Разблокируем кнопку "Начать анализ"
        self.start_analysis_btn.config(state="normal")
        
        # Проверяем наличие видео и разблокируем кнопку отчета
        self.update_buttons_state()
    
    def update_buttons_state(self):
        """Проверяет, все ли загруженные видео проанализированы"""
        videos = []
        for road in self.roads:
            for section in road["sections"]:
                for v in section['forward_videos']:
                    if v:
                        videos.append(v)
                for v in section['reverse_videos']:
                    if v:
                        videos.append(v)
        
        has_videos = len(videos) > 0
        all_analyzed = has_videos and all(v in self.analysis_results for v in videos)
        
        if hasattr(self, 'to_report_btn') and self.to_report_btn:
            try:
                if all_analyzed and self.analysis_completed:
                    self.to_report_btn.config(state="normal")
                else:
                    self.to_report_btn.config(state="disabled")
            except tk.TclError:
                pass
            
            
    def create_reports_from_table(self):
        """Создает отчеты для выбранных дорог (по всем проанализированным видео)"""
        
        if not self.analysis_results:
            self.error_var.set("Сначала выполните анализ видео")
            return
        
        # Собираем выбранные типы отчётов по дорогам
        selected_reports = {}
        for road_name, selections in self.report_selections.items():
            report_types = []
            if selections["ГОСТ"].get():
                report_types.append("gost")
            if selections["ОДМ"].get():
                report_types.append("odm")
            if report_types:
                selected_reports[road_name] = report_types
        
        if not selected_reports:
            self.error_var.set("Не выбраны типы отчетов ни для одной дороги")
            return
        
        # Собираем сегменты ПО ВСЕМ дорогам (по всем проанализированным видео)
        all_road_segments = self.collect_road_segments()
        
        # Определяем директорию для отчетов
        reports_dir = self.get_reports_directory()
        
        outputs = []
        
        for road_name, report_types in selected_reports.items():
            # Проверяем, есть ли данные для этой дороги
            if road_name not in all_road_segments:
                outputs.append(f"{road_name}: нет проанализированных видео")
                continue
            
            road_data = all_road_segments[road_name]
            forward_segments = road_data.get("forward", [])
            reverse_segments = road_data.get("reverse", [])
            
            if not forward_segments and not reverse_segments:
                outputs.append(f"{road_name}: нет данных для отчёта")
                continue
            
            print(f"\n=== Формирование отчета для дороги: {road_name} ===")
            print(f"  Прямое направление: {len(forward_segments)} сегментов")
            print(f"  Обратное направление: {len(reverse_segments)} сегментов")
            
            if "gost" in report_types:
                try:
                    filename = generate_gost_report(
                        forward_segments,
                        reverse_segments,
                        road_name,
                        reports_dir
                    )
                    outputs.append(f"ГОСТ ({road_name}): {os.path.basename(filename)}")
                except Exception as e:
                    outputs.append(f"ГОСТ ({road_name}): Ошибка - {str(e)}")
            
            if "odm" in report_types:
                try:
                    filename = generate_odm_report(
                        forward_segments,
                        reverse_segments,
                        road_name,
                        reports_dir
                    )
                    outputs.append(f"ОДМ ({road_name}): {os.path.basename(filename)}")
                except Exception as e:
                    outputs.append(f"ОДМ ({road_name}): Ошибка - {str(e)}")
        
        if outputs:
            self.error_var.set("\n".join(outputs))
        else:
            self.error_var.set("Не удалось создать отчеты")


    def collect_road_segments(self):
        from km_analyzer import km_to_meters
        
        road_segments = {}
        
        for road in self.roads:
            road_name = road["road_name"].get()
            if not road_name:
                continue
            
            section = road["sections"][0]
            forward_segments = []
            reverse_segments = []
            
            # Прямые видео
            for video in section['forward_videos']:
                if video and video in self.analysis_results:
                    result = self.analysis_results[video]
                    user_start = self.saved_settings.get(video, {}).get("start")
                    user_end = self.saved_settings.get(video, {}).get("end")
                    
                    user_start_m = km_to_meters(user_start) if user_start else None
                    user_end_m = km_to_meters(user_end) if user_end else None
                    
                    for seg_start, seg_end, defects in result.get("segments", []):
                        if user_start_m is not None and user_end_m is not None:
                            lo = min(user_start_m, user_end_m)
                            hi = max(user_start_m, user_end_m)
                            clipped_start = max(seg_start, lo)
                            clipped_end = min(seg_end, hi)
                            if clipped_start < clipped_end:
                                forward_segments.append((clipped_start, clipped_end, defects))
                        else:
                            forward_segments.append((seg_start, seg_end, defects))
            
            # Обратные видео
            for video in section['reverse_videos']:
                if video and video in self.analysis_results:
                    result = self.analysis_results[video]
                    user_start = self.saved_settings.get(video, {}).get("start")
                    user_end = self.saved_settings.get(video, {}).get("end")
                    
                    user_start_m = km_to_meters(user_start) if user_start else None
                    user_end_m = km_to_meters(user_end) if user_end else None
                    
                    for seg_start, seg_end, defects in result.get("segments", []):
                        norm_start = min(seg_start, seg_end)
                        norm_end = max(seg_start, seg_end)
                        
                        if user_start_m is not None and user_end_m is not None:
                            lo = min(user_start_m, user_end_m)
                            hi = max(user_start_m, user_end_m)
                            clipped_start = max(norm_start, lo)
                            clipped_end = min(norm_end, hi)
                            if clipped_start < clipped_end:
                                reverse_segments.append((clipped_start, clipped_end, defects))
                        else:
                            reverse_segments.append((norm_start, norm_end, defects))
            
            forward_segments.sort(key=lambda x: x[0])
            reverse_segments.sort(key=lambda x: x[0])
            
            road_segments[road_name] = {
                "forward": forward_segments,
                "reverse": reverse_segments
            }
            
            print(f"Дорога '{road_name}': forward={len(forward_segments)}, reverse={len(reverse_segments)}")
        
        return road_segments
    
    def collect_road_segments_for_video(self, video_name, video_result, road_name):
        """Собирает сегменты для конкретного видео + реальные сегменты из другого направления"""
        from km_analyzer import km_to_meters
        
        target_direction = None
        target_section = None
        
        for road in self.roads:
            if road["road_name"].get() == road_name:
                section = road["sections"][0]
                if video_name in section['forward_videos']:
                    target_direction = "forward"
                    target_section = section
                    break
                elif video_name in section['reverse_videos']:
                    target_direction = "reverse"
                    target_section = section
                    break
        
        forward_segments = []
        reverse_segments = []
        
        def _clip_and_add(seg_start, seg_end, defects, user_start, user_end, target_list):
            if user_start and user_end:
                user_start_m = km_to_meters(user_start)
                user_end_m = km_to_meters(user_end)
                if user_start_m is None or user_end_m is None:
                    return
                lo = min(user_start_m, user_end_m)
                hi = max(user_start_m, user_end_m)
                clipped_start = max(seg_start, lo)
                clipped_end = min(seg_end, hi)
                if clipped_start < clipped_end:
                    target_list.append((clipped_start, clipped_end, defects))
            else:
                target_list.append((seg_start, seg_end, defects))
        
        if target_direction == "forward":
            user_start = self.saved_settings.get(video_name, {}).get("start")
            user_end = self.saved_settings.get(video_name, {}).get("end")
            
            for seg_start, seg_end, defects in video_result.get("segments", []):
                _clip_and_add(seg_start, seg_end, defects, user_start, user_end, forward_segments)
            
            # Реальные сегменты из обратных видео
            for rev_video in target_section['reverse_videos']:
                if rev_video and rev_video in self.analysis_results:
                    rev_result = self.analysis_results[rev_video]
                    rev_user_start = self.saved_settings.get(rev_video, {}).get("start")
                    rev_user_end = self.saved_settings.get(rev_video, {}).get("end")
                    
                    for seg_start, seg_end, defects in rev_result.get("segments", []):
                        norm_start = min(seg_start, seg_end)
                        norm_end = max(seg_start, seg_end)
                        _clip_and_add(norm_start, norm_end, defects, rev_user_start, rev_user_end, reverse_segments)
        
        elif target_direction == "reverse":
            user_start = self.saved_settings.get(video_name, {}).get("start")
            user_end = self.saved_settings.get(video_name, {}).get("end")
            
            for seg_start, seg_end, defects in video_result.get("segments", []):
                norm_start = min(seg_start, seg_end)
                norm_end = max(seg_start, seg_end)
                _clip_and_add(norm_start, norm_end, defects, user_start, user_end, reverse_segments)
            
            # Реальные сегменты из прямых видео
            for fwd_video in target_section['forward_videos']:
                if fwd_video and fwd_video in self.analysis_results:
                    fwd_result = self.analysis_results[fwd_video]
                    fwd_user_start = self.saved_settings.get(fwd_video, {}).get("start")
                    fwd_user_end = self.saved_settings.get(fwd_video, {}).get("end")
                    
                    for seg_start, seg_end, defects in fwd_result.get("segments", []):
                        _clip_and_add(seg_start, seg_end, defects, fwd_user_start, fwd_user_end, forward_segments)
        
        forward_segments.sort(key=lambda x: x[0])
        reverse_segments.sort(key=lambda x: x[0])
        
        print(f"  Прямое направление: {len(forward_segments)} сегментов")
        print(f"  Обратное направление: {len(reverse_segments)} сегментов")
        
        return {
            "forward": forward_segments,
            "reverse": reverse_segments
        }
    
    # экран для выбора типа отчета
    def show_report_screen(self):
        self.clear()
        self.current_screen = "report"
        
        report_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        report_frame.pack(fill="both", expand=True)
        
        main_container = tk.Frame(report_frame, bg=self.BG_COLOR)
        main_container.pack(fill="both", expand=True, padx=80, pady=(30,10))
        main_container.pack_propagate(False)
        main_container.config(width=600)
        
        # Заголовок
        tk.Label(
            main_container,
            bg=self.BG_COLOR,
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 20))
        
        # Таблица
        self.report_table_frame = tk.Frame(main_container, bg=self.BG_COLOR)
        self.report_table_frame.pack(fill="both", expand=True)
        
        self.create_report_table()
        
        # Нижняя панель с кнопками
        bottom_frame = tk.Frame(report_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", fill="x", pady=10)
        
        # Контейнер для кнопки "Создать отчет" 
        create_btn_container = tk.Frame(bottom_frame, bg=self.BG_COLOR)
        create_btn_container.pack(fill="x", pady=(0, 40))
        
        create_btn = RoundedButtonImage(
            create_btn_container,
            text="Создать отчет",
            command=self.create_report_from_table,
            width=200,
            height=45,
            radius=15,
            bg_color="#5BB5FF",
            hover_color="#4492F8",
            text_color="white",
            font=("Arial", 11, "bold"),
            border_width=2,
            border_color="#085492"
        )
        create_btn.pack(anchor="center")
        
        # Контейнер для кнопок "Настройки" и "Назад" 
        buttons_container = tk.Frame(bottom_frame, bg=self.BG_COLOR)
        buttons_container.pack()
        
        # Кнопка "Настройки"
        settings_btn = RoundedButtonImage(
            buttons_container,
            text="Настройки",
            command=self.open_settings,
            width=150,
            height=45,
            radius=15,
            bg_color="#5BB5FF",
            hover_color="#4492F8",
            text_color="white",
            font=("Arial", 11, "bold"),
            border_width=2,
            border_color="#085492"
        )
        settings_btn.pack(side="left", padx=40)
        
        # Кнопка "Назад"
        back_btn = RoundedButtonImage(
            buttons_container,
            text="Назад",
            command=self.show_second_screen,
            width=150,
            height=45,
            radius=15,
            bg_color="#F1F4F7",
            hover_color="#C6D6EB",
            text_color="#1E1D26",
            font=("Arial", 11, "bold"),
            border_width=2,
            border_color="#085492"
        )
        back_btn.pack(side="left", padx=40)
        
        tk.Label(bottom_frame, bg=self.BG_COLOR, textvariable=self.error_var, fg="red", 
                font=("Arial", 9)).pack(pady=10)
        
        self.add_logo(self.root)

    def create_report_table(self):
        """Создает таблицу для выбора типа отчета по каждой дороге с мастер-чекбоксами"""
        
        # Очищаем предыдущие виджеты
        for w in self.report_table_frame.winfo_children():
            w.destroy()
        
        # Получаем список дорог с непустыми названиями
        roads_list = []
        for road in self.roads:
            road_name = road["road_name"].get()
            if road_name:  # Только дороги с заполненным названием
                roads_list.append(road_name)
        
        if not roads_list:
            tk.Label(
                self.report_table_frame,
                text="Нет добавленных дорог",
                bg=self.BG_COLOR,
                font=("Arial", 12),
                fg="gray"
            ).pack(expand=True)
            return

        # Создаем словарь для хранения выбора по каждой дороге
        self.report_selections = {}
        for road in roads_list:
            self.report_selections[road] = {
                "ГОСТ": tk.BooleanVar(value=True),
                "ОДМ": tk.BooleanVar(value=True)
            }
        
        # Создаем мастер-чекбоксы для управления всеми чекбоксами в столбце
        self.master_gost = tk.BooleanVar(value=True)
        self.master_odm = tk.BooleanVar(value=True)
        
        # Функции для управления мастер-чекбоксами
        def update_all_gost():
            value = self.master_gost.get()
            for road in roads_list:
                self.report_selections[road]["ГОСТ"].set(value)
        
        def update_all_odm():
            value = self.master_odm.get()
            for road in roads_list:
                self.report_selections[road]["ОДМ"].set(value)
        
        def on_gost_change(road):
            # Проверяем, все ли чекбоксы отмечены
            all_checked = all(self.report_selections[r]["ГОСТ"].get() for r in roads_list)
            # Проверяем, все ли чекбоксы сняты
            all_unchecked = all(not self.report_selections[r]["ГОСТ"].get() for r in roads_list)
            
            if all_checked:
                self.master_gost.set(True)
            elif all_unchecked:
                self.master_gost.set(False)
            else:
                pass
        
        def on_odm_change(road):
            all_checked = all(self.report_selections[r]["ОДМ"].get() for r in roads_list)
            all_unchecked = all(not self.report_selections[r]["ОДМ"].get() for r in roads_list)
            
            if all_checked:
                self.master_odm.set(True)
            elif all_unchecked:
                self.master_odm.set(False)
        
        # Привязываем функции к мастер-чекбоксам
        self.master_gost.trace_add('write', lambda *args: update_all_gost())
        self.master_odm.trace_add('write', lambda *args: update_all_odm())
        
        # Создаем canvas для прокрутки
        canvas = tk.Canvas(self.report_table_frame, bg=self.BG_COLOR, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.report_table_frame, orient="vertical", command=canvas.yview)
        
        scrollable_frame = tk.Frame(canvas, bg=self.BG_COLOR)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas_width)
        canvas.configure(yscrollcommand=scrollbar.set)
        

        headers_frame = tk.Frame(scrollable_frame, bg="#085492", height=80)
        headers_frame.pack(fill="x")
        headers_frame.pack_propagate(False)
        
        headers_inner = tk.Frame(headers_frame, bg="#5BB5FF")
        headers_inner.pack(fill="both", expand=True, padx=2, pady=(2,0))
        
        # Колонка "Наименование дороги" 
        col_widths = [0.4, 0.3, 0.3]  # Дорога, ГОСТ, ОДМ
        
        # Первая колонка 
        first_col = tk.Frame(headers_inner, bg="#5BB5FF")
        first_col.place(relx=0, rely=0, relwidth=col_widths[0], relheight=1)
        tk.Label(
            first_col,
            text="Наименование дороги",
            font=("Arial", 11, "bold"),
            fg="white",
            bg="#5BB5FF",
            anchor="center"
        ).pack(expand=True, fill="both")
        
        # Правая часть (тип отчета)
        right_part = tk.Frame(headers_inner, bg="#5BB5FF")
        right_part.place(relx=col_widths[0], rely=0, relwidth=1 - col_widths[0], relheight=1)
        
        # Вертикальная линия между колонками
        vertical_line = tk.Frame(headers_inner, bg="#085492", width=2)
        vertical_line.place(relx=col_widths[0], rely=0, relheight=1)
        vertical_line.lift()
        
        # Верхняя строка шапки (Тип отчета)
        top_header = tk.Frame(right_part, bg="#5BB5FF", height=40)
        top_header.pack(fill="x")
        top_header.pack_propagate(False)
        
        tk.Label(
            top_header,
            text="Тип отчета",
            font=("Arial", 11, "bold"),
            fg="white",
            bg="#5BB5FF",
            anchor="center"
        ).pack(expand=True, fill="both")
        
        # Горизонтальная линия
        middle_line = tk.Frame(right_part, bg="#085492", height=2)
        middle_line.pack(fill="x")
        middle_line.lift()
        
        # Нижняя строка шапки (ГОСТ, ОДМ)
        bottom_header = tk.Frame(right_part, bg="#5BB5FF", height=38)
        bottom_header.pack(fill="x")
        bottom_header.pack_propagate(False)
        
        # Колонка ГОСТ с мастер-чекбоксом
        gost_frame = tk.Frame(bottom_header, bg="#5BB5FF")
        gost_frame.place(relx=0, rely=0, relwidth=col_widths[1] / (1 - col_widths[0]), relheight=1)
        
        gost_label_frame = tk.Frame(gost_frame, bg="#5BB5FF")
        gost_label_frame.pack(expand=True, fill="both")
        
        tk.Label(
            gost_label_frame,
            text="ГОСТ 50597-2017",
            font=("Arial", 11, "bold"),
            fg="white",
            bg="#5BB5FF"
        ).pack(side="left", expand=True)
        
        # Мастер-чекбокс для ГОСТ 
        master_gost_check = tk.Checkbutton(
            gost_label_frame,
            variable=self.master_gost,
            bg="#5BB5FF",  
            cursor="hand2",
            selectcolor="white",
            activebackground="#5BB5FF",  
            highlightthickness=0,  
            bd=0  
        )
        master_gost_check.pack(side="right", padx=(0, 20))
        
        # Колонка ОДМ с мастер-чекбоксом
        odm_frame = tk.Frame(bottom_header, bg="#5BB5FF")
        odm_frame.place(relx=col_widths[1] / (1 - col_widths[0]), rely=0, 
                    relwidth=col_widths[2] / (1 - col_widths[0]), relheight=1)
        
        odm_label_frame = tk.Frame(odm_frame, bg="#5BB5FF")
        odm_label_frame.pack(expand=True, fill="both")
        
        tk.Label(
            odm_label_frame,
            text="ОДМ 218.4.039-2018",
            font=("Arial", 11, "bold"),
            fg="white",
            bg="#5BB5FF"
        ).pack(side="left", expand=True)
        
        # Мастер-чекбокс для ОДМ 
        master_odm_check = tk.Checkbutton(
            odm_label_frame,
            variable=self.master_odm,
            bg="#5BB5FF",
            cursor="hand2",
            selectcolor="white",
            activebackground="#5BB5FF",
            highlightthickness=0,
            bd=0
        )
        master_odm_check.pack(side="right", padx=(0, 20))
        
        # Вертикальная линия между ГОСТ и ОДМ
        sep_line = tk.Frame(bottom_header, bg="#085492", width=2)
        sep_line.place(relx=col_widths[1] / (1 - col_widths[0]), rely=0, relheight=1)
        sep_line.lift()
        
        # Нижняя граница шапки
        header_bottom_border = tk.Frame(scrollable_frame, bg="#085492", height=2)
        header_bottom_border.pack(fill="x")
        

        rows_container = tk.Frame(scrollable_frame, bg="#085492")
        rows_container.pack(fill="both", expand=True)
        
        row_height = 50
        total_rows = len(roads_list)
        total_height = total_rows * row_height
        
        table_body = tk.Frame(rows_container, bg="#085492", height=total_height + 2)
        table_body.pack(fill="x")
        table_body.pack_propagate(False)
        
        content = tk.Frame(table_body, bg="white")
        content.place(x=2, y=2, relwidth=1, width=-4, relheight=1, height=-4)
        
        # Заполняем строки таблицы
        for idx, road_name in enumerate(roads_list):
            y = idx * row_height
            
            # Колонка с названием дороги
            col_road = tk.Frame(content, bg="white")
            col_road.place(relx=0, y=y, relwidth=col_widths[0], height=row_height)
            tk.Label(
                col_road,
                text=road_name,
                font=("Arial", 10),
                bg="white",
                anchor="center",
                wraplength=120
            ).pack(expand=True, fill="both", padx=2)
            
            # Колонка ГОСТ
            col_gost = tk.Frame(content, bg="white")
            col_gost.place(relx=col_widths[0], y=y, relwidth=col_widths[1], height=row_height)
            
            gost_check = tk.Checkbutton(
                col_gost,
                variable=self.report_selections[road_name]["ГОСТ"],
                bg="white",
                cursor="hand2",
                command=lambda r=road_name: on_gost_change(r)
            )
            gost_check.place(relx=0.5, rely=0.5, anchor="center")
            
            # Колонка ОДМ
            col_odm = tk.Frame(content, bg="white")
            col_odm.place(relx=col_widths[0] + col_widths[1], y=y, 
                        relwidth=col_widths[2], height=row_height)
            
            odm_check = tk.Checkbutton(
                col_odm,
                variable=self.report_selections[road_name]["ОДМ"],
                bg="white",
                cursor="hand2",
                command=lambda r=road_name: on_odm_change(r)
            )
            odm_check.place(relx=0.5, rely=0.5, anchor="center")
        
        # Вертикальные линии в теле таблицы
        x_pos = col_widths[0]
        line = tk.Frame(content, bg="#085492", width=2)
        line.place(relx=x_pos, rely=0, relheight=1)
        
        x_pos += col_widths[1]
        line = tk.Frame(content, bg="#085492", width=2)
        line.place(relx=x_pos, rely=0, relheight=1)
        
        # Горизонтальные линии между строками
        for idx in range(1, total_rows):
            y = idx * row_height
            line = tk.Frame(content, bg="#085492", height=2)
            line.place(relx=0, y=y, relwidth=1)
        
        # Размещаем canvas и scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
    def create_report_from_table(self):
        self.create_reports_from_table()
    
    def open_settings(self):
        """Открывает экран настроек границ видео"""
        # Собираем видео по дорогам и строкам
        self.settings_roads = []  # список дорог, каждая содержит rows
        
        for road in self.roads:
            road_name = road["road_name"].get()
            section = road["sections"][0]
            
            # Определяем максимальное количество строк (по прямым видео)
            max_rows = max(1, len(section['forward_videos']))
            
            rows = []
            for idx in range(max_rows):
                row_data = {
                    "forward_video": None,
                    "reverse_video": None,
                    "row_index": idx
                }
                
                # Добавляем прямое видео, если есть
                if idx < len(section['forward_videos']) and section['forward_videos'][idx]:
                    row_data["forward_video"] = section['forward_videos'][idx]
                
                # Добавляем обратное видео, если есть
                if idx < len(section['reverse_videos']) and section['reverse_videos'][idx]:
                    row_data["reverse_video"] = section['reverse_videos'][idx]
                
                # Добавляем строку только если есть хотя бы одно видео
                if row_data["forward_video"] or row_data["reverse_video"]:
                    rows.append(row_data)
            
            if rows:
                self.settings_roads.append({
                    "road_name": road_name,
                    "rows": rows,
                    "section": section
                })
        
        if not self.settings_roads:
            self.error_var.set("Нет видео для настройки")
            return
        
        self.temp_settings = {}
        self.clear()
        self.current_screen = "settings"
        
        # Создаем фрейм для настроек
        self.settings_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        self.settings_frame.pack(fill="both", expand=True)
        
        main_container = tk.Frame(self.settings_frame, bg=self.BG_COLOR)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(
            main_container,
            text="Настройки",
            bg=self.BG_COLOR,
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 20))
        
        # Таблица настроек
        table_container = tk.Frame(main_container, bg=self.BG_COLOR)
        table_container.pack(fill="both", expand=True)
        
        self.create_settings_table(table_container)
        
        # Нижняя панель с кнопками
        bottom_frame = tk.Frame(self.settings_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", fill="x", pady=30)
        
        button_container = tk.Frame(bottom_frame, bg=self.BG_COLOR)
        button_container.pack()
        
        tk.Label(bottom_frame, bg=self.BG_COLOR, textvariable=self.error_var, fg="red", 
                font=("Arial", 9)).pack(pady=5)
        
        cancel_btn = RoundedButtonImage(
            button_container,
            text="Отменить",
            command=self.cancel_settings,
            width=140,
            height=40,
            radius=15,
            bg_color="#F1F4F7", 
            hover_color="#C6D6EB",
            text_color="#1E1D26",
            font=("Arial", 11, "bold"),
            border_width=2,           
            border_color="#085492"
        )
        cancel_btn.pack(side="left", padx=40)
        
        save_btn = RoundedButtonImage(
            button_container,
            text="Сохранить",
            command=self.save_settings,
            width=140,
            height=40,
            radius=15,
            bg_color="#5BB5FF", 
            hover_color="#4492F8",
            text_color="white",
            font=("Arial", 11, "bold"),
            border_width=2,           
            border_color="#085492"
        )
        save_btn.pack(side="left", padx=40)
        
        self.add_logo(self.root)

    def create_settings_table(self, parent):
        # Проверяем, есть ли видео обратного направления в любой строке
        has_reverse = any(row["reverse_video"] for road in self.settings_roads for row in road["rows"])
        
        # Создаем canvas для прокрутки
        canvas = tk.Canvas(parent, bg=self.BG_COLOR, highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        
        scrollable_frame = tk.Frame(canvas, bg=self.BG_COLOR)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas_width)
        canvas.configure(yscrollcommand=scrollbar.set)

        headers_frame = tk.Frame(scrollable_frame, bg="#085492", height=60)
        headers_frame.pack(fill="x")
        headers_frame.pack_propagate(False)

        headers_inner = tk.Frame(headers_frame, bg="#5BB5FF")
        headers_inner.pack(fill="both", expand=True, padx=2, pady=(2,0))

        if has_reverse:
            col_widths = [0.2, 0.15, 0.25, 0.15, 0.25]
        
            # Создаем фрейм для первой колонки
            first_col = tk.Frame(headers_inner, bg="#5BB5FF")
            first_col.place(relx=0, rely=0, relwidth=col_widths[0], relheight=1)
            
            # Добавляем текст по центру (вертикально и горизонтально)
            tk.Label(
                first_col, 
                text="Наименование дороги", 
                font=("Arial", 11, "bold"), 
                fg="white", 
                bg="#5BB5FF", 
                anchor="center"
            ).pack(expand=True, fill="both")
            
            # Создаем фрейм для остальных колонок (правой части)
            right_part = tk.Frame(headers_inner, bg="#5BB5FF")
            right_part.place(relx=0.2, rely=0, relwidth=0.8, relheight=1)
            
            # Вертикальная линия между первой колонкой и правой частью 
            vertical_line = tk.Frame(headers_inner, bg="#085492", width=2)
            vertical_line.place(relx=0.2, rely=0, relheight=1)
            vertical_line.lift()  # Поднимаем линию на передний план
            
            # Верхний ряд для правой части
            top_headers = tk.Frame(right_part, bg="#5BB5FF", height=30)
            top_headers.pack(fill="x")
            top_headers.pack_propagate(False)
            
            forward_width = (col_widths[1] + col_widths[2]) / (1 - col_widths[0])
            col1_top = tk.Frame(top_headers, bg="#5BB5FF")
            col1_top.place(relx=0, rely=0, relwidth=forward_width, relheight=1)
            tk.Label(col1_top, text="Прямое направление", font=("Arial", 11, "bold"), 
                    fg="white", bg="#5BB5FF", anchor="center").pack(expand=True, fill="both")
            
            # Обратное направление 
            reverse_width = (col_widths[3] + col_widths[4]) / (1 - col_widths[0])
            col2_top = tk.Frame(top_headers, bg="#5BB5FF")
            col2_top.place(relx=forward_width, rely=0, relwidth=reverse_width, relheight=1)
            tk.Label(col2_top, text="Обратное направление", font=("Arial", 11, "bold"), 
                    fg="white", bg="#5BB5FF", anchor="center").pack(expand=True, fill="both")
            
            # Вертикальный разделитель между прямым и обратным направлением
            sep = tk.Frame(top_headers, bg="#085492", width=2)
            sep.place(relx=0.5, rely=0, relheight=1)
            sep.lift()
            
            # Горизонтальная линия между рядами (только для правой части)
            middle_line = tk.Frame(right_part, bg="#085492", height=2)
            middle_line.pack(fill="x")
            middle_line.lift()
            
            # Нижний ряд для правой части
            bottom_headers = tk.Frame(right_part, bg="#5BB5FF", height=28)
            bottom_headers.pack(fill="x")
            bottom_headers.pack_propagate(False)
            
            # Название видео (прямое) - ширина = колонка 1 / ширина правой части
            video_forward_width = col_widths[1] / (1 - col_widths[0])
            forward_video = tk.Frame(bottom_headers, bg="#5BB5FF")
            forward_video.place(relx=0, rely=0, relwidth=video_forward_width, relheight=1)
            tk.Label(forward_video, text="Название видео", font=("Arial", 10, "bold"), 
                    fg="white", bg="#5BB5FF", anchor="center").pack(expand=True, fill="both")
            
            # Адрес дороги (прямой) - ширина = колонка 2 / ширина правой части
            address_forward_width = col_widths[2] / (1 - col_widths[0])
            forward_address = tk.Frame(bottom_headers, bg="#5BB5FF")
            forward_address.place(relx=video_forward_width, rely=0, relwidth=address_forward_width, relheight=1)
            tk.Label(forward_address, text="Адрес дороги", font=("Arial", 10, "bold"), 
                    fg="white", bg="#5BB5FF", anchor="center").pack(expand=True, fill="both")
            
            # Название видео (обратное) - ширина = колонка 3 / ширина правой части
            video_reverse_width = col_widths[3] / (1 - col_widths[0])
            reverse_video = tk.Frame(bottom_headers, bg="#5BB5FF")
            reverse_video.place(relx=video_forward_width + address_forward_width, rely=0, 
                            relwidth=video_reverse_width, relheight=1)
            tk.Label(reverse_video, text="Название видео", font=("Arial", 10, "bold"), 
                    fg="white", bg="#5BB5FF", anchor="center").pack(expand=True, fill="both")
            
            # Адрес дороги (обратный) - ширина = колонка 4 / ширина правой части
            address_reverse_width = col_widths[4] / (1 - col_widths[0])
            reverse_address = tk.Frame(bottom_headers, bg="#5BB5FF")
            reverse_address.place(relx=video_forward_width + address_forward_width + video_reverse_width, rely=0, 
                                relwidth=address_reverse_width, relheight=1)
            tk.Label(reverse_address, text="Адрес дороги", font=("Arial", 10, "bold"), 
                    fg="white", bg="#5BB5FF", anchor="center").pack(expand=True, fill="both")
            
            pos1 = video_forward_width
            pos2 = video_forward_width + address_forward_width
            pos3 = video_forward_width + address_forward_width + video_reverse_width
            
            sep1 = tk.Frame(bottom_headers, bg="#085492", width=2)
            sep1.place(relx=pos1, rely=0, relheight=1)
            sep1.lift()
            
            sep2 = tk.Frame(bottom_headers, bg="#085492", width=2)
            sep2.place(relx=pos2, rely=0, relheight=1)
            sep2.lift()
            
            sep3 = tk.Frame(bottom_headers, bg="#085492", width=2)
            sep3.place(relx=pos3, rely=0, relheight=1)
            sep3.lift()
                
        else:
            # 3 колонки
            col_widths = [0.25, 0.3, 0.45]
            
            first_col = tk.Frame(headers_inner, bg="#5BB5FF")
            first_col.place(relx=0, rely=0, relwidth=col_widths[0], relheight=1)
            
            tk.Label(
                first_col, 
                text="Наименование дороги", 
                font=("Arial", 11, "bold"), 
                fg="white", 
                bg="#5BB5FF", 
                anchor="center"
            ).pack(expand=True, fill="both")
            
            right_part = tk.Frame(headers_inner, bg="#5BB5FF")
            right_part.place(relx=col_widths[0], rely=0, relwidth=1 - col_widths[0], relheight=1)
            
            vertical_line = tk.Frame(headers_inner, bg="#085492", width=2)
            vertical_line.place(relx=col_widths[0], rely=0, relheight=1)
            vertical_line.lift()
            
            
            top_headers = tk.Frame(right_part, bg="#5BB5FF", height=30)
            top_headers.pack(fill="x")
            top_headers.pack_propagate(False)
            
            col1_top = tk.Frame(top_headers, bg="#5BB5FF")
            col1_top.place(relx=0, rely=0, relwidth=1, relheight=1)
            tk.Label(col1_top, text="Прямое направление", font=("Arial", 11, "bold"), 
                    fg="white", bg="#5BB5FF", anchor="center").pack(expand=True, fill="both")
            
            middle_line = tk.Frame(right_part, bg="#085492", height=2)
            middle_line.pack(fill="x")
            middle_line.lift()
            
            bottom_headers = tk.Frame(right_part, bg="#5BB5FF", height=28)
            bottom_headers.pack(fill="x")
            bottom_headers.pack_propagate(False)
            
            video_width = col_widths[1] / (1 - col_widths[0])
            video_col = tk.Frame(bottom_headers, bg="#5BB5FF")
            video_col.place(relx=0, rely=0, relwidth=video_width, relheight=1)
            tk.Label(video_col, text="Название видео", font=("Arial", 10, "bold"), 
                    fg="white", bg="#5BB5FF", anchor="center").pack(expand=True, fill="both")
            
            address_width = col_widths[2] / (1 - col_widths[0])
            address_col = tk.Frame(bottom_headers, bg="#5BB5FF")
            address_col.place(relx=video_width, rely=0, relwidth=address_width, relheight=1)
            tk.Label(address_col, text="Адрес дороги", font=("Arial", 10, "bold"), 
                    fg="white", bg="#5BB5FF", anchor="center").pack(expand=True, fill="both")
            
            sep = tk.Frame(bottom_headers, bg="#085492", width=2)
            sep.place(relx=video_width, rely=0, relheight=1)
            sep.lift()

        # Нижняя граница шапки
        header_bottom_border = tk.Frame(scrollable_frame, bg="#085492", height=2)
        header_bottom_border.pack(fill="x")
        

        rows_container = tk.Frame(scrollable_frame, bg="#085492")
        rows_container.pack(fill="both", expand=True)

        # Вычисляем общую высоту
        row_height = 60
        total_rows = sum(len(road["rows"]) for road in self.settings_roads)
        total_height = total_rows * row_height

        table_body = tk.Frame(rows_container, bg="#085492", height=total_height + 2)
        table_body.pack(fill="x")
        table_body.pack_propagate(False)

        content = tk.Frame(table_body, bg="white")
        content.place(x=2, y=2, relwidth=1, width=-4, relheight=1, height=-4)

        current_y = 0

        for road_data in self.settings_roads:
            rows_count = len(road_data["rows"])
            block_height = rows_count * row_height
            
            # Колонка с наименованием дороги (объединенная)
            if has_reverse:
                col_road = tk.Frame(content, bg="white")
                col_road.place(relx=0, y=current_y, relwidth=col_widths[0], height=block_height)
            else:
                col_road = tk.Frame(content, bg="white")
                col_road.place(relx=0, y=current_y, relwidth=col_widths[0], height=block_height)
            
            tk.Label(col_road, text=road_data["road_name"], font=("Arial", 10, "bold"), 
                    bg="white", anchor="center", wraplength=150).pack(expand=True, fill="both", padx=5)
            
            # Строки для видео
            for idx, row_data in enumerate(road_data["rows"]):
                y = current_y + idx * row_height
                
                if has_reverse:
                    # Колонка 1: Название видео (прямое) - ширина col_widths[1]
                    col_forward_video = tk.Frame(content, bg="white")
                    col_forward_video.place(relx=col_widths[0], y=y, 
                                        relwidth=col_widths[1], height=row_height)
                    
                    if row_data["forward_video"]:
                        tk.Label(col_forward_video, text=row_data["forward_video"], font=("Arial", 9), 
                                bg="white", anchor="center", wraplength=100).pack(expand=True, fill="both", padx=5)
                    else:
                        tk.Label(col_forward_video, text="—", font=("Arial", 9), 
                                bg="white", anchor="center", fg="gray").pack(expand=True, fill="both")
                    
                    # Колонка 2: Адрес для прямого видео - ширина col_widths[2]
                    col_forward_address = tk.Frame(content, bg="white")
                    col_forward_address.place(relx=col_widths[0] + col_widths[1], y=y,
                                            relwidth=col_widths[2], height=row_height)
                    
                    if row_data["forward_video"]:
                        self.create_address_widgets(col_forward_address, row_data["forward_video"])
                    else:
                        tk.Label(col_forward_address, text="—", font=("Arial", 9), 
                                bg="white", anchor="center", fg="gray").pack(expand=True, fill="both")
                    
                    # Колонка 3: Название видео (обратное) - ширина col_widths[3]
                    col_reverse_video = tk.Frame(content, bg="white")
                    col_reverse_video.place(relx=col_widths[0] + col_widths[1] + col_widths[2], y=y,
                                        relwidth=col_widths[3], height=row_height)
                    
                    if row_data["reverse_video"]:
                        tk.Label(col_reverse_video, text=row_data["reverse_video"], font=("Arial", 9), 
                                bg="white", anchor="center", wraplength=100).pack(expand=True, fill="both", padx=5)
                    else:
                        tk.Label(col_reverse_video, text="—", font=("Arial", 9), 
                                bg="white", anchor="center", fg="gray").pack(expand=True, fill="both")
                    
                    # Колонка 4: Адрес для обратного видео - ширина col_widths[4]
                    col_reverse_address = tk.Frame(content, bg="white")
                    col_reverse_address.place(relx=col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3], y=y,
                                            relwidth=col_widths[4], height=row_height)
                    
                    if row_data["reverse_video"]:
                        self.create_address_widgets(col_reverse_address, row_data["reverse_video"])
                    else:
                        tk.Label(col_reverse_address, text="—", font=("Arial", 9), 
                                bg="white", anchor="center", fg="gray").pack(expand=True, fill="both")
                    
                else:
                    # 3 колонки
                    # Колонка 1: Название видео - ширина col_widths[1]
                    col_video = tk.Frame(content, bg="white")
                    col_video.place(relx=col_widths[0], y=y, 
                                relwidth=col_widths[1], height=row_height)
                    
                    if row_data["forward_video"]:
                        tk.Label(col_video, text=row_data["forward_video"], font=("Arial", 9), 
                                bg="white", anchor="center", wraplength=150).pack(expand=True, fill="both", padx=5)
                    else:
                        tk.Label(col_video, text="—", font=("Arial", 9), 
                                bg="white", anchor="center", fg="gray").pack(expand=True, fill="both")
                    
                    # Колонка 2: Адрес - ширина col_widths[2]
                    col_address = tk.Frame(content, bg="white")
                    col_address.place(relx=col_widths[0] + col_widths[1], y=y,
                                    relwidth=col_widths[2], height=row_height)
                    
                    if row_data["forward_video"]:
                        self.create_address_widgets(col_address, row_data["forward_video"])
                    else:
                        tk.Label(col_address, text="—", font=("Arial", 9), 
                                bg="white", anchor="center", fg="gray").pack(expand=True, fill="both")
            
            current_y += block_height

        # Вертикальные линии в теле таблицы (динамические)
        x_pos = 0
        for i in range(len(col_widths) - 1):
            x_pos += col_widths[i]
            line = tk.Frame(content, bg="#085492", width=2)
            line.place(relx=x_pos, rely=0, relheight=1)

        # Горизонтальные линии между строками
        current_y = 0
        for road_data in self.settings_roads:
            rows_count = len(road_data["rows"])
            block_height = rows_count * row_height
            
            if current_y > 0:
                line = tk.Frame(content, bg="#085492", height=2)
                line.place(relx=0, y=current_y, relwidth=1)
            
            for idx in range(1, rows_count):
                y = current_y + idx * row_height
                line = tk.Frame(content, bg="#085492", height=2)
                line.place(relx=col_widths[0], y=y, relwidth=1 - col_widths[0])
            
            current_y += block_height
        
        # Размещаем canvas и scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)

    def create_address_widgets(self, parent, video):
        direction = self.get_video_direction(video)
        
        # Приоритет: saved_settings → analysis_results → пустые поля
        if video in self.saved_settings:
            current = self.saved_settings[video]
        elif video in self.analysis_results:
            result = self.analysis_results[video]
            current = {"start": result["start"], "end": result["end"]}
        else:
            # Ничего не распознано — пустые поля
            current = {"start": "", "end": ""}
        
        sv = tk.StringVar(value=current["start"])
        ev = tk.StringVar(value=current["end"])

        bounds = self.video_bounds.get(video)
        if bounds:
            rs = bounds["start"]
            re = bounds["end"]
        else:
            rs = 0
            re = 0
        
        # Контейнер для элементов адреса с центрированием
        address_frame = tk.Frame(parent, bg="white")
        address_frame.pack(expand=True, fill="both")
        
        # Внутренний фрейм для центрирования содержимого
        inner_frame = tk.Frame(address_frame, bg="white")
        inner_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(inner_frame, text="Начало:", font=("Arial", 9), bg="white").grid(row=0, column=0, padx=2)
        
        start_entry = tk.Entry(inner_frame, textvariable=sv, width=7, font=("Arial", 8),
                            relief="solid", bd=1, justify="center")
        start_entry.grid(row=0, column=1, padx=2)
        
        # Кнопки для начала
        start_buttons = tk.Frame(inner_frame, bg="white")
        start_buttons.grid(row=0, column=2, padx=1)
        tk.Button(start_buttons, text="▲", 
                command=lambda v=sv, o=ev, rs=rs, re=re: self.change_km(v, o, 100, rs, re, True, direction),
                width=2, height=1, relief="flat", bg="#e0e0e0", font=("Arial", 7)).pack(side="top")
        tk.Button(start_buttons, text="▼", 
                command=lambda v=sv, o=ev, rs=rs, re=re: self.change_km(v, o, -100, rs, re, True, direction),
                width=2, height=1, relief="flat", bg="#e0e0e0", font=("Arial", 7)).pack(side="bottom")
        
        # Разделитель
        tk.Label(inner_frame, text="→", font=("Arial", 10), bg="white", fg="#666").grid(row=0, column=3, padx=5)
        
        # Конец
        tk.Label(inner_frame, text="Конец:", font=("Arial", 9), bg="white").grid(row=0, column=4, padx=2)
        
        end_entry = tk.Entry(inner_frame, textvariable=ev, width=7, font=("Arial", 8),
                            relief="solid", bd=1, justify="center")
        end_entry.grid(row=0, column=5, padx=2)
        
        # Кнопки для конца
        end_buttons = tk.Frame(inner_frame, bg="white")
        end_buttons.grid(row=0, column=6, padx=1)
        tk.Button(end_buttons, text="▲", 
                command=lambda v=ev, o=sv, rs=rs, re=re: self.change_km(v, o, 100, rs, re, False, direction),
                width=2, height=1, relief="flat", bg="#e0e0e0", font=("Arial", 7)).pack(side="top")
        tk.Button(end_buttons, text="▼", 
                command=lambda v=ev, o=sv, rs=rs, re=re: self.change_km(v, o, -100, rs, re, False, direction),
                width=2, height=1, relief="flat", bg="#e0e0e0", font=("Arial", 7)).pack(side="bottom")
        
        # Сохраняем с учетом направления
        self.temp_settings[video] = (sv, ev, rs, re, direction)
            

    
    def change_km(self, var, other, delta, rs, re, is_start, direction=None):
        try:
            if not var or not other:
                return
            
            # Если direction не передан, определяем по границам
            if direction is None:
                direction = "reverse" if rs > re else "forward"
            
            cur = self.km_to_meters(var.get())
            oth = self.km_to_meters(other.get())
            new = cur + delta
            
            if direction == "reverse":
                # Для обратного направления
                max_val = max(rs, re)
                min_val = min(rs, re)
                
                if new < min_val or new > max_val:
                    self.error_var.set(f"Выход за границы видео (допустимо: {self.meters_to_km(min_val)} - {self.meters_to_km(max_val)})")
                    return
                
                if is_start:
                    if new <= oth:
                        self.error_var.set(f"Начало должно быть больше конца")
                        return
                else:
                    if new >= oth:
                        self.error_var.set(f"Конец должен быть меньше начала")
                        return
            else:
                # Для прямого направления
                if new < rs or new > re:
                    self.error_var.set(f"Выход за границы видео (допустимо: {self.meters_to_km(rs)} - {self.meters_to_km(re)})")
                    return
                
                if is_start and new >= oth:
                    self.error_var.set(f"Начало должно быть меньше конца")
                    return
                
                if not is_start and new <= oth:
                    self.error_var.set(f"Конец должен быть больше начала")
                    return
            
            self.error_var.set("")
            var.set(self.meters_to_km(new))
        except (tk.TclError, RuntimeError, AttributeError):
            pass
        
    def change_km_reverse(self, var, other, delta, rs, re, is_start):
        """Изменение километров для обратного направления (start > end)"""
        try:
            if not var or not other:
                return
            
            cur = self.km_to_meters(var.get())
            oth = self.km_to_meters(other.get())
            new = cur + delta
            
            # Для обратного направления: start от 3000 до 0, end от 3000 до 0
            # Границы: max_val = rs (3000), min_val = re (0)
            max_val = max(rs, re)
            min_val = min(rs, re)
            
            if new < min_val or new > max_val:
                self.error_var.set(f"Выход за границы видео (допустимо: {self.meters_to_km(min_val)} - {self.meters_to_km(max_val)})")
                return
            
            if is_start:
                # Начало должно быть больше конца
                if new <= oth:
                    self.error_var.set(f"Начало ({self.meters_to_km(new)}) должно быть больше конца ({self.meters_to_km(oth)}) для обратного направления")
                    return
            else:
                # Конец должен быть меньше начала
                if new >= oth:
                    self.error_var.set(f"Конец ({self.meters_to_km(new)}) должен быть меньше начала ({self.meters_to_km(oth)}) для обратного направления")
                    return
            
            self.error_var.set("")
            var.set(self.meters_to_km(new))
        except (tk.TclError, RuntimeError, AttributeError):
            pass
    
    def cancel_settings(self):
        """Отмена настроек - возврат на экран отчета"""
        self.temp_settings = {}
        self.show_report_screen()
    
    def save_settings(self):
        """Сохраняет настройки границ"""
        if not self.temp_settings:
            self.error_var.set("Нет настроек для сохранения")
            return
        
        for video, (s, e, rs, re, direction) in self.temp_settings.items():
            try:

                s_val = s.get().strip()
                e_val = e.get().strip()
                
                # Если поля пустые — не сохраняем (используем распознанные)
                if not s_val or not e_val:
                    print(f"Пропуск {video}: границы не заданы")
                    continue
                
                start = self.km_to_meters(s_val)
                end = self.km_to_meters(e_val)
                
                print(f"Сохранение: video={video}, direction={direction}")
                print(f"  start={start}м ({s_val}), end={end}м ({e_val})")
                
                if direction == "reverse":
                    max_val = max(rs, re)  
                    min_val = min(rs, re)  
                    
                    # Проверка что начало в пределах [min_val, max_val]
                    if start < min_val or start > max_val:
                        self.error_var.set(f"Начало {s.get()} вне допустимых границ ({self.meters_to_km(min_val)} - {self.meters_to_km(max_val)}) для {video}")
                        return
                    
                    # Проверка что конец в пределах [min_val, max_val]
                    if end < min_val or end > max_val:
                        self.error_var.set(f"Конец {e.get()} вне допустимых границ ({self.meters_to_km(min_val)} - {self.meters_to_km(max_val)}) для {video}")
                        return
                    
                    # Для обратного направления начало должно быть больше конца
                    if start <= end:
                        self.error_var.set(f"Для обратного направления начало ({s.get()}) должно быть больше конца ({e.get()})")
                        return
                        
                else:
                    if start < rs or start > re:
                        self.error_var.set(f"Начало {s.get()} вне допустимых границ ({self.meters_to_km(rs)} - {self.meters_to_km(re)}) для {video}")
                        return
                    if end > re or end < rs:
                        self.error_var.set(f"Конец {e.get()} вне допустимых границ ({self.meters_to_km(rs)} - {self.meters_to_km(re)}) для {video}")
                        return
                    if start >= end:
                        self.error_var.set(f"Начало должно быть меньше конца для {video}")
                        return
                        
            except tk.TclError as e:
                self.error_var.set(f"Ошибка доступа к данным видео {video}: {e}")
                return
            except Exception as e:
                self.error_var.set(f"Ошибка при проверке настроек: {e}")
                return
        
        # Сохраняем настройки
        saved_count = 0
        for video, (s, e, *_) in self.temp_settings.items():
            try:
                s_val = s.get().strip()
                e_val = e.get().strip()
                if not s_val or not e_val:
                    continue
                self.saved_settings[video] = {"start": s_val, "end": e_val}
                print(f"Сохранено: {video} -> {s_val} - {e_val}")
                saved_count += 1
            except tk.TclError:
                pass
        
        self.temp_settings = {}
        self.error_var.set(f"Настройки сохранены ({saved_count} видео)")
        self.show_report_screen()
    
    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()
            
        self.error_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()