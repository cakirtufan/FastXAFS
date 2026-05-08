# -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 10:35:58 2023

@author: bamline
"""
import sys
import epics
from epics import PV
import numpy as np
import xraylib
import pyqtgraph as pg
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QSlider,
                             QLabel, QHBoxLayout, QSpinBox, QDoubleSpinBox, QFormLayout)
from PyQt5.QtCore import Qt, QEvent

class SpectraPlotter(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the UI
        self.initUI()
        self.cuall=[]
    def initUI(self):

        # Set up the main window properties
        self.setWindowTitle("Spectra Plotter")
        self.setGeometry(100, 100, 800, 600)

        # Create a central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Set up the layout
        layout = QVBoxLayout()

        # Create the plot widget
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        # Create the element selection slider
        slider_layout = QHBoxLayout()
        self.element_label = QLabel("Element (Z): 1")
        self.element_label2 = QLabel("H")
        
        self.element_slider = QSlider(Qt.Horizontal)
        self.element_slider.setMinimum(1)
        self.element_slider.setMaximum(92)  # Up to uranium
        self.element_slider.valueChanged.connect(self.on_element_changed)
        slider_layout.addWidget(self.element_label)
        slider_layout.addWidget(self.element_label2)
        
        slider_layout.addWidget(self.element_slider)
        layout.addLayout(slider_layout)
        

        # Create ROI controls
        roi_layout = QHBoxLayout()
        self.roi_count_label = QLabel("Number of ROIs:")
        self.roi_count_spinbox = QSpinBox()
        self.roi_count_spinbox.setMinimum(0)
        self.roi_count_spinbox.setMaximum(10)
        self.roi_count_spinbox.valueChanged.connect(self.update_roi_controls)
        roi_layout.addWidget(self.roi_count_label)
        roi_layout.addWidget(self.roi_count_spinbox)
        self.roi_form_layout = QFormLayout()
        roi_layout.addLayout(self.roi_form_layout)
        layout.addLayout(roi_layout)

        # Set the layout to the central widget
        central_widget.setLayout(layout)

        # Create the PVs
        self.pvs = [
            PV("XSP3_4Chan:MCA1:ArrayData", callback=self.on_mca1_updated),
            PV("XSP3_4Chan:MCA2:ArrayData"),
            PV("XSP3_4Chan:MCA3:ArrayData"),
            PV("XSP3_4Chan:MCA4:ArrayData"),
        ]

    def on_element_changed(self, value):
        self.element_label.setText(f"Element (Z): {value}")
        self.update_spectra()

    def on_mca1_updated(self, pvname=None, value=None, char_value=None, **kwargs):
        QApplication.postEvent(self, UpdateSpectraEvent())

    def customEvent(self, event):
        if isinstance(event, UpdateSpectraEvent):
            self.update_spectra()

    def update_spectra(self):
        spectra = [pv.get() for pv in self.pvs]
        total_spectrum = np.sum(spectra, axis=0)
        
        spectra=np.asarray(spectra)
        cu=spectra[:,560:610]
        self.cuall.append(cu.sum())
        print(cu.sum(),np.asarray(self.cuall).max() )

        # Clear and re-plot the data
        self.plot_widget.clear()
        self.plot_widget.plot(total_spectrum)
        LINECOLORS = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
#        for i, spec in enumerate(spectra
        for i, spec in enumerate(spectra):
            self.plot_widget.plot(spec, pen=pg.mkPen(LINECOLORS[i]))

        # Overlay emission lines
        try:
            element_z = self.element_slider.value()
            
            element_symbol = xraylib.AtomicNumberToSymbol(element_z)
            self.element_label2.setText(element_symbol)
            for line in range(xraylib.LB5_LINE + 1,xraylib.KA1_LINE+1 ):
                try:
                    line_energy = xraylib.LineEnergy(element_z, line)
                    if line_energy > 0:
                        if xraylib.RadRate(element_z,line)>0.05:
                        #print(line_energy)
                          self.plot_widget.addLine(x=line_energy*100, pen='r')
                except ValueError:
                    pass
        except:
            pass

        # Overlay ROIs
        for i in range(self.roi_count_spinbox.value()):
            start_spinbox = self.findChild(QDoubleSpinBox, f"roi_start_{i}")
            end_spinbox = self.findChild(QDoubleSpinBox, f"roi_end_{i}")
            if start_spinbox and end_spinbox:
                start_val = start_spinbox.value()
                end_val = end_spinbox.value()
                self.plot_widget.addLine(x=start_val, pen='y')
                self.plot_widget.addLine(x=end_val, pen='y')

    def update_roi_controls(self):
        roi_count = self.roi_count_spinbox.value()

        # Remove all existing controls
        for i in range(self.roi_form_layout.rowCount()):
            self.roi_form_layout.removeRow(0)

        # Add new controls
        for i in range(roi_count):
            start_spinbox = QDoubleSpinBox()
            start_spinbox.setObjectName(f"roi_start_{i}")
            start_spinbox.setDecimals(2)
            start_spinbox.setSingleStep(0.01)
            start_spinbox.setRange(0, 10000)  # Assuming energy range is up to 10,000 eV
            start_spinbox.valueChanged.connect(self.update_spectra)

            end_spinbox = QDoubleSpinBox()
            end_spinbox.setObjectName(f"roi_end_{i}")
            end_spinbox.setDecimals(2)
            end_spinbox.setSingleStep(0.01)
            end_spinbox.setRange(0, 10000)  # Assuming energy range is up to 10,000 eV
            end_spinbox.valueChanged.connect(self.update_spectra)

            self.roi_form_layout.addRow(f"ROI {i+1} Start (eV):", start_spinbox)
            self.roi_form_layout.addRow(f"ROI {i+1} End (eV):", end_spinbox)

class UpdateSpectraEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self):
        super().__init__(UpdateSpectraEvent.EVENT_TYPE)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    plotter = SpectraPlotter()
    plotter.show()
    sys.exit(app.exec_())
                                 
