from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QGridLayout, QWidget, QTableWidget, QTableWidgetItem,
                             QComboBox, QPushButton, QGroupBox, QHBoxLayout,
                             QSpinBox, QTabWidget, QLineEdit, QFormLayout,
                             QMessageBox, QFileDialog, QCheckBox, QDoubleSpinBox,QSystemTrayIcon,QMenu,QAction, QSpacerItem, QSizePolicy,QFrame)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import qdarkstyle
import time
import serial
import json

START_FRAME = 0x02
END_FRAME = 0x03

class BMSMonitorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.data = {
            "voltage": [],
            "current": [],
            "temperature": [],
            "time": [],
            "cell_health": [],
            "battery_capacity": [],
            "cycle_count": []
        }
       
        self.settings = {}  # Để lưu cài đặt
         # Định nghĩa các nhãn (label) cần thiết
        self.total_voltage_label = QLabel("Tổng điện áp: 0 V")
        self.current_label = QLabel("Dòng điện: 0 A")
        self.max_temp_label = QLabel("Nhiệt độ cao nhất: 0 °C")  # Đảm bảo thuộc tính này đã được định nghĩa
        self.min_temp_label = QLabel("Nhiệt độ thấp nhất: 0 °C")
        self.status_label = QLabel("Trạng thái: OK")
        self.time_label = QLabel("Thời gian: 0 s")
        self.cycle_count_label = QLabel("Số chu kỳ: 0")
        self.cell_health_label = QLabel("Độ bền pin: OK")
    def initUI(self):
        self.setWindowTitle("Công cụ Giám sát BMS")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(qdarkstyle.load_stylesheet())
        self.setWindowIcon(QIcon("icon.png"))
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        tray_menu = QMenu()
        layout = QVBoxLayout()

         # Thêm các thành phần giao diện khác
        self.connect_button = QPushButton("Kết nối")
        self.disconnect_button = QPushButton("Ngắt kết nối")  # Thêm nút ngắt kết nối
        self.status_label = QLabel("Trạng thái: Chưa kết nối")

         # Thêm các thành phần khác như bảng, label, combobox...
        self.port_select = QComboBox()
        self.baud_rate_select = QComboBox()
        self.cell_table = QTableWidget()
        # Tạo tab widget
        tab_widget = QTabWidget(self)
         # Tạo tab tổng quan
        tab_widget.addTab(self.create_overview_tab(), "Tổng quan")

        # Bố trí giao diện
        layout = QVBoxLayout()
        layout.addWidget(tab_widget)
        self.setLayout(layout)
       

        layout.addWidget(self.port_select)
        layout.addWidget(self.baud_rate_select)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.disconnect_button)  # Thêm nút vào layout
        layout.addWidget(self.status_label)
        layout.addWidget(self.cell_table)
        # Thêm hành động vào menu 
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(quit_action)

        # Thêm menu vào biểu tượng 
        self.tray_icon.setContextMenu(tray_menu)

        # Hiển thị biểu tượng
        self.tray_icon.show()
        title_font = QFont("Arial", 18, QFont.Bold)

        # Tạo tiện ích tab chính
        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_connection_tab(), "Kết nối")
        tab_widget.addTab(self.create_overview_tab(), "Tổng quan")
        tab_widget.addTab(self.create_settings_tab(), "Thiết lập")

        main_layout = QVBoxLayout()
        main_layout.addWidget(tab_widget)

        # Đặt tiện ích trung tâm
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

    def create_connection_tab(self):
        connection_group = QGroupBox("Kết nối BMS")
        connection_group.setStyleSheet("QGroupBox { background-color: #333333; padding: 20px; border-radius: 10px; border: 1px solid #4CAF50; }")
        connection_layout = QVBoxLayout()

        # Tùy chọn kết nối
        self.port_select = QComboBox()
        self.port_select.addItems(["COM1", "COM2", "COM3", "COM4"])
        self.baud_rate_select = QComboBox()
        self.baud_rate_select.addItems(["9600", "19200", "38400", "115200"])
        self.bms_type_select = QComboBox()
        self.bms_type_select.addItems(["Loại A", "Loại B", "Loại C"])

        connection_layout.addWidget(QLabel("Cổng:"))
        connection_layout.addWidget(self.port_select)
        connection_layout.addWidget(QLabel("Baud Rate:"))
        connection_layout.addWidget(self.baud_rate_select)
        connection_layout.addWidget(QLabel("Loại BMS:"))
        connection_layout.addWidget(self.bms_type_select)

        self.connect_button = QPushButton("Kết nối", self)
        self.connect_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px; }"
                                           "QPushButton:hover { background-color: #45a049; }")
        self.connect_button.clicked.connect(self.connect_to_bms)
        connection_layout.addWidget(self.connect_button)

        connection_group.setLayout(connection_layout)
        return connection_group

    def connect_to_bms(self):
        selected_port = self.port_select.currentText()
        selected_baud = int(self.baud_rate_select.currentText())
        selected_bms_type = self.bms_type_select.currentText()
        print(f"Kết nối tới {selected_port} với Baud Rate {selected_baud} và loại BMS {selected_bms_type}")

        try:
            self.ser = serial.Serial(selected_port, baudrate=selected_baud, timeout=0.5)
            self.update_data()
        except Exception as e:
            self.show_error_message("Lỗi Kết nối", f"Có lỗi xảy ra khi kết nối tới BMS: {str(e)}")

    def create_overview_tab(self):
        overview_group = QGroupBox("Thông số BMS chi tiết")
        overview_group.setStyleSheet("QGroupBox { background-color: #282828; padding: 10px; border-radius: 10px; }")

        # Main layout for overview tab
        main_layout = QHBoxLayout()

        # Left column layout for cell data and charts
        left_layout = QVBoxLayout()

        # Data Table with fixed height
        self.cell_table = QTableWidget()
        self.cell_table.setRowCount(10)
        self.cell_table.setColumnCount(7)
        self.cell_table.setHorizontalHeaderLabels(["Điện áp (V)", "Dòng điện (A)", "Nhiệt độ (°C)", 
                                                "Trạng thái", "SoC", "Độ bền pin", "Dung lượng (Ah)"])
        self.cell_table.setFixedHeight(200)  # Fixed height for the table
        self.cell_table.setStyleSheet("QTableWidget { background-color: #4A4A4A; color: #FFFFFF; border-radius: 5px; border: 1px solid #4CAF50; }"
                                   "QHeaderView::section { background-color: #4CAF50; color: white; font-weight: bold; }"
                                   "QTableWidget::item { padding: 8px; border: 1px solid #4CAF50; }")
        left_layout.addWidget(self.cell_table)

        # Add some space between the table and the charts
        left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # SoC pie chart
        self.soc = 75  # Example state of charge
        soc_figure, soc_ax = plt.subplots(figsize=(4, 4))
        soc_ax.pie([self.soc, 100 - self.soc], labels=["Sạc", "Còn lại"], colors=["#4CAF50", "#555555"],
               autopct='%1.1f%%', startangle=90, textprops={'color': 'white', 'fontsize': 12})
        soc_ax.set_title("Tình trạng sạc", color='white', fontsize=14, fontweight='bold')
        soc_ax.set_facecolor('#1E1E1E')
        self.soc_canvas = FigureCanvas(soc_figure)
        left_layout.addWidget(self.soc_canvas)

        # Remaining capacity pie chart
        self.remaining_capacity = 60  # Example remaining capacity
        capacity_figure, capacity_ax = plt.subplots(figsize=(4, 4))
        capacity_ax.pie([self.remaining_capacity, 100 - self.remaining_capacity], labels=["Còn lại", "Sử dụng"],
                    colors=["#FFA500", "#555555"], autopct='%1.1f%%', startangle=90,
                    textprops={'color': 'white', 'fontsize': 12})
        capacity_ax.set_title("Dung lượng pin còn lại", color='white', fontsize=14, fontweight='bold')
        capacity_ax.set_facecolor('#1E1E1E')
        self.capacity_canvas = FigureCanvas(capacity_figure)
        left_layout.addWidget(self.capacity_canvas)

        #   Right layout for information and charts
        right_layout = QVBoxLayout()

        # Information labels in a frame
        info_frame = QFrame()
        info_frame.setStyleSheet("QFrame { background-color: #3C3C3C; border-radius: 10px; padding: 10px; }")
        info_layout = QVBoxLayout(info_frame)

        self.total_voltage_label = QLabel("Tổng điện áp: 0 V")
        self.current_label = QLabel("Dòng điện: 0 A")
        self.max_temp_label = QLabel("Nhiệt độ cao nhất: 0 °C")
        self.min_temp_label = QLabel("Nhiệt độ thấp nhất: 0 °C")
        self.status_label = QLabel("Trạng thái: OK")
        self.time_label = QLabel("Thời gian: 0 s")
        self.cycle_count_label = QLabel("Số chu kỳ: 0")
        self.cell_health_label = QLabel("Độ bền pin: OK")

        for label in [self.total_voltage_label, self.current_label, self.max_temp_label,
                  self.min_temp_label, self.status_label, self.time_label, 
                  self.cycle_count_label, self.cell_health_label]:
            label.setStyleSheet("color: white; font-size: 14px;")
            info_layout.addWidget(label)

        right_layout.addWidget(info_frame)

        # Add space between labels and charts
        right_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Create voltage, current, and temperature charts
        time = [0, 1, 2, 3, 4, 5]
        voltage = [3.5, 3.6, 3.7, 3.8, 3.6, 3.5]
        current = [1.0, 1.2, 1.1, 1.3, 1.1, 1.0]
        temperature = [25, 26, 27, 28, 27, 26]

        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)

        # Voltage and current chart
        self.ax1.set_title("Điện áp và Dòng điện", color='white', fontsize=14, fontweight='bold')
        self.ax1.plot(time, voltage, color='cyan', marker='o', markersize=4, label='Điện áp')
        self.ax1.plot(time, current, color='lime', marker='^', markersize=4, label='Dòng điện')
        self.ax1.legend(loc='upper right', fontsize='small', facecolor='black', edgecolor='white')
        self.ax1.set_facecolor('#1E1E1E')

        # Temperature chart
        self.ax2.set_title("Nhiệt độ", color='white', fontsize=14, fontweight='bold')
        self.ax2.plot(time, temperature, color='orange', marker='s', markersize=4, label='Nhiệt độ')
        self.ax2.legend(loc='upper right', fontsize='small', facecolor='black', edgecolor='white')
        self.ax2.set_facecolor('#1E1E1E')
        right_layout.addWidget(self.canvas)

        # Save Data button
        self.save_button = QPushButton("Lưu Dữ Liệu", self)
        self.save_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px; }"
                                   "QPushButton:hover { background-color: #45a049; }")
        self.save_button.clicked.connect(self.save_data)
        right_layout.addWidget(self.save_button)

        # Add left and right layouts to the main layout with stretch factors
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)

        overview_group.setLayout(main_layout)
        return overview_group

    def create_settings_tab(self):
        settings_group = QGroupBox("Thiết lập Hệ thống Pin")
        settings_group.setStyleSheet("QGroupBox { background-color: #2E2E2E; padding: 15px; border-radius: 10px; }")
        
        main_layout = QVBoxLayout()
        
        # Common Font Style
        title_font = QFont("Arial", 10, QFont.Bold)
        label_font = QFont("Arial", 9)
        
        # Basic Settings Group
        basic_settings_group = QGroupBox("Basic Settings")
        basic_settings_group.setFont(title_font)
        basic_settings_layout = QGridLayout()
        basic_settings_group.setStyleSheet("QGroupBox { background-color: #333333; padding: 10px; border-radius: 8px; }")
        
        # Add widgets for Basic Settings
        basic_settings_data = [
            ("Cell Count:", 8),
            ("Battery Capacity(AH):", 50),
            ("Balance Trig. Volt(V):", 0.010),
            ("Calibrating Volt(V):", 33.0),
            ("Balance Max:", 0),
            ("Charge Max:", 150.0)
        ]
        
        for i, (label_text, default_value) in enumerate(basic_settings_data):
            label = QLabel(label_text)
            label.setFont(label_font)
            spin_box = QDoubleSpinBox() if isinstance(default_value, float) else QSpinBox()
            spin_box.setValue(default_value)
            spin_box.setFixedWidth(80)
            ok_button = QPushButton("OK")
            ok_button.setFixedWidth(50)
            basic_settings_layout.addWidget(label, i, 0)
            basic_settings_layout.addWidget(spin_box, i, 1)
            basic_settings_layout.addWidget(ok_button, i, 2)

        basic_settings_group.setLayout(basic_settings_layout)

        # Advanced Settings Group
        advanced_settings_group = QGroupBox("Advanced Settings")
        advanced_settings_group.setFont(title_font)
        advanced_settings_layout = QGridLayout()
        advanced_settings_group.setStyleSheet("QGroupBox { background-color: #333333; padding: 10px; border-radius: 8px; }")

        # Add widgets for Advanced Settings
        advanced_settings_data = [
            ("Start Balance Volt (V):", 3.0),
            ("Max Balance Cur (A):", 1.0),
            ("Cell OVP(V):", 4.200),
            ("SOC - 100% Volt(V):", 4.180),
            ("Cell OVPR (V):", 4.180),
            ("Cell UVPR(V):", 2.850),
            ("SOC - 0% Volt(V):", 2.900),
            ("T°C - BMS:", 90),
            ("T°C - Cell battery:", 65)
        ]
        
        for i, (label_text, default_value) in enumerate(advanced_settings_data):
            label = QLabel(label_text)
            label.setFont(label_font)
            spin_box = QDoubleSpinBox() if isinstance(default_value, float) else QSpinBox()
            spin_box.setValue(default_value)
            spin_box.setFixedWidth(80)
            ok_button = QPushButton("OK")
            ok_button.setFixedWidth(50)
            advanced_settings_layout.addWidget(label, i, 0)
            advanced_settings_layout.addWidget(spin_box, i, 1)
            advanced_settings_layout.addWidget(ok_button, i, 2)

        advanced_settings_group.setLayout(advanced_settings_layout)

        # Add all groups to the main layout
        main_layout.addWidget(basic_settings_group)
        main_layout.addWidget(advanced_settings_group)
        main_layout.addStretch()  # Add spacer for flexibility

        settings_group.setLayout(main_layout)
        return settings_group

    def save_settings(self):
        # Save settings logic
        QMessageBox.information(self, "Thông báo", "Thiết lập đã được lưu!")

    def save_data(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Data File", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if file_name:
            QMessageBox.information(self, "Thông báo", "Dữ liệu đã được lưu!")

    def show_error_message(self, title, message):
        QMessageBox.critical(self, title, message)
    def update_data(self):
    # Mock update data function (replace with actual data reading logic)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.data['time'].append(current_time)
        self.data['voltage'].append(np.random.uniform(3.0, 4.5))
        self.data['current'].append(np.random.uniform(-1.0, 1.0))
        self.data['temperature'].append(np.random.uniform(20, 80))
        self.data['cell_health'].append("Good" if np.random.random() > 0.1 else "Warning")
        self.data['battery_capacity'].append(np.random.uniform(10, 100))
        self.data['cycle_count'].append(len(self.data['time']))
        self.data['soc'].append(np.random.uniform(20, 100))  # State of Charge
        self.data['status_flags'].append("OK" if np.random.random() > 0.1 else "Overheat")

    # Update the table and labels for the latest 10 readings
        for i in range(len(self.data['voltage'])):
            if i < 10:  # Display only the last 10 readings
                self.cell_table.setItem(i, 0, QTableWidgetItem(f"{self.data['time'][i]}"))
                self.cell_table.setItem(i, 1, QTableWidgetItem(f"{self.data['voltage'][i]:.2f} V"))
                self.cell_table.setItem(i, 2, QTableWidgetItem(f"{self.data['current'][i]:.2f} A"))
                self.cell_table.setItem(i, 3, QTableWidgetItem(f"{self.data['temperature'][i]:.2f} °C"))
                self.cell_table.setItem(i, 4, QTableWidgetItem(f"{self.data['cell_health'][i]}"))
                self.cell_table.setItem(i, 5, QTableWidgetItem(f"{self.data['battery_capacity'][i]:.2f} mAh"))
                self.cell_table.setItem(i, 6, QTableWidgetItem(f"{self.data['cycle_count'][i]}"))
                self.cell_table.setItem(i, 7, QTableWidgetItem(f"{self.data['soc'][i]:.2f}%"))
                self.cell_table.setItem(i, 8, QTableWidgetItem(f"{self.data['status_flags'][i]}"))


        # Update labels
        self.total_voltage_label.setText(f"Tổng điện áp: {sum(self.data['voltage'][-10:]):.2f} V")
        self.current_label. setText(f"Dòng điện: {self.data['current'][-1]:.2f} A")
        self.max_temp_label.setText(f"Nhiệt độ cao nhất: {max(self.data['temperature'][-10:]):.2f} °C")
        self.min_temp_label.setText(f"Nhiệt độ thấp nhất: {min(self.data['temperature'][-10:]):.2f} °C")
        self.cycle_count_label.setText(f"Số chu kỳ: {self.data['cycle_count'][-1]}")
        self.cell_health_label.setText(f"Độ bền pin: {self.data['cell_health'][-1]}")
        self.time_label.setText(f"Thời gian: {len(self.data['time'])} s")      
        
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.plot(self.data['time'], self.data['voltage'], label='Voltage', color='blue')
        self.ax.plot(self.data['time'], self.data['current'], label='Current', color='red')
        self.ax.plot(self.data['time'], self.data['temperature'], label='Temperature', color='green')
        self.ax.set_title("Biểu đồ Điện áp, Dòng điện và Nhiệt độ", color='white')
        self.ax.set_xlabel("Thời gian (s)", color='white')
        self.ax.set_ylabel("Giá trị", color='white')
        self.ax.set_facecolor('#1E1E1E')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['top'].set_color('none')
        self.ax.spines['right'].set_color('none')
        self.ax.legend()
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication([])
    window = BMSMonitorUI()
    window.show()
    app.exec_()
