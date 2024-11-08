import time
import serial
from PyQt5.QtWidgets import QApplication, QMessageBox, QTableWidgetItem
from sympy import python
from ui import BMSMonitorUI
from graph_handler import GraphHandler
from alerts import BMSAlerts
from logger import Logger
import sys

START_FRAME = 0x02
END_FRAME = 0x03
ser = None  # Biến toàn cục để lưu trữ kết nối serial

def main():
    app = QApplication(sys.argv)

    # Khởi tạo giao diện
    window = BMSMonitorUI()
    
    # Khởi tạo các thành phần khác
    graph_handler = GraphHandler()
    alerts = BMSAlerts(voltage_threshold=4.2, temp_threshold=40)
    logger = Logger()
    
    # Kết nối BMS khi nút "Kết nối" được nhấn
    window.connect_button.clicked.connect(lambda: connect_bms(window, alerts, logger))
    window.disconnect_button.clicked.connect(lambda: disconnect_bms(window))  # Thêm nút ngắt kết nối

    window.show()
    sys.exit(app.exec_())

def connect_bms(window, alerts, logger):
    global ser  # Sử dụng biến toàn cục
    port = window.port_select.currentText()
    baud_rate = int(window.baud_rate_select.currentText())
    
    try:
        ser = serial.Serial(port, baudrate=baud_rate, timeout=0.5)
        window.status_label.setText("Đã kết nối tới BMS.")
        read_bms_data(window, alerts, logger)  # Gọi hàm để đọc dữ liệu từ BMS

    except serial.SerialException as e:
        show_error_message("Lỗi Kết nối", f"Có lỗi xảy ra khi kết nối tới BMS: {str(e)}", window)
    except Exception as e:
        show_error_message("Lỗi", f"Có lỗi xảy ra: {str(e)}", window)

def disconnect_bms(window):
    global ser
    if ser and ser.is_open:
        ser.close()
        window.status_label.setText("Đã ngắt kết nối khỏi BMS.")
    else:
        show_error_message("Lỗi", "Không có kết nối nào để ngắt.", window)

def read_bms_data(window, alerts, logger):
    global ser
    if ser and ser.is_open:
        start_address = 0x0000  # Địa chỉ bắt đầu
        quantity = 10  # Số lượng thanh ghi cần đọc
        command = 0x03  # Giả định đây là mã lệnh để đọc dữ liệu BMS
        data = [start_address >> 8, start_address & 0xFF, quantity >> 8, quantity & 0xFF]  # Dữ liệu yêu cầu
        response_frame = send_and_receive_frame(ser, command, data)

        if response_frame:
            data = parse_bms_data(response_frame)  # Giải mã dữ liệu từ phản hồi thành dictionary
            logger.log(data)
            update_ui_with_data(window, data, alerts)
        else:
            show_error_message("Lỗi Kết nối", "Không thể nhận dữ liệu từ BMS.", window)

def send_and_receive_frame(ser, command, data):
    # Tạo frame request và gửi
    frame = create_request_frame(command, data) # type: ignore
    ser.write(frame)
    print(f"Đã gửi frame: {frame.hex()}")

    # Nhận và xử lý frame response
    start_time = time.time()
    response_frame = bytearray()

    while (time.time() - start_time) < 0.5: 
        if ser.in_waiting > 0:
            byte = ser.read(1)
            response_frame.append(int.from_bytes(byte, "big"))

            if len(response_frame ) == 1 and response_frame[0] != START_FRAME:
                response_frame.clear()
            if len(response_frame) >= 3 and response_frame[-1] == END_FRAME:
                if response_frame[1] == len(response_frame) - 2:
                    print(f"Frame hợp lệ nhận được: {response_frame.hex()}")
                    return response_frame
                else:
                    print("Lỗi độ dài frame không hợp lệ.")
                    return None

    print("Timeout: Frame không hoàn thành.")
    return None

def show_error_message(title, message, parent):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setText(message)
    msg_box.setWindowTitle(title)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()

def parse_bms_data(response_frame):
    # Giải mã dữ liệu từ response_frame
    data = {
        "voltage": (response_frame[3] << 8 | response_frame[4]) / 1000,  # Giả định đơn vị 10mV
        "current": (response_frame[5] << 8 | response_frame[6]) / 100,  # Giả định đơn vị 10mA
        "max_temp": response_frame[7],
        "min_temp": response_frame[8],
        "cycle_count": response_frame[9],
        "cell_health": "Tốt" if response_frame[10] else "Kém",
        "battery_capacity": response_frame[11] * 100,  # Giả định dung lượng
        "cells": [
            {
                "voltage": response_frame[i],
                "current": response_frame[i + 1],
                "temperature": response_frame[i + 2],
                "soc": response_frame[i + 3]
            }
            for i in range(12, len(response_frame), 4)
        ]
    }
    return data

def update_ui_with_data(window, data, alerts):
    if data:
        window.total_voltage_label.setText(f"Tổng điện áp: {data.get('voltage', 0)} V")
        window.current_label.setText(f"Dòng điện: {data.get('current', 0)} A")
        window.max_temp_label.setText(f"Nhiệt độ cao nhất: {data.get('max_temp', 0)} °C")
        window.min_temp_label.setText(f"Nhiệt độ thấp nhất: {data.get('min_temp', 0)} °C")
        window.cycle_count_label.setText(f"Số chu kỳ: {data.get('cycle_count', 0)}")
        window.cell_health_label.setText(f"Độ bền pin: {data.get('cell_health', 'Không xác định')}")
        window.battery_capacity_label.setText(f"Dung lượng pin: {data.get('battery_capacity', 0)} mAh")

        # Cập nhật dữ liệu cho từng cell
        for i, cell_data in enumerate(data.get('cells', [])):
            if i < window.cell_table.rowCount():
                window.cell_table.setItem(i, 0, QTableWidgetItem(f"{cell_data['voltage']} V"))
                window.cell_table.setItem(i, 1, QTableWidgetItem(f"{cell_data['current']} A"))
                window.cell_table.setItem(i, 2, QTableWidgetItem(f"{cell_data['temperature']} °C"))
                window.cell_table.setItem(i, 3, QTableWidgetItem(cell_data.get('status', 'OK')))
                window.cell_table.setItem(i, 4, QTableWidgetItem(f"{cell_data['soc']}%"))

if __name__ == "__main__":
    main() 