import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout
import xraylib

class XrayEdgeSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_element = None
        self.selected_edge = None
        self.edge_energy = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("X-ray Edge Energy Selector")

        # Main layout
        layout = QVBoxLayout()

        # ComboBox for element selection
        element_layout = QHBoxLayout()
        element_label = QLabel("Select Element:")
        self.element_combo = QComboBox(self)
        self.populate_element_combo()
        self.element_combo.currentIndexChanged.connect(self.update_edge_energy)
        element_layout.addWidget(element_label)
        element_layout.addWidget(self.element_combo)
        layout.addLayout(element_layout)

        # ComboBox for edge selection
        edge_layout = QHBoxLayout()
        edge_label = QLabel("Select X-ray Edge:")
        self.edge_combo = QComboBox(self)
        self.populate_edge_combo()
        self.edge_combo.currentIndexChanged.connect(self.update_edge_energy)
        edge_layout.addWidget(edge_label)
        edge_layout.addWidget(self.edge_combo)
        layout.addLayout(edge_layout)

        # Label to show edge energy
        self.edge_energy_label = QLabel("Edge Energy: N/A", self)
        layout.addWidget(self.edge_energy_label)

        # Set the layout to the widget
        self.setLayout(layout)
        

    def populate_element_combo(self):
        # Populate ComboBox with element names
        self.element_names = [xraylib.AtomicNumberToSymbol(i) for i in range(1, 101)]  # First 100 elements
        self.element_combo.addItems(self.element_names)
        
        
    def populate_edge_combo(self):
        # Populate ComboBox with edge names
        self.edge_names = {
            'K': xraylib.K_SHELL,
            'L1': xraylib.L1_SHELL,
            'L2': xraylib.L2_SHELL,
            'L3': xraylib.L3_SHELL,
            'M1': xraylib.M1_SHELL,
            'M2': xraylib.M2_SHELL,
            'M3': xraylib.M3_SHELL,
            'M4': xraylib.M4_SHELL,
            'M5': xraylib.M5_SHELL,
        }
        self.edge_combo.addItems(self.edge_names.keys())
        

    def update_edge_energy(self):
        # Get the selected element and edge
        self.selected_element = self.element_combo.currentText()
        self.selected_edge = self.edge_combo.currentText()

        # Get atomic number from element symbol
        atomic_number = xraylib.SymbolToAtomicNumber(self.selected_element)

        # Get the shell value (edge) using xraylib
        edge_value = self.edge_names[self.selected_edge]

        try:
            # Calculate the edge energy
            self.edge_energy = xraylib.EdgeEnergy(atomic_number, edge_value)
            self.edge_energy_label.setText(f"Edge Energy: {self.edge_energy:.2f} keV")
        except ValueError:
            # If the edge energy doesn't exist for the selected element (e.g., no L1 for H)
            self.edge_energy_label.setText("Edge Energy: N/A")
            self.edge_energy = None

    # Getter methods
    def get_selected_element(self):
        return self.selected_element

    def get_selected_edge(self):
        return self.selected_edge

    def get_edge_energy(self):
        return self.edge_energy
