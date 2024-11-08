# src/graph_handler.py
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

class GraphHandler:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.voltage_data = []

    def update_graph(self, data):
        self.voltage_data.append(data['voltage'])
        if len(self.voltage_data) > 100:  # Giới hạn số điểm để tránh quá tải
            self.voltage_data.pop(0)
        self.ax.clear()
        self.ax.plot(self.voltage_data, color='blue')
        self.ax.set_ylim([3.0, 4.5])  # Ngưỡng hiển thị
        plt.xlabel("Time")
        plt.ylabel("Voltage (V)")
        plt.title("Voltage over Time")

    def start_graph(self):
        ani = FuncAnimation(self.fig, self.update_graph, interval=1000)
        plt.show()
