import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
import epics

class EPICSControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EPICS Control GUI")
        self.setGeometry(100, 100, 300, 200)
        
        self.layout = QVBoxLayout()
        
        self.label = QLabel("EPICS Control: Rfa:Info.NIST")
        self.layout.addWidget(self.label)
        
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run)
        self.layout.addWidget(self.run_button)
        
        self.stop_button = QPushButton("Stop All")
        self.stop_button.clicked.connect(self.stop_all)
        self.layout.addWidget(self.stop_button)
        
        self.stop_single_button = QPushButton("Stop")
        self.stop_single_button.clicked.connect(self.stop)
        self.layout.addWidget(self.stop_single_button)
        
        self.setLayout(self.layout)
        
        self.controlscan = epics.PV('Rfa:Info.NIST')
        self.controlscan.add_callback(self.update_label)
    
    def run(self):
        if self.controlscan:
            self.controlscan.put("run")  # Sending "run" command
    
    def stop_all(self):
        if self.controlscan:
            self.controlscan.put("stopall")  # Sending "stopall" command
    
    def stop(self):
        if self.controlscan:
            self.controlscan.put("stop")  # Sending "stop" command
    
    def update_label(self, pvname=None, value=None, **kwargs):
        self.label.setText(f"Status: {value}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EPICSControlApp()
    window.show()
    sys.exit(app.exec_())
