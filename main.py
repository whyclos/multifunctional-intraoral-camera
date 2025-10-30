import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import cv2
from PIL import Image, ImageTk
import os
import serial
import serial.tools.list_ports
import time
from datetime import datetime
import threading

class MedicalCameraController:
    def __init__(self, root):
        self.root = root
        self.patient_surname = ""
        self.images_dir = "medical_images"
        
        self.setup_variables()
        self.get_patient_info()
        self.create_gui()
        self.setup_arduino()
        
    def get_patient_info(self):
        """Запрос фамилии пациента при запуске программы"""
        while not self.patient_surname:
            surname = simpledialog.askstring("Пациент", "Введите фамилию пациента:", 
                                           parent=self.root)
            if surname:
                self.patient_surname = surname.strip()
                # Создаем основную папку если ее нет
                os.makedirs(self.images_dir, exist_ok=True)
                # Создаем папку для пациента
                self.patient_folder = os.path.join(self.images_dir, self.patient_surname)
                os.makedirs(self.patient_folder, exist_ok=True)
                print(f"[INIT] Папка пациента создана: {self.patient_folder}")
            else:
                if messagebox.askretrycancel("Ошибка", "Фамилия пациента обязательна для работы программы."):
                    continue
                else:
                    self.root.destroy()
                    return
        
    def setup_variables(self):
        """Инициализация всех переменных состояния"""
        self.camera_active = False
        self.camera = None
        self.arduino = None
        self.arduino_connected = False
        self.last_photo_path = None
        
        # Инициализируем переменные для GUI
        self.debug_label = None
        self.status_label = None
        self.video_label = None
        self.photo_label = None
        self.arduino_status = None
        self.camera_status = None
        self.button_status = None
        self.led_status = None  # Новый статус для светодиодов
        self.start_camera_btn = None
        self.stop_camera_btn = None
        self.take_photo_btn = None
        
    def create_gui(self):
        """Создание графического интерфейса"""
        self.root.title(f"Medical Camera Controller - Пациент: {self.patient_surname}")
        self.root.geometry("1200x700")
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.create_video_panel(main_frame)
        self.create_control_panel(main_frame)
        self.create_status_bar()
        self.create_debug_panel(main_frame)
        
        # Обновляем статус после создания всех элементов GUI
        self.update_status(f"Программа запущена для пациента: {self.patient_surname}")
        self.update_debug(f"Папка для снимков: {self.patient_folder}")
        
    def create_video_panel(self, parent):
        video_frame = ttk.LabelFrame(parent, text="Видео с камеры", padding=10)
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.video_label = ttk.Label(video_frame, background="black")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        self.video_placeholder = ttk.Label(video_frame, 
                                         text="Камера выключена\n\nКороткое нажатие: Вкл/Выкл камеры\nДлинное нажатие: Сделать снимок", 
                                         foreground="white", background="black",
                                         font=("Arial", 12))
        self.video_placeholder.pack(fill=tk.BOTH, expand=True)
        
    def create_control_panel(self, parent):
        control_frame = ttk.Frame(parent)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Информация о пациенте
        patient_frame = ttk.LabelFrame(control_frame, text="Информация о пациенте", padding=10)
        patient_frame.pack(fill=tk.X, pady=(0, 10))
        
        patient_label = ttk.Label(patient_frame, text=f"Пациент: {self.patient_surname}", 
                                font=("Arial", 10, "bold"))
        patient_label.pack(anchor=tk.W)
        
        date_label = ttk.Label(patient_frame, text=f"Дата: {datetime.now().strftime('%d.%m.%Y')}")
        date_label.pack(anchor=tk.W)
        
        # Путь к папке пациента
        self.folder_label = ttk.Label(patient_frame, text=f"Папка: {self.patient_folder}", 
                               foreground="gray", font=("Arial", 8))
        self.folder_label.pack(anchor=tk.W)
        
        # Статус системы
        info_frame = ttk.LabelFrame(control_frame, text="Статус системы", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.arduino_status = ttk.Label(info_frame, text="Arduino: Не подключен", foreground="red")
        self.arduino_status.pack(anchor=tk.W)
        
        self.camera_status = ttk.Label(info_frame, text="Камера: ВЫКЛ", foreground="red")
        self.camera_status.pack(anchor=tk.W)
        
        self.led_status = ttk.Label(info_frame, text="Светодиоды: ВЫКЛ", foreground="red")
        self.led_status.pack(anchor=tk.W)
        
        self.button_status = ttk.Label(info_frame, text="Кнопка: Готова", foreground="blue")
        self.button_status.pack(anchor=tk.W)
        
        # Превью последнего снимка
        photo_frame = ttk.LabelFrame(control_frame, text="Последний снимок", padding=10)
        photo_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.photo_label = ttk.Label(photo_frame, text="Снимков еще нет", 
                                   background="lightgray", anchor=tk.CENTER)
        self.photo_label.pack(fill=tk.BOTH, expand=True, ipady=50)
        
        # Ручное управление
        manual_frame = ttk.LabelFrame(control_frame, text="Ручное управление", padding=10)
        manual_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_camera_btn = ttk.Button(manual_frame, text="Включить камеру", 
                                         command=self.manual_start_camera)
        self.start_camera_btn.pack(fill=tk.X, pady=2)
        
        self.stop_camera_btn = ttk.Button(manual_frame, text="Выключить камеру", 
                                        command=self.manual_stop_camera,
                                        state="disabled")
        self.stop_camera_btn.pack(fill=tk.X, pady=2)
        
        self.take_photo_btn = ttk.Button(manual_frame, text="Сделать снимок", 
                                       command=self.manual_take_photo,
                                       state="disabled")
        self.take_photo_btn.pack(fill=tk.X, pady=2)
        
    def create_debug_panel(self, parent):
        """Панель отладки"""
        debug_frame = ttk.LabelFrame(parent, text="События кнопки", padding=10)
        debug_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        self.debug_label = ttk.Label(debug_frame, text="Ожидание событий кнопки...", foreground="blue")
        self.debug_label.pack(anchor=tk.W)
        
    def create_status_bar(self):
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(status_frame, text="Готов к подключению...")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
    def update_button_states(self):
        """Обновление состояний кнопок ручного управления"""
        if self.camera_active:
            # Камера включена - активируем кнопки Стоп и Снимок, деактивируем Старт
            self.start_camera_btn.config(state="disabled")
            self.stop_camera_btn.config(state="normal")
            self.take_photo_btn.config(state="normal")
        else:
            # Камера выключена - активируем кнопку Старт, деактивируем Стоп и Снимок
            self.start_camera_btn.config(state="normal")
            self.stop_camera_btn.config(state="disabled")
            self.take_photo_btn.config(state="disabled")
        
    def setup_arduino(self):
        """Настройка подключения к Arduino"""
        def connect_arduino():
            try:
                ports = serial.tools.list_ports.comports()
                arduino_port = None
                
                self.update_debug("Поиск Arduino...")
                
                for port in ports:
                    port_description = port.description.lower()
                    if any(keyword in port_description for keyword in 
                          ['arduino', 'ch340', 'cp210', 'usb serial']):
                        arduino_port = port.device
                        self.update_debug(f"Arduino найден: {arduino_port}")
                        break
                
                if not arduino_port:
                    self.update_status("Arduino не найден!")
                    return
                
                self.arduino = serial.Serial(arduino_port, 9600, timeout=1)
                time.sleep(2)
                self.arduino.reset_input_buffer()
                
                self.arduino_connected = True
                self.update_gui_status()
                self.update_status(f"Подключено к Arduino")
                
                # Запускаем мониторинг кнопки
                self.start_button_monitoring()
                
            except Exception as e:
                self.update_status(f"Ошибка подключения Arduino: {str(e)}")
        
        arduino_thread = threading.Thread(target=connect_arduino, daemon=True)
        arduino_thread.start()
        
    def start_button_monitoring(self):
        """Запуск мониторинга кнопки Arduino"""
        def monitor_button():
            self.update_debug("Мониторинг кнопки запущен - ожидание SHORT_PRESS или LONG_PRESS")
            
            while self.arduino_connected and self.arduino:
                try:
                    if self.arduino.in_waiting > 0:
                        line = self.arduino.readline().decode('utf-8').strip()
                        self.update_debug(f"Получено: '{line}'")
                        
                        # Обрабатываем команды
                        if line == "SHORT_PRESS":
                            self.update_debug("SHORT_PRESS обнаружено - переключение камеры")
                            self.root.after(0, self.handle_short_press)
                            
                        elif line == "LONG_PRESS":
                            self.update_debug("LONG_PRESS обнаружено - создание снимка")
                            self.root.after(0, self.handle_long_press)
                            
                except Exception as e:
                    self.update_debug(f"Ошибка мониторинга: {e}")
                    time.sleep(0.1)
                    
                time.sleep(0.01)
        
        button_thread = threading.Thread(target=monitor_button, daemon=True)
        button_thread.start()
        
    def handle_short_press(self):
        """Обработка КОРОТКОГО нажатия - переключение камеры"""
        self.update_button_status("Короткое нажатие - Переключение камеры")
        self.toggle_camera()
        
    def handle_long_press(self):
        """Обработка ДЛИННОГО нажатия - создание снимка"""
        self.update_button_status("Длинное нажатие - Создание снимка")
        self.take_photo_action()
            
    def toggle_camera(self):
        """Включение/выключение камеры"""
        if not self.camera_active:
            self.start_camera()
        else:
            self.stop_camera()
            
    def start_camera(self):
        """Запуск камеры"""
        try:
            available_cameras = self.get_available_cameras()
            
            if not available_cameras:
                self.update_status("Камеры не найдены!")
                return
                
            camera_index = max(available_cameras)
            self.camera = cv2.VideoCapture(camera_index)
            
            if not self.camera.isOpened():
                self.update_status(f"Не удалось открыть камеру {camera_index}")
                return
                
            self.camera_active = True
            self.update_gui_status()
            self.update_status(f"Камера включена")
            self.update_button_states()
            
            self.video_placeholder.pack_forget()
            self.update_video_feed()
            
        except Exception as e:
            self.update_status(f"Ошибка запуска камеры: {str(e)}")
            
    def stop_camera(self):
        """Остановка камеры"""
        if self.camera:
            self.camera.release()
            self.camera = None
            
        self.camera_active = False
        self.update_gui_status()
        self.update_status("Камера выключена")
        self.update_button_states()
        
        self.video_placeholder.pack(fill=tk.BOTH, expand=True)
        
    def take_photo_action(self):
        """Действие по созданию снимка"""
        if not self.camera_active:
            self.update_status("Камера не активна! Невозможно сделать снимок.")
            return
            
        self.take_photo()
        
    def take_photo(self):
        """Создание снимка через PIL (рабочий метод)"""
        if not self.camera_active or not self.camera:
            return
            
        try:
            ret, frame = self.camera.read()
            
            if ret:
                # Создаем имя файла: Фамилия_ГГГГ-ММ-ДД_ЧЧ-ММ-СС.jpg
                timestamp = datetime.now()
                date_str = timestamp.strftime("%Y-%m-%d")
                time_str = timestamp.strftime("%H-%M-%S")
                
                # Имя файла
                filename = f"{self.patient_surname}_{date_str}_{time_str}.jpg"
                filepath = os.path.join(self.patient_folder, filename)
                
                self.update_debug(f"Сохранение снимка через PIL: {filepath}")
                
                # СОХРАНЕНИЕ ЧЕРЕЗ PIL (РАБОЧИЙ МЕТОД)
                # Конвертируем BGR (OpenCV) в RGB (PIL)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                # Сохраняем через PIL с высоким качеством
                pil_image.save(filepath, 'JPEG', quality=95)
                
                self.last_photo_path = filepath
                self.update_photo_preview(frame)
                self.update_status(f"Снимок сохранен: {filename}")
                self.update_debug("✅ Снимок успешно сохранен через PIL!")
                
                # Проверяем что файл действительно создался
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    self.update_debug(f"Файл создан, размер: {file_size} байт")
                else:
                    self.update_debug("❌ ОШИБКА: Файл не создан!")
                
        except Exception as e:
            error_msg = f"Ошибка создания снимка: {str(e)}"
            self.update_status(error_msg)
            self.update_debug(f"❌ {error_msg}")
            
    def get_available_cameras(self, max_test=5):
        """Получение списка доступных камер"""
        available_cameras = []
        
        for i in range(max_test):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
                
        return available_cameras
        
    def update_video_feed(self):
        """Обновление видео потока в GUI"""
        if self.camera_active and self.camera:
            try:
                ret, frame = self.camera.read()
                
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    h, w = frame_rgb.shape[:2]
                    max_width = 800
                    max_height = 600
                    
                    if w > max_width or h > max_height:
                        scale = min(max_width/w, max_height/h)
                        new_w, new_h = int(w*scale), int(h*scale)
                        frame_rgb = cv2.resize(frame_rgb, (new_w, new_h))
                    
                    photo = ImageTk.PhotoImage(Image.fromarray(frame_rgb))
                    
                    self.video_label.configure(image=photo)
                    self.video_label.image = photo
                    
            except Exception as e:
                print(f"Ошибка обновления видео: {e}")
                
        if self.camera_active:
            self.root.after(30, self.update_video_feed)
            
    def update_photo_preview(self, frame):
        """Обновление превью последнего снимка"""
        try:
            h, w = frame.shape[:2]
            max_size = 300
            
            if w > max_size or h > max_size:
                scale = min(max_size/w, max_size/h)
                new_w, new_h = int(w*scale), int(h*scale)
                frame_resized = cv2.resize(frame, (new_w, new_h))
            else:
                frame_resized = frame
                
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            photo = ImageTk.PhotoImage(Image.fromarray(frame_rgb))
            
            self.photo_label.configure(image=photo, text="")
            self.photo_label.image = photo
            
        except Exception as e:
            print(f"Ошибка обновления превью: {e}")
            
    def update_gui_status(self):
        """Обновление статусов в GUI"""
        arduino_text = "Arduino: Подключен" if self.arduino_connected else "Arduino: Не подключен"
        arduino_color = "green" if self.arduino_connected else "red"
        self.arduino_status.config(text=arduino_text, foreground=arduino_color)
        
        camera_text = "Камера: ВКЛ" if self.camera_active else "Камера: ВЫКЛ"
        camera_color = "green" if self.camera_active else "red"
        self.camera_status.config(text=camera_text, foreground=camera_color)
        
        # Новый статус для светодиодов
        led_text = "Светодиоды: ВКЛ" if self.camera_active else "Светодиоды: ВЫКЛ"
        led_color = "green" if self.camera_active else "red"
        self.led_status.config(text=led_text, foreground=led_color)
        
    def update_button_status(self, message):
        """Обновление статуса кнопки"""
        self.button_status.config(text=f"Кнопка: {message}", foreground="green")
        self.root.after(2000, lambda: self.button_status.config(text="Кнопка: Готова", foreground="blue"))
        
    def update_status(self, message):
        """Обновление статус бара"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_label.config(text=f"[{timestamp}] {message}")
        print(f"[{timestamp}] {message}")
        
    def update_debug(self, message):
        """Обновление отладочной информации"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.debug_label.config(text=f"[{timestamp}] {message}")
        print(f"[DEBUG] {message}")
        
    def manual_start_camera(self):
        """Ручное включение камеры"""
        if not self.camera_active:
            self.start_camera()
            
    def manual_stop_camera(self):
        """Ручное выключение камеры"""
        if self.camera_active:
            self.stop_camera()
            
    def manual_take_photo(self):
        """Ручное создание снимка"""
        if self.camera_active:
            self.take_photo()
            
    def on_closing(self):
        """Обработчик закрытия приложения"""
        self.stop_camera()
        if self.arduino and self.arduino_connected:
            self.arduino.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MedicalCameraController(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()