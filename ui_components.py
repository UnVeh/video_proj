import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import os
from tkinter import ttk
import math


class RoundedButtonImage(tk.Button):
    def __init__(self, parent, text="", command=None,
                 width=120, height=40, radius=20,
                 bg_color="#4CAF50", hover_color="#45a049",
                 text_color="white", font=("Arial", 10, "bold"),
                 border_width=2, border_color="#ffffff", button_bg=None):
        
        # Сохраняем параметры
        self.border_width = border_width
        self.border_color = border_color
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.width = width
        self.height = height
        self.radius = radius
        
        if button_bg is None:
            button_bg = parent.cget("bg")
        
        # Создаем изображения для нормального состояния и наведения
        self.normal_image = self._create_rounded_image(
            width, height, radius, bg_color, border_width, border_color
        )
        self.hover_image = self._create_rounded_image(
            width, height, radius, hover_color, border_width, border_color
        )
        
        # Правильно вызываем конструктор tk.Button
        tk.Button.__init__(
            self, parent, 
            text=text, 
            command=command,
            image=self.normal_image,
            compound="center",
            font=font,
            fg=text_color,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            bg=button_bg,  
            activebackground=button_bg
        )
        
        # Привязываем события наведения
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
    def _create_rounded_image(self, width, height, radius, color, border_width=0, border_color=None):
        """Создает закругленное изображение с окантовкой"""
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Рисуем закругленный прямоугольник с окантовкой
        if border_width > 0 and border_color:
            draw.rounded_rectangle(
                (border_width//2, border_width//2, 
                 width - border_width//2 - 1, 
                 height - border_width//2 - 1),
                radius=radius - border_width//2,
                fill=color,
                outline=border_color,
                width=border_width
            )
        else:
            draw.rounded_rectangle(
                (0, 0, width-1, height-1), 
                radius=radius, 
                fill=color
            )
        
        return ImageTk.PhotoImage(image)
    
    def _on_enter(self, event):
        self.config(image=self.hover_image)
        
    def _on_leave(self, event):
        self.config(image=self.normal_image)


class ImageIconButton(tk.Label):
    """Кнопка с иконкой из файла изображения"""
    
    def __init__(self, parent, image_path, command=None,
                 size=(24, 24), hover_effect=True,
                 normal_opacity=1.0, hover_opacity=0.7):
        
        self.command = command
        self.hover_effect = hover_effect
        
        # Загружаем изображение
        self.normal_image = self._load_image(image_path, size)
        self.hover_image = None
        
        if hover_effect and self.normal_image:
            self.hover_image = self._create_hover_image(image_path, size, hover_opacity)
        
        super().__init__(
            parent,
            image=self.normal_image,
            cursor="hand2",
            bg=parent.cget("bg") if hasattr(parent, 'cget') else "SystemButtonFace"
        )
        
        # Привязываем события
        self.bind("<Button-1>", self._on_click)
        if hover_effect and self.hover_image:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
        
        # Сохраняем ссылки на изображения
        self._normal_image_ref = self.normal_image
        self._hover_image_ref = self.hover_image
        
    def _load_image(self, image_path, size):
        """Загружает и изменяет размер изображения"""
        if not image_path or not os.path.exists(image_path):
            return self._create_placeholder(size)
        
        try:
            img = Image.open(image_path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Ошибка загрузки изображения {image_path}: {e}")
            return self._create_placeholder(size)
    
    def _create_hover_image(self, image_path, size, opacity):
        """Создает изображение с эффектом при наведении"""
        try:
            img = Image.open(image_path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img = img.resize(size, Image.Resampling.LANCZOS)
            
            # Изменяем прозрачность
            pixels = img.getdata()
            new_pixels = []
            for pixel in pixels:
                new_pixels.append((pixel[0], pixel[1], pixel[2], int(pixel[3] * opacity)))
            
            img.putdata(new_pixels)
            return ImageTk.PhotoImage(img)
        except:
            return self._load_image(image_path, size)
    
    def _create_placeholder(self, size):
        """Создает заглушку, если изображение не загрузилось"""
        img = Image.new('RGBA', size, (255, 0, 0, 128))
        return ImageTk.PhotoImage(img)
    
    def _on_click(self, event):
        if self.command:
            self.command()
            
    def _on_enter(self, event):
        if self.hover_image:
            self.config(image=self.hover_image)
        
    def _on_leave(self, event):
        self.config(image=self.normal_image)


class TextIconButton(tk.Label):
    """Кнопка с текстовой иконкой (эмодзи или символ)"""
    
    def __init__(self, parent, icon="✖", command=None,
                 font_size=16, normal_color="#f44336", hover_color="#d32f2f"):
        
        self.command = command
        self.normal_color = normal_color
        self.hover_color = hover_color
        
        super().__init__(
            parent,
            text=icon,
            font=("Segoe UI Emoji", font_size),
            fg=normal_color,
            bg=parent.cget("bg") if hasattr(parent, 'cget') else "SystemButtonFace",
            cursor="hand2"
        )
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
    def _on_click(self, event):
        if self.command:
            self.command()
            
    def _on_enter(self, event):
        self.config(fg=self.hover_color)
        
    def _on_leave(self, event):
        self.config(fg=self.normal_color)


# =========================
# МЕНЕДЖЕР ИКОНОК
# =========================

class IconManager:
    """Управление иконками приложения"""
    
    def __init__(self, app_dir=None):
        if app_dir is None:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.icons_dir = os.path.join(app_dir, "icons")
        self._create_icons_dir()
        self.icon_cache = {}  # Кэш для загруженных иконок
        
    def _create_icons_dir(self):
        """Создает директорию для иконок если её нет"""
        if not os.path.exists(self.icons_dir):
            os.makedirs(self.icons_dir)
            self._create_default_icons()
    
    def _create_default_icons(self):
        """Создает простые иконки по умолчанию"""
        from PIL import Image, ImageDraw
        
        icons = {
            "delete": {"color": (255, 68, 68), "symbol": "✖", "size": (24, 24)},
            "add": {"color": (76, 175, 80), "symbol": "+", "size": (24, 24)},
            "settings": {"color": (33, 150, 243), "symbol": "⚙", "size": (24, 24)},
            "edit": {"color": (255, 152, 0), "symbol": "✎", "size": (24, 24)},
            "save": {"color": (76, 175, 80), "symbol": "💾", "size": (24, 24)},
            "folder": {"color": (33, 150, 243), "symbol": "📁", "size": (24, 24)},
            "video": {"color": (156, 39, 176), "symbol": "🎬", "size": (24, 24)},
        }
        
        for icon_name, data in icons.items():
            path = os.path.join(self.icons_dir, f"{icon_name}.png")
            if not os.path.exists(path):
                img = Image.new('RGBA', data["size"], (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # Рисуем простую иконку
                if icon_name == "delete":
                    draw.line((6, 6, 18, 18), fill=data["color"], width=2)
                    draw.line((18, 6, 6, 18), fill=data["color"], width=2)
                elif icon_name == "add":
                    draw.rectangle((11, 5, 13, 19), fill=data["color"])
                    draw.rectangle((5, 11, 19, 13), fill=data["color"])
                elif icon_name == "settings":
                    draw.ellipse((8, 8, 16, 16), outline=data["color"], width=2)
                    draw.ellipse((11, 11, 13, 13), fill=data["color"])
                else:
                    # Для остальных иконок используем текст
                    draw.text((4, 2), data["symbol"], fill=data["color"], font=None)
                
                img.save(path)
        
        print(f"Создана директория с иконками: {self.icons_dir}")
    
    def get_icon_path(self, icon_name):
        """Возвращает путь к иконке"""
        for ext in ['.png', '.ico', '.gif', '.jpg', '.svg']:
            path = os.path.join(self.icons_dir, f"{icon_name}{ext}")
            if os.path.exists(path):
                return path
        return None
    
    def get_icon(self, icon_name, size=(24, 24)):
        """Возвращает загруженную иконку (с кэшированием)"""
        cache_key = f"{icon_name}_{size[0]}_{size[1]}"
        
        if cache_key not in self.icon_cache:
            path = self.get_icon_path(icon_name)
            if path:
                try:
                    img = Image.open(path)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img = img.resize(size, Image.Resampling.LANCZOS)
                    self.icon_cache[cache_key] = ImageTk.PhotoImage(img)
                except:
                    self.icon_cache[cache_key] = None
            else:
                self.icon_cache[cache_key] = None
        
        return self.icon_cache[cache_key]
    
    def create_icon_button(self, parent, icon_name, command, 
                          size=(24, 24), use_text_fallback=True):
        """Создает кнопку-иконку"""
        icon_path = self.get_icon_path(icon_name)
        
        if icon_path:
            return ImageIconButton(parent, icon_path, command, size=size)
        elif use_text_fallback:
            # Используем текстовую иконку как запасной вариант
            icons_map = {
                "delete": "🗑",
                "add": "+",
                "settings": "⚙",
                "edit": "✎",
                "save": "💾",
                "folder": "📁",
                "video": "🎬"
            }
            icon_text = icons_map.get(icon_name, "•")
            return TextIconButton(parent, icon=icon_text, command=command)
        else:
            return None


class Spinner:
    def __init__(self, parent, size=30, color="#4CAF50", speed=10, bg="#FEFEFF"):
        self.canvas = tk.Canvas(parent, width=size, height=size, highlightthickness=0, bg=bg)
        self.size = size
        self.color = color
        self.speed = speed
        self.angle = 0
        self.running = False
        

        pad = 5
        self.arc = self.canvas.create_arc(
            pad, pad, size - pad, size - pad,
            start=0, extent=210,
            style="arc",
            width=3,
            outline=color
        )

    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)

    def start(self):
        self.running = True
        self._animate()

    def stop(self):
        self.running = False

    def destroy(self):
        self.canvas.destroy()

    def _animate(self):
        if not self.running:
            return
        self.angle = (self.angle + self.speed) % 360
        self.canvas.itemconfig(self.arc, start=self.angle)
        self.canvas.after(50, self._animate)
        
        
