import time
import serial  # Giả sử dùng PySerial để giao tiếp với thiết bị

# Kết nối với cổng nối tiếp
ser = serial.Serial('COM1', baudrate=9600, timeout=0.5)

START_FRAME = 0x02
END_FRAME = 0x03

# Hàm để tính toán độ dài frame
def calculate_length(data_length):
    return 1 + data_length + 1  # Command word (1 byte) + Data + End frame

# Hàm tạo và gửi request frame, sau đó nhận và kiểm tra response frame
def send_and_receive_frame(command, data):
    # Tạo frame request
    length = calculate_length(len(data))
    frame = bytearray([START_FRAME, length, command] + list(data) + [END_FRAME])

    # Gửi frame request
    ser.write(frame)
    print(f"Đã gửi frame: {frame.hex()}")

    # Nhận và xử lý frame response
    start_time = time.time()
    response_frame = bytearray()

    while (time.time() - start_time) < 0.5:  # Kiểm tra timeout 0.5ms
        if ser.in_waiting > 0:
            byte = ser.read(1)
            response_frame.append(int.from_bytes(byte, "big"))

            # Kiểm tra Start Frame
            if len(response_frame) == 1 and response_frame[0] != START_FRAME:
                response_frame.clear()  # Bỏ frame nếu không có byte bắt đầu hợp lệ

            # Kiểm tra End Frame
            if len(response_frame) >= 3 and response_frame[-1] == END_FRAME:
                if response_frame[1] == len(response_frame) - 2:
                    print(f"Frame hợp lệ nhận được: {response_frame.hex()}")

                    # Kiểm tra lỗi
                    if response_frame[2] & 0x80:  # Kiểm tra bit cao nhất của Command Word
                        error_code = response_frame[3]
                        print(f"Frame lỗi nhận được với mã lỗi: {error_code}")
                        return None  # Kết thúc hàm nếu có lỗi

                    # Trả về response nếu không có lỗi
                    return response_frame
                else:
                    print("Lỗi độ dài frame không hợp lệ.")
                    return None

    print("Timeout: Frame không hoàn thành.")
    return None

# Ví dụ sử dụng
command = 0x01  # Lệnh ví dụ
data = [0x10, 0x20, 0x30]  # Dữ liệu ví dụ

response_frame = send_and_receive_frame(command, data)
if response_frame:
    print("Phản hồi nhận được:", response_frame.hex())
else:
    print("Không nhận được phản hồi hợp lệ.")
