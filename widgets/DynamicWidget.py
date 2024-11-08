from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QApplication
from PyQt5.QtCore import QTimer
import sys

class DynamicWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.label = QLabel("Current Value: 0")
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)

        # Timer to update the label every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_label)
        self.timer.start(1000)  # Update every 1000 ms (1 second)

        self.value = 0

    def update_label(self):
        self.value += 1  # Increment value
        self.label.setText(f"Current Value: {self.value}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DynamicWidget()
    window.show()
    sys.exit(app.exec_())