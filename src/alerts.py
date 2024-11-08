# src/alerts.py

class BMSAlerts:
    def __init__(self, voltage_threshold, temp_threshold):
        self.voltage_threshold = voltage_threshold
        self.temp_threshold = temp_threshold

    def check_alerts(self, data):
        alerts = []
        if data['voltage'] > self.voltage_threshold:
            alerts.append("Voltage Exceeds Threshold!")
        if data['temperature'] > self.temp_threshold:
            alerts.append("Temperature Exceeds Threshold!")
        return alerts
