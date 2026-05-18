import tkinter as tk
from tkinter import filedialog, ttk
import os
import threading
from km_analyzer import analyze_video
from ui_components import (
    RoundedButtonImage, 
    ImageIconButton, 
    TextIconButton,
    IconManager,
    Spinner
)

class App:
    def __init__(self, root=None, build_ui=True):
        self.root = root or tk.Tk()

        self.root.title("Приложение")
        self.root.geometry("1300x600")
        self.BG_COLOR = "#FEFEFF"
        self.root.configure(bg=self.BG_COLOR)

        self.icon_manager = IconManager()

        # state
        self.video_path = None
        self.road_files = []
        self.reverse_video_path = None
        self.reverse_road_files = []

        self.saved_settings = {}
        self.analysis_status = {}
        self.analysis_error = {}

        self.error_var = tk.StringVar(master=self.root)

        self.temp_settings = {}
        self.video_bounds = {}
        self.settings_window = None
        self.settings_frame = None

        if hasattr(self, "init_state"):
            self.init_state()

        if build_ui:
            self.show_main_screen()

    # UTILS
    def km_to_meters(self, value):
        try:
            km, m = map(int, value.split("+"))
            return km * 1000 + m
        except:
            return 0

    def meters_to_km(self, value):
        return f"{value // 1000}+{value % 1000:03d}"
    
    
    def create_report(self):
        from km_analyzer import run_ai_analysis
        from report_generator import generate_excel, generate_odm_excel
        import threading

        if any(self.analysis_status.values()):
            self.error_var.set("Дождитесь окончания анализа")
            return

        if any(self.analysis_error.values()):
            self.error_var.set("Есть ошибки анализа")
            return

        if not self.report_gost_var.get() and not self.report_odm_var.get():
            self.error_var.set("Выберите хотя бы один тип отчета")
            return

        self.error_var.set("Генерация отчета...")

        def process():
            forward_segments = []
            reverse_segments = []
            
            # Прямое направление
            if self.video_path:
                forward_files = [self.video_path] + self.road_files
                
                for f in forward_files:
                    if f in self.saved_settings:
                        start_str = self.saved_settings[f]["start"]
                        end_str = self.saved_settings[f]["end"]
                        
                        if start_str and end_str:
                            # run_ai_analysis возвращает список кортежей (start, end, defects)
                            # где defects - список дефектов на этом сегменте
                            segments_data = run_ai_analysis(f, start_str, end_str)
                            
                            for seg_start, seg_end, defects in segments_data:
                                forward_segments.append((seg_start, seg_end, defects))
            
            # Обратное направление
            if self.reverse_video_path or self.reverse_road_files:
                reverse_files = []
                if self.reverse_video_path:
                    reverse_files.append(self.reverse_video_path)
                reverse_files.extend(self.reverse_road_files)
                
                for f in reverse_files:
                    if f in self.saved_settings:
                        start_str = self.saved_settings[f]["start"]
                        end_str = self.saved_settings[f]["end"]
                        
                        if start_str and end_str:
                            # run_ai_analysis возвращает список кортежей (start, end, defects)
                            segments_data = run_ai_analysis(f, start_str, end_str)
                            
                            for seg_start, seg_end, defects in segments_data:
                                reverse_segments.append((seg_start, seg_end, defects))

            if not forward_segments and not reverse_segments:
                self.root.after(0, lambda: self.error_var.set("Нет данных для отчета"))
                return

            # Сортируем сегменты по начальной координате
            forward_segments.sort(key=lambda x: x[0])
            reverse_segments.sort(key=lambda x: x[0])

            outputs = []

            # ГОСТ
            if self.report_gost_var.get():
                filename = generate_excel(forward_segments, reverse_segments if reverse_segments else None)
                outputs.append(f"ГОСТ: {filename}")

            # ОДМ
            if self.report_odm_var.get():
                filename = generate_odm_excel(forward_segments, reverse_segments if reverse_segments else None)
                outputs.append(f"ОДМ: {filename}")

            self.root.after(
                0,
                lambda: self.error_var.set(" | ".join(outputs))
            )

        threading.Thread(target=process, daemon=True).start()

    # 1 экран
    def show_main_screen(self):
        self.clear()
        
        btn = RoundedButtonImage(
            self.root, 
            text="Выбрать видео", 
            command=self.select_video,
            width=200, 
            height=60, 
            radius=15,
            bg_color="#5BB5FF", 
            hover_color="#4492F8",
            text_color="white",
            font=("Arial", 12, "bold"),
            border_width=2,           
            border_color="#085492"    
        )
        btn.place(relx=0.5, rely=0.5, anchor="center")

    def select_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            self.video_path = path
            self.analysis_status[path] = True
            self.analysis_error[path] = False
            self.saved_settings[path] = {"start": "", "end": ""}
            self.show_second_screen()
            threading.Thread(target=self.analyze_and_update,
                             args=(path, "forward"), daemon=True).start()

    # 2 экран
    def show_second_screen(self):
        self.clear()
        
        # Основной контейнер
        main_vertical = tk.Frame(self.root, bg=self.BG_COLOR)
        main_vertical.pack(fill="both", expand=True)
        
        # Контейнер для колонок
        columns_container = tk.Frame(main_vertical, bg=self.BG_COLOR)
        columns_container.pack(fill="both", expand=True, padx=20, pady=(30, 5)) 
        
        # Две колонки
        left_column = tk.Frame(columns_container, bg=self.BG_COLOR)
        left_column.pack(side="left", fill="both", expand=True, padx=4)
        
        right_column = tk.Frame(columns_container, bg=self.BG_COLOR)
        right_column.pack(side="right", fill="both", expand=True, padx=4)
        
        # Заголовки колонок
        tk.Label(left_column, bg=self.BG_COLOR, text="Прямое направление", font=("Arial", 14, "bold")).pack(pady=5)
        tk.Label(right_column, bg=self.BG_COLOR, text="Обратное направление", font=("Arial", 14, "bold")).pack(pady=5)
        
        # Левая колонка - прямое направление
        self.forward_frame = tk.Frame(left_column, bg=self.BG_COLOR)
        self.forward_frame.pack(fill="both", expand=True)
        self.update_forward_column()
        
        # Правая колонка - обратное направление
        self.reverse_frame = tk.Frame(right_column, bg=self.BG_COLOR)
        self.reverse_frame.pack(fill="both", expand=True)
        self.update_reverse_column()
        
        # Тип отчета внизу
        report_frame = tk.Frame(main_vertical, bg=self.BG_COLOR)
        report_frame.pack(pady=(0, 5)) 
        
        tk.Label(report_frame, text="Тип отчета:", bg=self.BG_COLOR , font=("Arial", 14, "bold") ).pack(pady=(0, 10))
        
        self.report_gost_var = tk.BooleanVar(value=True)
        self.report_odm_var = tk.BooleanVar(value=True)
        
        tk.Checkbutton(report_frame, text="ГОСТ", bg=self.BG_COLOR , variable=self.report_gost_var, font=("Arial", 12)).pack(side="left", padx=20)
        tk.Checkbutton(report_frame, text="ОДМ", bg=self.BG_COLOR, variable=self.report_odm_var, font=("Arial", 12)).pack(side="right", padx=20)
        
        # Ошибки
        tk.Label(self.root, textvariable=self.error_var, bg=self.BG_COLOR, fg="red").pack(pady=(0, 12))
        
        # Кнопки внизу
        bottom = tk.Frame(main_vertical, bg=self.BG_COLOR)
        bottom.pack(side="bottom", pady=30)

        
        self.settings_btn = RoundedButtonImage(
            bottom, 
            text="Настройки", 
            command=self.open_settings,
            width=150, 
            height=40, 
            radius=15,
            bg_color="#F1F4F7", 
            hover_color="#C6D6EB",
            text_color="#1E1D26",
            font=("Arial", 11, "bold"),
            border_width=2,           
            border_color="#085492"    
        )
        self.settings_btn.pack(side="left", padx=30)
        
        spacer = tk.Frame(bottom, width=100, bg=self.BG_COLOR)  
        spacer.pack(side="left", fill="y")
        
        self.report_btn = RoundedButtonImage(
            bottom,
            text="Создать отчет",
            command=self.create_report,
            width=150,
            height=40,
            radius=15,
            bg_color="#5BB5FF", 
            hover_color="#4492F8",
            text_color="white",
            font=("Arial", 11, "bold"),
            border_width=2,           
            border_color="#085492" 
        )
        self.report_btn.pack(side="right", padx=30)
        
        self.update_buttons_state()
    
    def update_forward_column(self):
        # Очищаем фрейм
        try:
            for w in self.forward_frame.winfo_children():
                w.destroy()
        except tk.TclError:
            # Виджет уже уничтожен, выходим
            return
            
        if not self.video_path:
            # Если видео не выбрано
            btn = RoundedButtonImage(
                self.forward_frame,
                text="Выбрать видео",
                command=self.select_forward_video,
                width=150,
                height=40,
                radius=15,
                bg_color="#5BB5FF", 
                hover_color="#4492F8",
                text_color="white",
                font=("Arial", 11, "bold"),
                border_width=2,           
                border_color="#085492" 
            )
            btn.pack(pady=20, anchor="center")

            return
        
        # Основное видео
        video_container = tk.Frame(self.forward_frame, bg=self.BG_COLOR)
        video_container.pack(fill="x", pady=10, padx=20)
        
        video_inner = tk.Frame(video_container, bg=self.BG_COLOR)
        video_inner.pack(anchor="center")
        
        # Название файла
        video_label = tk.Label(
            video_inner, 
            text=os.path.basename(self.video_path),
            font=("Arial", 11),
            anchor="w", 
            bg=self.BG_COLOR
        )
        video_label.pack(side="left", padx=5)
        
        delete_btn = self.icon_manager.create_icon_button(
            video_inner,
            "delete",
            self.remove_forward_video,
            size=(24, 24)
        )
        if delete_btn:
            delete_btn.pack(side="left", padx=5)
        
        # Крутилка для основного видео
        if self.analysis_status.get(self.video_path):
            spinner = Spinner(video_inner, size=25, color="#3b82f6", bg=self.BG_COLOR)
            spinner.pack(side="left", padx=5)
            spinner.start()
            setattr(self, "forward_main_spinner", spinner)
        
        # Дополнительные участки
        tk.Label(self.forward_frame, bg=self.BG_COLOR, text="Дополнительные участки дороги:", 
                font=("Arial", 12, "bold")).pack(pady=(10, 0))
        
        files_frame = tk.Frame(self.forward_frame, bg=self.BG_COLOR)
        files_frame.pack()
        
        for f in self.road_files:
            row = tk.Frame(files_frame, bg=self.BG_COLOR)
            row.pack(fill="x", pady=2)
            
            text = os.path.basename(f)
            if self.analysis_status.get(f):
                text += " (анализ...)"
            elif self.analysis_error.get(f):
                text += " (ошибка анализа)"
            else:
                s = self.saved_settings[f]["start"]
                e = self.saved_settings[f]["end"]
                text += f" | {s} - {e}"
            
            lbl = tk.Label(row, text=text, bg=self.BG_COLOR, fg="red" if self.analysis_error.get(f) else "black")
            lbl.pack(side="left")
            
            btn = tk.Button(row, text="Удалить", bg=self.BG_COLOR,
                          command=lambda file=f: self.remove_forward_file(file))
            btn.pack(side="right")
            
            # крутилка
            if self.analysis_status.get(f):
                spinner = Spinner(row, size=25, color="#3b82f6", bg=self.BG_COLOR)
                spinner.pack(side="right", padx=5)
                spinner.start()

        add_btn = RoundedButtonImage(
            self.forward_frame,  
            text="Добавить участок дороги",
            command=self.add_forward_file,  
            width=250,
            height=40,
            radius=15,
            bg_color="#5BB5FF", 
            hover_color="#4492F8",
            text_color="white",
            font=("Arial", 11, "bold"),
            border_width=2,           
            border_color="#085492"
        )
        add_btn.pack(pady=5, anchor="center")
    
    def update_reverse_column(self):
        # Очищаем фрейм
        try:
            for w in self.reverse_frame.winfo_children():
                w.destroy()
        except tk.TclError:
            return
        
        if not self.reverse_video_path:
            # Если видео не выбрано
            btn = RoundedButtonImage(
                self.reverse_frame,
                text="Выбрать видео",
                command=self.select_reverse_video,
                width=150,
                height=40,
                radius=15,
                bg_color="#5BB5FF", 
                hover_color="#4492F8",
                text_color="white",
                font=("Arial", 11, "bold"),
                border_width=2,           
                border_color="#085492" 
            )
            btn.pack(pady=20, anchor="center")
            return
        
        # Основное видео
        video_container = tk.Frame(self.reverse_frame, bg=self.BG_COLOR)
        video_container.pack(fill="x", pady=10, padx=20)
        
        video_inner = tk.Frame(video_container, bg=self.BG_COLOR)
        video_inner.pack(anchor="center")
        
        # Название файла
        video_label = tk.Label(
            video_inner, 
            text=os.path.basename(self.reverse_video_path),
            font=("Arial", 11),
            anchor="w", 
            bg=self.BG_COLOR
        )
        video_label.pack(side="left", padx=5)
        
        # Кнопка удаления (иконка, как в левой колонке)
        delete_btn = self.icon_manager.create_icon_button(
            video_inner,
            "delete",
            self.remove_reverse_video,
            size=(24, 24)
        )
        if delete_btn:
            delete_btn.pack(side="left", padx=5)
        
        # Крутилка для основного видео
        if self.analysis_status.get(self.reverse_video_path):
            spinner = Spinner(video_inner, size=25, color="#3b82f6", bg=self.BG_COLOR)
            spinner.pack(side="left", padx=5)
            spinner.start()
            setattr(self, "reverse_main_spinner", spinner)
        
        # Дополнительные участки
        tk.Label(self.reverse_frame, bg=self.BG_COLOR, text="Дополнительные участки дороги:", 
                font=("Arial", 12, "bold")).pack(pady=(10, 0))
        
        files_frame = tk.Frame(self.reverse_frame, bg=self.BG_COLOR)
        files_frame.pack()
        
        for f in self.reverse_road_files:
            row = tk.Frame(files_frame, bg=self.BG_COLOR)
            row.pack(fill="x", pady=2)
            
            text = os.path.basename(f)
            if self.analysis_status.get(f):
                text += " (анализ...)"
            elif self.analysis_error.get(f):
                text += " (ошибка анализа)"
            else:
                s = self.saved_settings[f]["start"]
                e = self.saved_settings[f]["end"]
                text += f" | {s} - {e}"
            
            lbl = tk.Label(row, text=text, fg="red" if self.analysis_error.get(f) else "black", bg=self.BG_COLOR)
            lbl.pack(side="left")
            
            delete_file_btn = self.icon_manager.create_icon_button(
                row,
                "delete",
                lambda file=f: self.remove_reverse_file(file),
                size=(20, 20)
            )
            if delete_file_btn:
                delete_file_btn.pack(side="right", padx=5)
            
            # крутилка
            if self.analysis_status.get(f):
                spinner = Spinner(row, size=25, color="#3b82f6", bg=self.BG_COLOR)
                spinner.pack(side="right", padx=5)
                spinner.start()
        
        add_btn = RoundedButtonImage(
            self.reverse_frame,  
            text="Добавить участок дороги",
            command=self.add_reverse_file,  
            width=250,
            height=40,
            radius=15,
            bg_color="#5BB5FF", 
            hover_color="#4492F8",
            text_color="white",
            font=("Arial", 11, "bold"),
            border_width=2,           
            border_color="#085492"
        )
        add_btn.pack(pady=5, anchor="center")
    
    def select_forward_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            self.video_path = path
            self.analysis_status[path] = True
            self.analysis_error[path] = False
            self.saved_settings[path] = {"start": "", "end": ""}
            self.update_forward_column()
            threading.Thread(target=self.analyze_and_update,
                           args=(path, "forward"), daemon=True).start()
            self.update_buttons_state()
    
    def select_reverse_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            self.reverse_video_path = path
            self.analysis_status[path] = True
            self.analysis_error[path] = False
            self.saved_settings[path] = {"start": "", "end": ""}
            self.update_reverse_column()
            threading.Thread(target=self.analyze_and_update,
                           args=(path, "reverse"), daemon=True).start()
            self.update_buttons_state()
    
    def add_forward_file(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if path and path not in self.road_files and path != self.video_path:
            self.road_files.append(path)
            self.analysis_status[path] = True
            self.analysis_error[path] = False
            self.saved_settings[path] = {"start": "", "end": ""}
            self.update_forward_column()
            threading.Thread(target=self.analyze_and_update,
                           args=(path, "forward"), daemon=True).start()
            self.update_buttons_state()
    
    def add_reverse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if path and path not in self.reverse_road_files and path != self.reverse_video_path:
            self.reverse_road_files.append(path)
            self.analysis_status[path] = True
            self.analysis_error[path] = False
            self.saved_settings[path] = {"start": "", "end": ""}
            self.update_reverse_column()
            threading.Thread(target=self.analyze_and_update,
                           args=(path, "reverse"), daemon=True).start()
            self.update_buttons_state()
    
    def remove_forward_video(self):
        if self.video_path and self.video_path in self.analysis_status:
            del self.analysis_status[self.video_path]
            if self.video_path in self.analysis_error:
                del self.analysis_error[self.video_path]
            if self.video_path in self.saved_settings:
                del self.saved_settings[self.video_path]
            if self.video_path in self.video_bounds:  
                del self.video_bounds[self.video_path]
        self.video_path = None
        self.update_forward_column()
        self.update_buttons_state()
    
    def remove_reverse_video(self):
        if self.reverse_video_path and self.reverse_video_path in self.analysis_status:
            del self.analysis_status[self.reverse_video_path]
            if self.reverse_video_path in self.analysis_error:
                del self.analysis_error[self.reverse_video_path]
            if self.reverse_video_path in self.saved_settings:
                del self.saved_settings[self.reverse_video_path]
            if self.reverse_video_path in self.video_bounds:  
                del self.video_bounds[self.reverse_video_path]
        self.reverse_video_path = None
        self.update_reverse_column()
        self.update_buttons_state()
    
    def remove_forward_file(self, file):
        if file in self.road_files:
            self.road_files.remove(file)
        if file in self.saved_settings:
            del self.saved_settings[file]
        if file in self.analysis_status:
            del self.analysis_status[file]
        if file in self.analysis_error:
            del self.analysis_error[file]
        self.update_forward_column()
        self.update_buttons_state()
    
    def remove_reverse_file(self, file):
        if file in self.reverse_road_files:
            self.reverse_road_files.remove(file)
        if file in self.saved_settings:
            del self.saved_settings[file]
        if file in self.analysis_status:
            del self.analysis_status[file]
        if file in self.analysis_error:
            del self.analysis_error[file]
        self.update_reverse_column()
        self.update_buttons_state()

    # АНАЛИЗ
    def analyze_and_update(self, path, direction):
        start, end, error = analyze_video(path)
        self.root.after(0, lambda: self.apply_result(path, start, end, error, direction))

    def apply_result(self, path, start, end, error, direction):
        self.analysis_status[path] = False

        if error:
            self.analysis_error[path] = True
            self.saved_settings[path] = {"start": "", "end": ""}
            self.video_bounds[path] = {"start": 0, "end": 0}
        else:
            self.analysis_error[path] = False
            self.saved_settings[path] = {"start": start, "end": end}
            # Сохраняем ИСХОДНЫЕ границы видео в метрах
            self.video_bounds[path] = {
                "start": self.km_to_meters(start),
                "end": self.km_to_meters(end)
            }

        if direction == "forward":
            self.update_forward_column()
        else:
            self.update_reverse_column()
        
        self.update_buttons_state()

    def update_buttons_state(self):
        all_files = []
        if self.video_path:
            all_files.append(self.video_path)
        all_files.extend(self.road_files)
        if self.reverse_video_path:
            all_files.append(self.reverse_video_path)
        all_files.extend(self.reverse_road_files)
        
        analyzing = any(self.analysis_status.get(f, False) for f in all_files)
        has_error = any(self.analysis_error.get(f, False) for f in all_files)

        # Проверяем существование кнопок перед изменением
        if hasattr(self, 'settings_btn') and self.settings_btn:
            try:
                if analyzing or has_error:
                    self.settings_btn.config(state="disabled")
                    self.report_btn.config(state="disabled")
                else:
                    self.settings_btn.config(state="normal")
                    self.report_btn.config(state="normal")
            except tk.TclError:
                pass  # Виджет уже уничтожен

    # НАСТРОЙКИ
    def open_settings(self):
        all_files = []
        if self.video_path:
            all_files.append(self.video_path)
        all_files.extend(self.road_files)
        
        has_reverse = self.reverse_video_path is not None or len(self.reverse_road_files) > 0
        
        if any(self.analysis_status.get(f, False) for f in all_files):
            self.error_var.set("Дождитесь окончания анализа")
            return
        if any(self.analysis_error.get(f, False) for f in all_files):
            self.error_var.set("Есть ошибки анализа")
            return

        self.error_var.set("")
        
        self.temp_settings = {} 
        
        self.clear()

        # Создаем фрейм для настроек
        self.settings_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        self.settings_frame.pack(fill="both", expand=True)
        
        if has_reverse:
            # Создаем контейнер для двух таблиц
            main_container = tk.Frame(self.settings_frame, bg=self.BG_COLOR)
            main_container.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Левая таблица
            left_frame = tk.Frame(main_container, bg=self.BG_COLOR)
            left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
            
            tk.Label(left_frame, bg=self.BG_COLOR, text="Прямое направление", font=("Arial", 13, "bold"), 
                    fg="#333333").pack(pady=(0, 10))
            
            # Создаем контейнер для таблицы 
            left_table_container = tk.Frame(left_frame, bg=self.BG_COLOR)
            left_table_container.pack(fill="both", expand=True) 
            
            # Используем create_settings_table для левой таблицы
            self.create_settings_table(left_table_container, all_files, 0)
            
            # Правая таблица
            right_frame = tk.Frame(main_container, bg=self.BG_COLOR)
            right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
            
            tk.Label(right_frame, bg=self.BG_COLOR, text="Обратное направление", font=("Arial", 13, "bold"),
                    fg="#333333").pack(pady=(0, 10))
            
            right_table_container = tk.Frame(right_frame, bg=self.BG_COLOR)
            right_table_container.pack(fill="both", expand=True)
            
            reverse_files = []
            if self.reverse_video_path:
                reverse_files.append(self.reverse_video_path)
            reverse_files.extend(self.reverse_road_files)
            
            # Используем create_settings_table для правой таблицы
            self.create_settings_table(right_table_container, reverse_files, len(all_files))
            
        else:
            main_frame = tk.Frame(self.settings_frame, bg=self.BG_COLOR)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            tk.Label(main_frame, text="Настройки", bg=self.BG_COLOR, font=("Arial", 14, "bold"),
                    fg="#333333").pack(pady=(0, 15))
            
            table_container = tk.Frame(main_frame, bg=self.BG_COLOR)
            table_container.pack(fill="both", expand=True)
            
            # Используем create_settings_table
            self.create_settings_table(table_container, all_files, 0)

        # Нижняя панель с кнопками (общая для всех случаев)
        bottom_frame = tk.Frame(self.settings_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", fill="x", pady=30)  

        button_container = tk.Frame(bottom_frame, bg=self.BG_COLOR)
        button_container.pack(fill="x", pady=10)

        left_spacer = tk.Frame(button_container, bg=self.BG_COLOR)
        left_spacer.pack(side="left", expand=True)
        
        center_buttons = tk.Frame(button_container, bg=self.BG_COLOR)
        center_buttons.pack(side="left", expand=True)
        
        right_spacer = tk.Frame(button_container, bg=self.BG_COLOR)
        right_spacer.pack(side="left", expand=True)
        
        tk.Label(bottom_frame, bg=self.BG_COLOR, textvariable=self.error_var, fg="red", 
                font=("Arial", 9)).pack(pady=5)
        
        back_btn = RoundedButtonImage(
            center_buttons, 
            text="Отменить",
            command=self.back_to_main,
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
        back_btn.pack(side="left", padx=80)  
        
        # Кнопка "Сохранить"
        save_btn = RoundedButtonImage(
            center_buttons, 
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
        save_btn.pack(side="left", padx=80)
        
        
        
    def create_settings_table(self, parent, files, start_index):
        """Создает таблицу с подстройкой высоты под количество строк"""
        
        # Создаем основной контейнер с окантовкой
        table_frame = tk.Frame(parent, bg="#085492", bd=0, highlightthickness=2, highlightbackground="#085492",  highlightcolor="#085492")
        table_frame.pack(fill="x", padx=10)
        
        # Внутренний контейнер
        inner_container = tk.Frame(table_frame, bg="#085492")
        inner_container.pack(fill="both", padx=1, pady=1)  
        

        # Заголовки таблицы (шапка)
        headers_frame = tk.Frame(inner_container, bg="#085492", height=40)
        headers_frame.pack(fill="x")
        headers_frame.pack_propagate(False)

        # Внутренний фрейм для заголовков (аналогично строкам)
        headers_inner = tk.Frame(headers_frame, bg="#5BB5FF")
        headers_inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Левая ячейка шапки
        header_cell_file = tk.Frame(headers_inner, bg="#5BB5FF")
        header_cell_file.place(relx=0, rely=0, relwidth=0.4, relheight=1)

        # Вертикальная граница в шапке (как в строках)
        header_sep = tk.Frame(headers_inner, bg="#085492", width=2)
        header_sep.place(relx=0.4, rely=0, relheight=1)

        # Правая ячейка шапки
        header_cell_address = tk.Frame(headers_inner, bg="#5BB5FF")
        header_cell_address.place(relx=0.402, rely=0, relwidth=0.598, relheight=1)

        # Текст заголовка "Файл"
        tk.Label(
            header_cell_file,
            text="Файл",
            font=("Arial", 11, "bold"),
            fg="white",
            bg="#5BB5FF",
            anchor="center"
        ).pack(expand=True, fill="both")

        # Текст заголовка "Адрес дороги"
        tk.Label(
            header_cell_address,
            text="Адрес дороги",
            font=("Arial", 11, "bold"),
            fg="white",
            bg="#5BB5FF",
            anchor="center"
        ).pack(expand=True, fill="both")

        # Черная горизонтальная граница между шапкой и строками
        header_bottom_border = tk.Frame(inner_container, bg="#085492", height=2)
        header_bottom_border.pack(fill="x")
        
        # Параметры строк
        row_height = 49
        row_count = len(files)

        total_rows_height = row_height * row_count
        rows_container = tk.Frame(inner_container, bg="#085492", height=total_rows_height)
        rows_container.pack(fill="x")  # Только горизонтальное заполнение
        rows_container.pack_propagate(False)
        
        # Определяем нужно ли показывать скролл
        max_visible = 8
        if row_count > max_visible:
            # Высота с прокруткой
            scroll_height = row_height * max_visible
            rows_container.configure(height=scroll_height)
            
            canvas = tk.Canvas(rows_container, highlightthickness=0, bg="#085492", height=scroll_height)
            scrollbar = tk.Scrollbar(rows_container, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#085492")
            
            scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Создаем строки в scrollable_frame
            self._create_table_rows(scrollable_frame, files, row_height)
            
        else:
            # Строк мало - скролл не нужен, точная высота
            rows_container.configure(height=total_rows_height)
            self._create_table_rows(rows_container, files, row_height)
        
        # Устанавливаем общую высоту inner_container
        inner_container.update_idletasks()
        total_height = 40 + 2 + total_rows_height  # шапка + граница + строки
        inner_container.configure(height=total_height)
        inner_container.pack_propagate(False)
        
        # Устанавливаем общую высоту table_frame
        table_frame.configure(height=total_height + 4)  # +4 на границы
        table_frame.pack_propagate(False)
        

    def _create_table_rows(self, parent, files, row_height):
        """Создает строки таблицы"""
        for i, f in enumerate(files):
            # Контейнер строки
            row_container = tk.Frame(parent, bg="#085492", height=row_height)
            row_container.pack(fill="x")
            row_container.pack_propagate(False)
            
            # Фон строки (белый)
            row_bg = tk.Frame(row_container, bg="white")
            row_bg.pack(fill="both", expand=True, padx=1, pady=1)
            
            # Левая ячейка (название файла)
            cell_file = tk.Frame(row_bg, bg="white")
            cell_file.place(relx=0, rely=0, relwidth=0.4, relheight=1)
            
            # Черная вертикальная граница между ячейками
            vertical_sep = tk.Frame(row_bg, bg="#085492", width=2)
            vertical_sep.place(relx=0.4, rely=0, relheight=1)
            
            # Правая ячейка (адрес)
            cell_address = tk.Frame(row_bg, bg="white")
            cell_address.place(relx=0.402, rely=0, relwidth=0.598, relheight=1)
            
            # Название файла (по центру)
            file_label = tk.Label(
                cell_file,
                text=os.path.basename(f),
                font=("Arial", 10),
                bg="white",
                anchor="center"
            )
            file_label.pack(expand=True, fill="both", padx=8, pady=8)
            
            # Элементы адреса
            current = self.saved_settings[f]
            sv = tk.StringVar(value=current["start"])
            ev = tk.StringVar(value=current["end"])
            
            # ИСХОДНЫЕ границы видео (неизменяемые)
            bounds = self.video_bounds.get(f, {"start": 0, "end": 0})
            rs = bounds["start"]  # исходное начало видео
            re = bounds["end"]    # исходный конец видео 
            
            # Контейнер для элементов адреса
            address_frame = tk.Frame(cell_address, bg="white")
            address_frame.pack(expand=True, fill="both")
            
            # Центрирование элементов
            for col in range(9):
                address_frame.grid_columnconfigure(col, weight=0)
            address_frame.grid_columnconfigure(0, weight=1)
            address_frame.grid_columnconfigure(8, weight=1)
            
            # Метка "Начало"
            tk.Label(
                address_frame,
                text="Начало:",
                font=("Arial", 10),
                bg="white"
            ).grid(row=0, column=1, padx=5)
            
            # Поле ввода начала
            start_entry = tk.Entry(
                address_frame,
                textvariable=sv,
                width=8,
                font=("Arial", 9),
                relief="solid",
                bd=1,
                justify="center"
            )
            start_entry.grid(row=0, column=2, padx=2)
            
            # Кнопки для начала
            start_buttons = tk.Frame(address_frame, bg="white")
            start_buttons.grid(row=0, column=3, padx=2)
            
            tk.Button(
                start_buttons,
                text="▲",
                command=lambda v=sv, o=ev, rs=rs, re=re: self.change_km(v, o, 100, rs, re, True),
                width=2,
                height=1,
                relief="flat",
                bg="#e0e0e0",
                activebackground="#d0d0d0",
                font=("Arial", 8)
            ).pack(side="top")
            
            tk.Button(
                start_buttons,
                text="▼",
                command=lambda v=sv, o=ev, rs=rs, re=re: self.change_km(v, o, -100, rs, re, True),
                width=2,
                height=1,
                relief="flat",
                bg="#e0e0e0",
                activebackground="#d0d0d0",
                font=("Arial", 8)
            ).pack(side="bottom")
            
            # Разделитель
            tk.Label(
                address_frame,
                text="→",
                font=("Arial", 12),
                bg="white",
                fg="#666"
            ).grid(row=0, column=4, padx=10)
            
            # Метка "Конец"
            tk.Label(
                address_frame,
                text="Конец:",
                font=("Arial", 10),
                bg="white"
            ).grid(row=0, column=5, padx=5)
            
            # Поле ввода конца
            end_entry = tk.Entry(
                address_frame,
                textvariable=ev,
                width=8,
                font=("Arial", 9),
                relief="solid",
                bd=1,
                justify="center"
            )
            end_entry.grid(row=0, column=6, padx=2)
            
            # Кнопки для конца
            end_buttons = tk.Frame(address_frame, bg="white")
            end_buttons.grid(row=0, column=7, padx=2)
            
            tk.Button(
                end_buttons,
                text="▲",
                command=lambda v=ev, o=sv, rs=rs, re=re: self.change_km(v, o, 100, rs, re, False),
                width=2,
                height=1,
                relief="flat",
                bg="#e0e0e0",
                activebackground="#d0d0d0",
                font=("Arial", 8)
            ).pack(side="top")
            
            tk.Button(
                end_buttons,
                text="▼",
                command=lambda v=ev, o=sv, rs=rs, re=re: self.change_km(v, o, -100, rs, re, False),
                width=2,
                height=1,
                relief="flat",
                bg="#e0e0e0",
                activebackground="#d0d0d0",
                font=("Arial", 8)
            ).pack(side="bottom")
            
            # Сохраняем переменные
            if f not in self.temp_settings:
                self.temp_settings[f] = (sv, ev, rs, re)
            else:
                # Обновляем существующие
                self.temp_settings[f] = (sv, ev, rs, re)
            
            # Черная горизонтальная граница между строками (кроме последней)
            if i < len(files) - 1:
                bottom_border = tk.Frame(row_container, bg="#085492", height=2)
                bottom_border.place(relx=0, rely=1, relwidth=1)

    def change_km(self, var, other, delta, rs, re, is_start):
        try:
            # Проверяем, что var и other еще существуют
            if not var or not other:
                return
                
            cur = self.km_to_meters(var.get())
            oth = self.km_to_meters(other.get())
            new = cur + delta
            
            print(f"DEBUG: cur={cur}, oth={oth}, new={new}, rs={rs}, re={re}, is_start={is_start}")

            # Проверка границ видео
            if new < rs or new > re:
                self.error_var.set(f"Выход за границы видео (допустимо: {self.meters_to_km(rs)} - {self.meters_to_km(re)})")
                return
            
            # Проверка для начала (должно быть меньше конца)
            if is_start and new >= oth:
                self.error_var.set(f"Начало ({self.meters_to_km(new)}) должно быть меньше конца ({self.meters_to_km(oth)})")
                return
            
            # Проверка для конца (должно быть больше начала)
            if not is_start and new <= oth:
                self.error_var.set(f"Конец ({self.meters_to_km(new)}) должен быть больше начала ({self.meters_to_km(oth)})")
                return

            self.error_var.set("")
            var.set(self.meters_to_km(new))
        except (tk.TclError, RuntimeError, AttributeError):
            pass
        
    def back_to_main(self):
        """Возврат на главный экран"""
        self.temp_settings = {}  
        if hasattr(self, 'settings_frame'):
            self.settings_frame = None
        self.clear()
        self.show_second_screen()

    def save_settings(self):
        if not self.temp_settings:
            self.error_var.set("Нет настроек для сохранения")
            return
            
        for f, (s, e, rs, re) in self.temp_settings.items():
            try:
                start = self.km_to_meters(s.get())
                end = self.km_to_meters(e.get())
                
                # Проверка по ИСХОДНЫМ границам видео
                if start < rs:
                    self.error_var.set(f"Начало {s.get()} меньше допустимого {self.meters_to_km(rs)} для {os.path.basename(f)}")
                    return
                if end > re:
                    self.error_var.set(f"Конец {e.get()} больше допустимого {self.meters_to_km(re)} для {os.path.basename(f)}")
                    return
                if start >= end:
                    self.error_var.set(f"Начало должно быть меньше конца для {os.path.basename(f)}")
                    return
            except tk.TclError:
                self.error_var.set(f"Ошибка доступа к данным файла {os.path.basename(f)}")
                return
        
        # Сохраняем только пользовательские настройки
        for f, (s, e, *_ ) in self.temp_settings.items():
            try:
                self.saved_settings[f] = {"start": s.get(), "end": e.get()}
            except tk.TclError:
                pass
        
        self.temp_settings = {}
        
        try:
            if self.video_path:
                self.update_forward_column()
            if self.reverse_video_path:
                self.update_reverse_column()
        except tk.TclError:
            pass
        
        self.back_to_main()
    
    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()