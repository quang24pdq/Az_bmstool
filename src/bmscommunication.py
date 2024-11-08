from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import struct

class BMSCommunication:
    def __init__(self, port, baudrate=9600):
        self.client = ModbusClient(method='rtu', port=port, baudrate=baudrate, timeout=1)
        
    def connect(self):
        if not self.client.connect():
            print("Failed to connect to BMS")
            return False
        return True

    def read_input_registers(self, start_address, quantity):
        response = self.client.read_input_registers(start_address, quantity)
        if response.isError():
            print(f"Error reading registers: {response}")
            return None
        return response.registers

    def disconnect(self):
        self.client.close()

if __name__ == "__main__":
    # Ví dụ sử dụng
    bms = BMSCommunication(port='COM3', baudrate=9600)
    if bms.connect():
        start_address = 0x0000  # Địa chỉ bắt đầu
        quantity = 10  # Số lượng thanh ghi cần đọc
        registers = bms.read_input_registers(start_address, quantity)
        if registers:
            for i, reg in enumerate(registers):
                print(f"Register {start_address + i}: {reg}")
        bms.disconnect()
