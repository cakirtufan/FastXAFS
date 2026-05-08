# -*- coding: utf-8 -*-
"""
Created on Wed May  7 19:24:02 2025

@author: bamline
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 11:02:30 2025

@author: bamline
"""


import sys
import os
import time
import math
import numpy as np
import matplotlib.pyplot as plt

import epics
import motorlist as ml
from XrayEdgeSelector import XrayEdgeSelector
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget
from PyQt5.QtWidgets import QCheckBox, QTableWidget, QTableWidgetItem, QPushButton,QFrame
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox
from PyQt5 import QtGui

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import checkpitchbayes as checkpitch
#import checkpitch_adam as checkpitch
from datetime import datetime
import csv
 
controlscan=epics.PV('Rfa:Info.NIST')

D_SPACING = 0.31355  # Angstrom

filterpos = {
    "V K": 11,
    "V_K": 11,
    
    "Cr_K": 14,
   "Cr K": 14,
   
   "Mn_K": 20,
   "Mn K": 20,
   
    "Fe K": 7,
    "Fe_K": 7,
    
    "Co_K": 2,
    "Co K": 2,
   
    "Ni_K": 9,
    "Ni K": 9,
    
    "Cu_K": 5,
    "Cu K": 5,
    
    "Zn_K": 18,
    "Zn K": 18,
    
    "Se_K": 8,
    "Se K": 8
     
}


def add_constant_if_decreasing(a, c):
    # Convert a to a NumPy array in case it's a list
    a = np.array(a)
    
    # Loop through the array, starting from the second element
    for i in range(1, len(a)):
        # Check if the current element is less than the previous one
        if a[i] < a[i - 1]:
            # Add constant c to all subsequent elements
            a[i:] += c
            print('Offset Corrected')
           # break  # Stop after the first adjustment, if needed
    return(a)

# Conversion functions
def angle_to_energy(angles):
    angles_rad = np.radians(angles)
    wavelengths = 2 * D_SPACING * np.sin(angles_rad)
    energies = 1.239843 / wavelengths  # keV
    return energies

def energy_to_angle(energy):
    wavelength = 1.239843 / energy
    sin_theta = wavelength / (2 * D_SPACING)
    if sin_theta > 1 or sin_theta < -1:
        raise ValueError("Energy is too high/low to result in a valid angle.")
    angle_rad = math.asin(sin_theta)
    angle_deg = math.degrees(angle_rad)
    return angle_deg

