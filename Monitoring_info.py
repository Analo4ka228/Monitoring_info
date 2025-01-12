import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel,
    QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QTextEdit
)
from PySide6.QtCore import QTimer
import psutil
import datetime
import sqlite3
import os

DATABASE = "system_data.db"

def create_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpu TEXT,
            ram TEXT,
            disk TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_data(data):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO system_stats (cpu, ram, disk, timestamp)
        VALUES (?, ?, ?, ?)
    """, (data['cpu'], data['ram'], data['disk'], data['timestamp']))
    conn.commit()
    conn.close()

    return f"Inserted Data: {data['cpu']}% CPU, {data['ram']}% RAM, {data['disk']} at {data['timestamp']}"

def get_system_info():
    """Получает информацию о ЦП, ОЗУ и дисках."""
    cpu_usage = psutil.cpu_percent(interval=0.1)  
    mem = psutil.virtual_memory()
    mem_usage = mem.percent
    
    disk_usage_info = []
    for partition in psutil.disk_partitions(all=False):
        usage = psutil.disk_usage(partition.mountpoint)
        disk_usage_info.append(f"{partition.device}: {usage.percent}%")

    disk_usage_str = ", ".join(disk_usage_info)  # Объединяем информацию о дисках в строку

    return {
        "cpu": f"{cpu_usage:.2f}",
        "ram": f"{mem_usage:.2f}",
        "disk": disk_usage_str,  # Используем строку с информацией о всех дисках
        "timestamp": datetime.datetime.now().isoformat()
    }

class MonitorPage(QWidget):
    def __init__(self, settings_page):
        super().__init__()
        self.settings_page = settings_page

        self.cpu_label = QLabel("CPU: ")
        self.ram_label = QLabel("RAM: ")
        self.disk_label = QLabel("Disk: ")
        self.timer_label = QLabel("00:00:00")

        self.start_btn = QPushButton("Start Recording")
        self.stop_btn = QPushButton("Stop Recording")
        self.stop_btn.hide()

        v_layout = QVBoxLayout()
        v_layout.addWidget(self.cpu_label)
        v_layout.addWidget(self.ram_label)
        v_layout.addWidget(self.disk_label)
        v_layout.addWidget(self.timer_label)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.start_btn)
        h_layout.addWidget(self.stop_btn)
        v_layout.addLayout(h_layout)

        self.setLayout(v_layout)

        self.start_time = None
        self.recording = False

        # Подключаем кнопки к действиям
        self.start_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)

        # Timers
        self.timer = QTimer(self)
        self.data_timer = QTimer(self)

        # Подключаем функции к таймерам
        self.timer.timeout.connect(self.update_timer)
        self.data_timer.timeout.connect(self.record_data)

    def update_ui(self):
        data = get_system_info()
        self.cpu_label.setText(f"CPU: {data['cpu']}%")
        self.ram_label.setText(f"RAM: {data['ram']}%")
        self.disk_label.setText(f"Disk: {data['disk']}")
        return data

    def start_recording(self):
        self.recording = True
        self.start_btn.hide()
        self.stop_btn.show()
        self.start_time = datetime.datetime.now()
        self.update_timer()
        self.timer.start(1000)
        self.data_timer.start(2000)

    def stop_recording(self):
        self.recording = False
        self.stop_btn.hide()
        self.start_btn.show()
        self.timer.stop()
        self.data_timer.stop()
        self.timer_label.setText("00:00:00")
        self.start_time = None

    def update_timer(self):
        if self.start_time:
            elapsed = datetime.datetime.now() - self.start_time
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            seconds = elapsed.seconds % 60
            self.timer_label.setText(f"{hours:02}:{minutes:02}:{seconds:02}")
            self.update_ui()

    def record_data(self):
        if self.recording:
            data = get_system_info()
            message = insert_data(data)  # Записываем данные в БД
            self.settings_page.append_log(message)  # Обновляем текст в настройках

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True) 
        layout.addWidget(QLabel("System Log:"))
        layout.addWidget(self.log_view)
        self.setLayout(layout)

    def append_log(self, message):
        self.log_view.append(message)  # Добавляем новое сообщение в текстовое поле

class SystemMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Monitor")
        self.setGeometry(100, 100, 400, 300)

        self.settings_page = SettingsPage()
        self.monitor_page = MonitorPage(self.settings_page)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.monitor_page)
        self.stacked_widget.addWidget(self.settings_page)

        self.monitor_btn = QPushButton("Monitor")
        self.settings_btn = QPushButton("Settings")

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.monitor_btn)
        h_layout.addWidget(self.settings_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(h_layout)
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

        self.monitor_btn.clicked.connect(self.show_monitor_page)
        self.settings_btn.clicked.connect(self.show_settings_page)

        self.update_ui()

    def show_monitor_page(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_settings_page(self):
        self.stacked_widget.setCurrentIndex(1)

    def update_ui(self):
        self.monitor_page.update_ui()

def load_styles(app):
    """Loads styles from a .qss file."""
    style_file = os.path.join(os.path.dirname(__file__), 'style.qss')
    if os.path.exists(style_file):
        with open(style_file, 'r') as f:
            style = f.read()
            app.setStyleSheet(style)

if __name__ == "__main__":
    create_database()
    app = QApplication(sys.argv)
    load_styles(app)
    monitor = SystemMonitor()
    monitor.show()
    sys.exit(app.exec())