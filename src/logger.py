# src/logger.py
import pandas as pd
from datetime import datetime

class Logger:
    def __init__(self):
        self.data = []

    def log(self, data):
        self.data.append(data)
        if len(self.data) >= 10:  # Ghi log sau mỗi 10 điểm dữ liệu
            df = pd.DataFrame(self.data)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            df.to_csv(f"data/logs/log_{timestamp}.csv", index=False)
            self.data = []  # Xóa dữ liệu sau khi ghi