# The main GUI window class
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()
    def initUI(self):
        self.setWindowTitle("XANES/EXAFS Acquisition GUI")
        
        # Main container layout
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()  # Left column layout for input fields and buttons
        right_layout = QVBoxLayout()  # Right column layout for the plot area and table
    
        # Energy input fields
        energy_layout = QGridLayout()  # Using grid layout for aligned labels and inputs
    
        self.start_energy_label = QtWidgets.QLabel("Start Energy (keV):")
        self.start_energy_input = QtWidgets.QLineEdit("8")
        energy_layout.addWidget(self.start_energy_label, 0, 0)
        energy_layout.addWidget(self.start_energy_input, 0, 1)
    
        self.stop_energy_label = QtWidgets.QLabel("Stop Energy (keV):")
        self.stop_energy_input = QtWidgets.QLineEdit("9")
        energy_layout.addWidget(self.stop_energy_label, 1, 0)
        energy_layout.addWidget(self.stop_energy_input, 1, 1)
    
        # Number of points
        self.npoints_label = QtWidgets.QLabel("Number of Points:")
        self.npoints_input = QtWidgets.QLineEdit("2000")
        energy_layout.addWidget(self.npoints_label, 2, 0)
        energy_layout.addWidget(self.npoints_input, 2, 1)
    
        # Acquisition time field
        self.velo_label = QtWidgets.QLabel("Time:")
        self.velo_input = QtWidgets.QLineEdit("10")
        energy_layout.addWidget(self.velo_label, 3, 0)
        energy_layout.addWidget(self.velo_input, 3, 1)
    
        left_layout.addLayout(energy_layout)
    
        # Start and Save buttons
        self.start_button = QtWidgets.QPushButton("Start Acquisition")
        self.file_button = QtWidgets.QPushButton("Save Data")
        left_layout.addWidget(self.start_button)
        left_layout.addWidget(self.file_button)

        self.mode_dropdown = QComboBox()
        self.mode_dropdown.addItems(["XANES", "EXAFS"])

    
        # Connect button actions
        self.start_button.clicked.connect(self.start_acquisition)
        self.file_button.clicked.connect(self.save_data)
    
    
        self.savetable = QtWidgets.QPushButton("Save Table")
        self.loadtable = QtWidgets.QPushButton("Load Table")
        left_layout.addWidget(self.savetable)
        left_layout.addWidget(self.loadtable) 
       # Connect button actions
        self.savetable.clicked.connect(self.save_table_content)
        self.loadtable.clicked.connect(self.load_table_content)
   
 
        # Plot area and toolbar
        self.plot_widget = QWidget(self)
        self.plot_layout = QVBoxLayout(self.plot_widget)
    
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
    
        self.plot_layout.addWidget(self.toolbar)
        self.plot_layout.addWidget(self.canvas)
    
        
        # Sample Table
        self.sample_table = QTableWidget(self)
        self.sample_table.setRowCount(0)
        self.sample_table.setColumnCount(9)
        self.sample_table.setHorizontalHeaderLabels(["Sample_Name", "X", "Y", "Edge", "Time", "N-Points","Element", "Mode", "Repeat"])
        self.sample_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sample_table.setSelectionMode(QTableWidget.SingleSelection)
        self.sample_table.setFixedSize(1200, 500)
        self.sample_table.cellDoubleClicked.connect(self.cell_double_clicked)
        
        
    
        right_layout.addWidget(self.sample_table)
        self.xray_edge_selector = XrayEdgeSelector()
        right_layout.addWidget(self.xray_edge_selector)
    
        self.add_sample_btn = QPushButton('Add Sample Position', self)
        left_layout.addWidget(self.add_sample_btn)
        self.add_sample_btn.clicked.connect(self.add_sample_position)
       
        self.remove_sample_btn = QPushButton('Remove Sample Position', self)
        left_layout.addWidget(self.remove_sample_btn)
        self.remove_sample_btn.clicked.connect(self.remove_sample_position)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)  # Set the frame shape to Horizontal Line
        line.setFrameShadow(QFrame.Sunken)  # Add a shadow to make it appear sunken
        left_layout.addWidget(line)
        left_layout2 = QGridLayout()
        self.start_all_btn = QPushButton('Start All Measurement', self)
        left_layout2.addWidget(self.start_all_btn,0,0) 
        
        self.start_all_btn.clicked.connect(self.start_all)
        
        self.repeat_label = QtWidgets.QLabel("Repeat:")
        self.repeat_input = QtWidgets.QLineEdit("1")
        left_layout2.addWidget(self.repeat_label,1,0)
        left_layout2.addWidget(self.repeat_input,1,1)
        
        self.check_pitch_cb = QCheckBox('Check Pitch', self)
        self.check_pitch_cb.setChecked(False)
        left_layout2.addWidget(self.check_pitch_cb,2,0)
        
        self.bothdir_cb = QCheckBox('Both Directions', self)
        self.bothdir_cb.setChecked(False)
        left_layout2.addWidget(self.bothdir_cb,2,1)
        
        self.with_xrf = QCheckBox('With XRF', self)
        self.with_xrf.setChecked(False)
        left_layout2.addWidget(self.with_xrf,3,0)
        
         
        
        left_layout.addLayout(left_layout2)     
        self.get_path = QtWidgets.QPushButton("Directory")
        self.get_path.clicked.connect(self.get_directory)
    
    
    
        left_layout.addWidget(self.get_path)


        self.path = QtWidgets.QLineEdit(r"E:\ContXANES")
        left_layout.addWidget(self.path)
        # Add left and right layouts to the main layout
        main_layout.addLayout(left_layout)
    
        main_layout.addLayout(right_layout)
        main_layout.addWidget(self.plot_widget)
    
        # Set the main layout as the layout for the central widget
        central_widget = QWidget(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
        self.show()
        self.xray_edge_selector.element_combo.setCurrentIndex(24)
        
        
    def save_table_content(self, file_name='table.csv'):
        with open(file_name, 'w', newline='') as file:
            writer = csv.writer(file)
            # Write headers
            headers = [self.sample_table.horizontalHeaderItem(i).text() for i in range(self.sample_table.columnCount())]
            writer.writerow(headers)
            
            # Write table contents
            for row in range(self.sample_table.rowCount()):
                row_data = []
                for column in range(self.sample_table.columnCount()):
                    item = self.sample_table.item(row, column)
                    row_data.append(item.text() if item else "")
                writer.writerow(row_data)

    def load_table_content(self, file_name='table.csv'):
        if not os.path.exists(file_name):
            print(f"Table file not found: {file_name}")
            return

        with open(file_name, 'r') as file:
            reader = csv.reader(file)
            try:
                headers = next(reader)
            except StopIteration:
                print(f"Table file is empty: {file_name}")
                return

            self.sample_table.setColumnCount(len(headers))
            self.sample_table.setHorizontalHeaderLabels(headers)
            self.sample_table.setRowCount(0)  # Clear any existing data
            
            for row_data in reader:
                row = self.sample_table.rowCount()
                self.sample_table.insertRow(row)
                for column, data in enumerate(row_data):
                    self.sample_table.setItem(row, column, QTableWidgetItem(data))


    def get_directory(self):
        # Create a QWidget to host the dialog (it can be hidden)
        widget = QWidget()
        widget.setWindowTitle("Select Directory")
    
        # Open the QFileDialog to get the existing directory
        directory = QFileDialog.getExistingDirectory(
            widget,
            "Select Directory",  # Dialog title
            "",  # Default directory (empty string means the home directory)
            QFileDialog.ShowDirsOnly  # Show only directories, no files
        )

    # Return the selected directory path as a string
        self.path.setText(directory)
        
    def get_table_headers(self):
        headers = []
        for column in range(self.sample_table.columnCount()):
            header_item = self.sample_table.horizontalHeaderItem(column)
            if header_item is not None:
                headers.append(header_item.text())
        return headers
        
    def get_row_values(self,sample_table, row):
    # Create a list to store the values from the row
        row_values = []
    
        # Loop through each column in the specified row
        for column in range(self.sample_table.columnCount()):
            item = self.sample_table.item(row, column)
            if item is not None:
                row_values.append(item.text())  # Add the text of the item to the list
            else:
                row_values.append('')  # If no item exists in the cell, append an empty string
    
        return row_values
    def add_sample_position(self):
            row_count = self.sample_table.rowCount()
            self.sample_table.setRowCount(row_count + 1)

            sample_name = "Sample " + str(row_count + 1)
            x = ml.XANES_X.get_position()
            y = ml.XANES_Y.get_position()
             

            self.sample_table.setItem(row_count, 0, QTableWidgetItem(sample_name))
            self.sample_table.setItem(row_count, 1, QTableWidgetItem(str(x)))
            self.sample_table.setItem(row_count, 2, QTableWidgetItem(str(y)))

            self.sample_table.setItem(row_count, 4, QTableWidgetItem(str(30)))
            self.sample_table.setItem(row_count, 5, QTableWidgetItem(str(2000)))
             
            selected_element = self.xray_edge_selector.get_selected_element()
            selected_edge = self.xray_edge_selector.get_selected_edge()
            edge_energy = self.xray_edge_selector.get_edge_energy()
            self.sample_table.setItem(row_count, 3, QTableWidgetItem(str(edge_energy)))
            self.sample_table.setItem(row_count, 6, QTableWidgetItem(selected_element+'_'+selected_edge))
  
            self.sample_table.setItem(row_count, 7, QTableWidgetItem(str(1)))
            self.sample_table.setItem(row_count, 8, QTableWidgetItem(str(1)))
            
    def remove_sample_position(self):
            selected_rows = self.sample_table.selectionModel().selectedRows()
            for index in selected_rows:
                self.sample_table.removeRow(index.row())
            self.sample_table.clearSelection()
    def cell_double_clicked(self, row, column):
        if column == 6:  # Check if the double-clicked cell is in the "Input File" column
            selected_element = self.xray_edge_selector.get_selected_element()
            selected_edge = self.xray_edge_selector.get_selected_edge()
            edge_energy = self.xray_edge_selector.get_edge_energy()
            self.sample_table.setItem(row, 3, QTableWidgetItem(str(edge_energy)))
            self.sample_table.setItem(row, 6, QTableWidgetItem(selected_element+' '+selected_edge))
    
    
    def start_acquisition(self):
        start_energy = float(self.start_energy_input.text())
        stop_energy = float(self.stop_energy_input.text())
        npoints = int(self.npoints_input.text())
        thetagatestart = energy_to_angle(start_energy)
        thetagatestop = energy_to_angle(stop_energy)
        thetadelta = thetagatestart - thetagatestop
        

        
        
        velneu=thetadelta/float(self.velo_input.text())
        print('velneu2',velneu)
        
        self.run_acquisition(thetagatestart,thetagatestop,thetadelta,npoints,velneu)
    
    
    def start_all(self):
        
        controlscan.value='Started'
        nrepeat=int(self.repeat_input.text())
        for i in range(nrepeat):
            
            for row in range(self.sample_table.rowCount()):
                self.sample_table.selectRow(row)
                
                # Optionally change the background color to indicate it's active
                for column in range(self.sample_table.columnCount()):
                    item = self.sample_table.item(row, column)
                    if item:
                        item.setBackground(QtGui.QColor(255, 255, 150))  # light yellow
                        QtWidgets.QApplication.processEvents()
                if controlscan.value in('stop','stopall'):
    
                    break
                
                mode = self.sample_table.item(row, 7).text()
                
                repeat = int(self.sample_table.item(row, 8).text())
                
                for s in range(repeat):
                
                    sample_name = self.sample_table.item(row, 0).text()
                    self.actualname=sample_name
                    x_position = self.sample_table.item(row, 1).text()
                    y_position = self.sample_table.item(row, 2).text()
                    edgename = self.sample_table.item(row, 6).text()
                    
                    if mode == "1":
                        
                    
                        start_energy = float(self.sample_table.item(row, 3).text()) - 0.3
         
                        stop_energy = float(self.sample_table.item(row, 3).text()) + 0.4
                    
                    else:
                        # it was 0.15 to 0.85
                        start_energy = float(self.sample_table.item(row, 3).text()) - 0.25
         
                        stop_energy = float(self.sample_table.item(row, 3).text()) + 0.75
                    
                    epics.caput("Energ:25002000selectMotors",1)
                    ml.DCM_THETA.VELO = 0.2  
                    ml.DCM_ENERGY.move(start_energy+0.2)
                    
                    ml.XANES_X.move(x_position)
                    ml.XANES_Y.move(y_position)
                    print(edgename)
                    refpos=(filterpos.get(edgename,16))
                    ml.XANES_Reference.move(refpos)
                    ml.XANES_X.move(x_position,wait=True)
                    ml.XANES_Y.move(y_position,wait=True)
                    ml.XANES_Reference.move(refpos,wait=True)
                    
                    while not (epics.caget('Energ:25002000dmov')) :
                        time.sleep(0.1)
                     
                        
                     
                        
                  #  ml.DCM_ENERGY.move(start_energy+0.2,wait=True)
                    
                    
                    realtheta=ml.DCM_THETA.get_position()
                    epics.caput("BAMZEBRA:M2:ERES",0.0000037464974)
                    time.sleep(0.1)
                    epics.caput("BAMZEBRA:POS2_SET",realtheta)
                    time.sleep(.1)
                    if self.check_pitch_cb.isChecked():checkpitch.checkpitch()
                  #  if self.check_pitch_cb.isChecked():checkpitch.physics_informed_pitch_optimization()
                    npoints = int(self.sample_table.item(row, 5).text())
                    thetagatestart = energy_to_angle(start_energy)
                    thetagatestop = energy_to_angle(stop_energy)
                    thetadelta = thetagatestart - thetagatestop
                    velneu=thetadelta/float( self.sample_table.item(row, 4).text())    
                    print('velneu1',velneu,thetadelta , thetagatestart ,thetagatestop)
                    
                    self.run_acquisition(thetagatestart,thetagatestop,thetadelta,npoints,velneu,direction=1)
                    row_values = self.get_row_values(self.sample_table, row)
                    print(row_values)
                    header=self.get_table_headers()
                    unique= datetime.now().strftime("%Y%m%d%H%M%S")
                    file_path=self.path.text()+'/'+sample_name+'_'+str(i)+'_'+str(s)+'_'+unique+'.csv'
                    if file_path:
                        with open(file_path, "w") as file_object:
                            file_object.write('#'+ ' '.join(header)+'\n' )
                            file_object.write('#'+ ' '.join(row_values)+'\n' )
                            file_object.write('Ene I0 I1 I2 ENC\n')
                  #          
                            for a, b, c, d,e in zip(self.ene, self.i0, self.i1, self.i2,self.encpos):
                                file_object.write(f"{a} {b} {c} {d} {e}\n")
    
                        print("Data saved to:", file_path)
                    if self.bothdir_cb.isChecked():
                        self.run_acquisition(thetagatestop,thetagatestart,thetadelta,npoints,velneu,direction=0)
                        row_values = self.get_row_values(self.sample_table, row)
                        print(row_values)
                        header=self.get_table_headers()
                        unique= datetime.now().strftime("%Y%m%d%H%M%S")
                        file_path=self.path.text()+'/'+sample_name+'_'+str(i)+'_back_'+unique+'.csv'
                        if file_path:
                            with open(file_path, "w") as file_object:
                                file_object.write('#'+ ' '.join(header)+'\n' )
                                file_object.write('#'+ ' '.join(row_values)+'\n' )
                                file_object.write('Ene I0 I1 I2 ENC\n')
                      #          
                                for a, b, c, d,e in zip(self.ene, self.i0, self.i1, self.i2,self.encpos):
                                    file_object.write(f"{a} {b} {c} {d} {e}\n")
            
                            print("Data saved to:", file_path)
            # Optional: Reset background color after the scan
                    for column in range(self.sample_table.columnCount()):
                        item = self.sample_table.item(row, column)
                        if item:
                            item.setBackground(QtGui.QColor(255, 55, 255))  # white
                            QtWidgets.QApplication.processEvents()    


        controlscan.value='Finished'
    
    
    def run_acquisition(self,thetagatestart,thetagatestop,thetadelta,npoints,velneu,direction=1):
        
        if self.with_xrf.isChecked():
#            base = "/mnt/raid-triglav/RFA-xspress3/"
 #           folder = os.path.basename(self.path.text())

  #          full_path = os.path.join(base, folder).replace("\\", "/")
          
   #         print("XSP3 FilePath:", full_path)

    #        epics.caput('XSP3_4Chan:HDF1:FilePath', full_path + "/")


            epics.caput('XSP3_4Chan:HDF1:FilePath',"/mnt/raid-triglav/RFA-xspress3/2026KW19/Tomek")
            
            unique= datetime.now().strftime("%Y%m%d%H%M%S")
            epics.caput('XSP3_4Chan:HDF1:Capture',0)    
            epics.caput('XSP3_4Chan:det1:Acquire',0) 
            
            epics.caput('XSP3_4Chan:det1:NumImages',npoints) 
            
            
            epics.caput('XSP3_4Chan:det1:ERASE',1)
            epics.caput('XSP3_4Chan:det1:UPDATE',1) 
            epics.caput('XSP3_4Chan:HDF1:FileName', self.actualname+unique)
            epics.caput('XSP3_4Chan:det1:TriggerMode',3)   
            epics.caput('XSP3_4Chan:det1:Acquire', 1)
            epics.caput('XSP3_4Chan:HDF1:Capture',1)
        
        # Get user input
        
        epics.caput('BAMZEBRA:PC_DIR', direction)

        # Calculate initial values
        thetadeltastep = thetadelta / npoints 
        epics.caput('BAMZEBRA:PC_GATE_START', thetagatestart)


        epics.caput('BAMZEBRA:PC_GATE_WID', thetadelta + 0.1)
        epics.caput('BAMZEBRA:PC_GATE_STEP', thetadelta + 0.2)
        epics.caput('BAMZEBRA:PC_GATE_NGATE', 1)

#        ypulsewid = 0.0094
#        ygatedeltastep = 0.0113
#        ypulseanzahl = 100.0
#        ygatewid = ypulseanzahl * (ypulsewid + ygatedeltastep)

        epics.caput('BAMZEBRA:PC_PULSE_START', 0)
        epics.caput('BAMZEBRA:PC_PULSE_STEP', thetadeltastep)
        epics.caput('BAMZEBRA:PC_PULSE_WID', thetadeltastep * 0.9)
        epics.caput('BAMZEBRA:PC_PULSE_MAX', npoints)

        time.sleep(1)

        dcmstart = thetagatestart
        dcmstop = thetagatestop

        ml.DCM_THETA.VELO = 0.2 
        print('Move to Start with 0.2')
        if direction:
            ml.DCM_THETA.move(dcmstart + 0.03, wait=True)
        else :
            ml.DCM_THETA.move(dcmstart - 0.03, wait=True)
        print('Reached ',dcmstart,'+-0.1')
        time.sleep(0.2)
        epics.caput("BAMZEBRA:SYS_RESET.PROC", 1)
        epics.caput('BAMZEBRA:PC_ARM', 1)
    #    velneu=thetadelta/float(self.velo_input.text())
        ml.DCM_THETA.VELO = min(velneu,0.2)
        ml.DCM_THETA.BVEL = min(velneu,0.2)
        print('move to ',dcmstop,'-+0.1 with',velneu)
        if direction:
            ml.DCM_THETA.move(dcmstop - 0.02, wait=True)
        else:
            ml.DCM_THETA.move(dcmstop + 0.02, wait=True)
        print('Reached ',dcmstop,'-+0.1')


        time.sleep(2)
        epics.caput('BAMZEBRA:PC_DISARM', 1)
        
        if self.with_xrf.isChecked():
        
            epics.caput('XSP3_4Chan:HDF1:Capture',0)    
            
            epics.caput('XSP3_4Chan:det1:Acquire',0)
            
        ml.DCM_THETA.VELO = 0.2 
        ml.DCM_THETA.BVEL = 0.2 
        npoints_real=int(epics.caget("BAMZEBRA:PC_NUM_CAP"))

        # Retrieve data
        self.ioni1 = epics.caget("BAMZEBRA:PC_DIV1", count=npoints)
        self.ioni2 = epics.caget("BAMZEBRA:PC_DIV2", count=npoints)
        self.ioni3 = epics.caget("BAMZEBRA:PC_DIV3", count=npoints)
        self.encpos = epics.caget("BAMZEBRA:PC_ENC2", count=npoints)
        
        self.ioni1=self.ioni1[0:npoints_real-1]
        self.ioni2=self.ioni2[0:npoints_real-1]
        self.ioni3=self.ioni3[0:npoints_real-1]
        self.encpos = self.encpos[0:npoints_real-1]
        
        self.divmax= epics.caget("BAMZEBRA:DIV2_DIV")
        self.ioni1=add_constant_if_decreasing(self.ioni1, self.divmax)
        self.ioni2=add_constant_if_decreasing(self.ioni2, self.divmax)
        self.ioni3=add_constant_if_decreasing(self.ioni3, self.divmax)

        self.i0 = np.gradient(self.ioni1) 
        self.i1 = np.gradient(self.ioni2) 
        self.i2 = np.gradient(self.ioni3) 
        self.ene = angle_to_energy(self.encpos) 

        # Plot the results
        
        self.plot_data(self.ene, self.i0, self.i1, self.i2,direction)
        
       # ml.DCM_THETA.VELO = 0.15  
      #  ml.DCM_THETA.move(dcmstart + 0.1, wait=True)



    def plot_data(self, ene, i0, i1, i2,direction):
        directions=('Backwards','Forward')
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(ene, -1 * i0 / i1, label='Sample')
        ax.plot(ene, -1 * i2 / i1, label='Reference')
        ax.legend()
        print(directions[direction])
        self.canvas.draw()
         
        self.canvas.flush_events()
        plt.pause(0.1)  
        
    def save_data(self):
        # Open a file dialog to select the directory and filename
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Save Data", "", "Text Files (*.txt);;All Files (*)")

        if file_path:
            with open(file_path, "w") as file_object:
                file_object.write('Ene I0 I1 I2\n')
                for a, b, c, d in zip(self.ene, self.i0, self.i1, self.i2):
                    file_object.write(f"{a} {b} {c} {d}\n")

            print("Data saved to:", file_path)

# Entry point of the application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())

