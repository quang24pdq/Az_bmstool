# src/data_handler.py
import serial

class DataHandler:
    def __init__(self, port, baud_rate):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            print("Kết nối thành công.")
        except serial.SerialException as e:
            print("Không thể kết nối:", e)

    def get_data(self):
        if self.ser and self.ser.is_open:
            line = self.ser.readline().decode().strip()
            # Xử lý dòng dữ liệu
            return line
        else:
            print("Chưa kết nối!")
