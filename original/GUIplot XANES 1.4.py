#  -*- coding: utf-8 -*-
"""
Created on Fri Mar 24 14:14:34 2023

@author: bamline
"""
import sys
import h5py
import numpy as np
import os
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseButton

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLineEdit, QLabel, QHBoxLayout, QCheckBox

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'XANES Data Visualization'
        self.left = 100
        self.top = 100
        self.width = 800
        self.height = 600
        self.file_names = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        widget = QWidget(self)
        self.setCentralWidget(widget)

        layout = QVBoxLayout()
 
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('button_press_event', self.onclick)
        layout.addWidget(self.canvas)

        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)

        idx_layout = QHBoxLayout()
        self.start_idx_label = QLabel("Start ROI:")
        idx_layout.addWidget(self.start_idx_label)
        self.start_idx_edit = QLineEdit("0")
        idx_layout.addWidget(self.start_idx_edit)
        self.end_idx_label = QLabel("End ROI:")
        idx_layout.addWidget(self.end_idx_label)
        self.end_idx_edit = QLineEdit("4000")
        idx_layout.addWidget(self.end_idx_edit)
        self.plot_normalized_checkbox = QCheckBox("Plot XANES Normalized to Ioni")
        idx_layout.addWidget(self.plot_normalized_checkbox)
        self.plot_normalized_checkbox.stateChanged.connect(self.plot_data)

        layout.addLayout(idx_layout)

        self.start_idx_edit.editingFinished.connect(self.update_plot)
        self.end_idx_edit.editingFinished.connect(self.update_plot)

        self.load_button = QPushButton('Load Data', self)
        self.load_button.clicked.connect(self.load_data)
        layout.addWidget(self.load_button)

        self.plot_sum_button = QPushButton('Plot XRF Spectrum (for ROI selection)', self)
        self.plot_sum_button.clicked.connect(self.plot_sum_spectra)
        layout.addWidget(self.plot_sum_button)

        self.save_button = QPushButton('Save XAS Spectra', self)
        self.save_button.clicked.connect(self.save_spectra)
        layout.addWidget(self.save_button)

        # New button for saving XRF spectra
        self.save_xrf_button = QPushButton('Save XRF Spectra', self)
        self.save_xrf_button.clicked.connect(self.save_xrf_spectra)
        layout.addWidget(self.save_xrf_button)

        widget.setLayout(layout)

    def load_data(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select Data Files", "", "HDF5 Files (*.hdf5);;All Files (*)", options=options)
        if file_names:
            self.file_names = file_names
            self.plot_data()

    def save_spectra(self):
        if not self.file_names:
            print("No files loaded. Please load data first.")
            return
        for file_name in self.file_names:
            self.process_and_save(file_name)
        print(f"Successfully saved processed XANES data for {len(self.file_names)} file(s).")

    def _get_processed_data(self, file_name):
        """
        Centralized data processing function.
        It loads, normalizes each channel by its real-time, sums the channels,
        and applies the ROI.
        This ensures both plotting and saving use the exact same data.
        """
        start_idx = int(self.start_idx_edit.text())
        end_idx = int(self.end_idx_edit.text())
        
        with h5py.File(file_name, 'r') as hf:
            # Load data as float64 to allow for division
            dataraw = np.asarray(hf.get('entry/data/data'), dtype=np.float64)
            energy = np.asarray(hf.get('entry/instrument/NDAttributes/ENERGYDCM'))
            ioni = np.asarray(hf.get('entry/instrument/NDAttributes/Ioni13'))
            
            # Load real-time for all 4 channels
            try:
                real_time_ch1 = np.asarray(hf.get('entry/instrument/NDAttributes/CHAN1REALTIME')) * 12.5e-9
                real_time_ch2 = np.asarray(hf.get('entry/instrument/NDAttributes/CHAN2REALTIME')) * 12.5e-9
                real_time_ch3 = np.asarray(hf.get('entry/instrument/NDAttributes/CHAN3REALTIME')) * 12.5e-9
                real_time_ch4 = np.asarray(hf.get('entry/instrument/NDAttributes/CHAN4REALTIME')) * 12.5e-9
            except TypeError:
                print(f"Warning: Could not load real-time data for {os.path.basename(file_name)}. Data will not be normalized by time.")
                return None, None, None

            # Trim arrays to the same length
            npoints = len(dataraw)
            energy = energy[:npoints]
            ioni = ioni[:npoints]
            
            # --- Per-channel normalization by real-time ---
            # Avoid division by zero
            real_time_ch1[real_time_ch1 == 0] = 1.0
            real_time_ch2[real_time_ch2 == 0] = 1.0
            real_time_ch3[real_time_ch3 == 0] = 1.0
            real_time_ch4[real_time_ch4 == 0] = 1.0

            # The shape of real_time is (n_points,). We need to add a new axis to
            # broadcast it correctly for division with dataraw (n_points, n_channels, n_bins)
            dataraw[:, 0, :] /= real_time_ch1[:, np.newaxis]
            dataraw[:, 1, :] /= real_time_ch2[:, np.newaxis]
            dataraw[:, 2, :] /= real_time_ch3[:, np.newaxis]
            dataraw[:, 3, :] /= real_time_ch4[:, np.newaxis]
            
            # Sum the four (now normalized) detector channels
            data_sum_channels = np.sum(dataraw, axis=1)
            
            # Sum over the selected ROI from the MCA bins
            data_sum_roi = np.sum(data_sum_channels[:, start_idx:end_idx], axis=1)

            # Find the actual start of the scan (minimum energy) and trim away pre-scan points
            startpos = energy.argmin()
            
            final_energy = energy[startpos:]
            final_ioni = ioni[startpos:]
            final_data = data_sum_roi[startpos:]
            
            return final_energy, final_ioni, final_data

    def process_and_save(self, file_name):
        """Saves the processed XANES data to a CSV file."""
        energy, ioni, data = self._get_processed_data(file_name)
        
        if energy is None:
            print(f"Skipping save for {os.path.basename(file_name)} due to processing error.")
            return

        # Prepare for saving
        ioni_safe = ioni.copy()
        ioni_safe[ioni_safe == 0] = 1.0  # Avoid division by zero in the normalized column
        data_norm = data / ioni_safe
        
        output_filename = file_name.split('.hdf5')[0] + '_processed_XANES.csv'

        with open(output_filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Energy", "Ioni", "Data_Counts", "Data_Norm"])
            for i in range(len(energy)):
                writer.writerow([energy[i], ioni[i], data[i], data_norm[i]])

    def save_xrf_spectra(self):
        """Saves the integrated XRF spectrum (summed over energy) to a CSV file."""
        if not self.file_names:
            print("No files loaded. Please load data first.")
            return

        for file_name in self.file_names:
            with h5py.File(file_name, 'r') as hf:
                dataraw = np.asarray(hf.get('entry/data/data'), dtype=np.float64)
                
                # Load real-time for all 4 channels for normalization
                try:
                    real_time_ch1 = np.asarray(hf.get('entry/instrument/NDAttributes/CHAN1REALTIME')) * 12.5e-9
                    real_time_ch2 = np.asarray(hf.get('entry/instrument/NDAttributes/CHAN2REALTIME')) * 12.5e-9
                    real_time_ch3 = np.asarray(hf.get('entry/instrument/NDAttributes/CHAN3REALTIME')) * 12.5e-9
                    real_time_ch4 = np.asarray(hf.get('entry/instrument/NDAttributes/CHAN4REALTIME')) * 12.5e-9
                    
                    # Avoid division by zero
                    real_time_ch1[real_time_ch1 == 0] = 1.0
                    real_time_ch2[real_time_ch2 == 0] = 1.0
                    real_time_ch3[real_time_ch3 == 0] = 1.0
                    real_time_ch4[real_time_ch4 == 0] = 1.0

                    # Normalize each channel by its real-time
                    dataraw[:, 0, :] /= real_time_ch1[:, np.newaxis]
                    dataraw[:, 1, :] /= real_time_ch2[:, np.newaxis]
                    dataraw[:, 2, :] /= real_time_ch3[:, np.newaxis]
                    dataraw[:, 3, :] /= real_time_ch4[:, np.newaxis]

                except TypeError:
                    print(f"Warning: Could not load real-time data for {os.path.basename(file_name)}. XRF data will not be normalized by time.")
                    # If real-time data is not available, proceed without time normalization for XRF
                    pass # dataraw remains un-normalized for time in this case
                
                # Sum over all energy points (axis 0) and all channels (axis 1)
                # to get a single spectrum vs MCA bins
                xrf_spectrum = np.sum(dataraw, axis=(0, 1))

                output_filename = file_name.split('.hdf5')[0] + '_XRF_Spectrum.csv'
                with open(output_filename, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["MCA_Channel", "Total_Counts"])
                    for i in range(len(xrf_spectrum)):
                        writer.writerow([i, xrf_spectrum[i]])
            print(f"Successfully saved XRF spectrum for {os.path.basename(file_name)} to {output_filename}")
        print(f"Successfully saved XRF spectra for {len(self.file_names)} file(s).")


    def plot_data(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        for file_name in self.file_names:
            self.plot_individual_data(file_name, ax)
        
        ax.legend()
        self.canvas.draw()

    def plot_individual_data(self, file_name, ax):
        """Plots the data from a single file using the centralized processing function."""
        energy, ioni, data = self._get_processed_data(file_name)
        
        if energy is None:
            return # Don't plot if processing failed
            
        if self.plot_normalized_checkbox.isChecked():
            ioni_safe = ioni.copy()
            ioni_safe[ioni_safe == 0] = 1.0 # Avoid division by zero
            ax.plot(energy, data / ioni_safe, label=f'Normalized: {os.path.basename(file_name)}')
        else:
            # This plots the total counts from all channels within the ROI
            ax.plot(energy, data, label=os.path.basename(file_name))
        
    def update_plot(self):
        if self.file_names:
            self.plot_data()

    def plot_sum_spectra(self):
        """Plots the summed spectrum vs. MCA channel to help the user select the ROI."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        sum_spectra_all_files = None
        for file_name in self.file_names:
            with h5py.File(file_name, 'r') as hf:
                dataraw = np.asarray(hf.get('entry/data/data'), dtype=np.float64) # Ensure float for division

                # Load real-time for all 4 channels for normalization
                try:
                    real_time_ch1 = np.asarray(hf.get('entry/instrument/NDAttributes/CHAN1REALTIME')) * 12.5e-9
                    real_time_ch2 = np.asarray(hf.get('entry/instrument/NDAttributes/CHAN2REALTIME')) * 12.5e-9
                    real_time_ch3 = np.asarray(hf.get('entry/instrument/NDAttributes/CHAN3REALTIME')) * 12.5e-9
                    real_time_ch4 = np.asarray(hf.get('entry/instrument/NDAttributes/CHAN4REALTIME')) * 12.5e-9

                    # Avoid division by zero
                    real_time_ch1[real_time_ch1 == 0] = 1.0
                    real_time_ch2[real_time_ch2 == 0] = 1.0
                    real_time_ch3[real_time_ch3 == 0] = 1.0
                    real_time_ch4[real_time_ch4 == 0] = 1.0

                    # Normalize each channel by its real-time
                    dataraw[:, 0, :] /= real_time_ch1[:, np.newaxis]
                    dataraw[:, 1, :] /= real_time_ch2[:, np.newaxis]
                    dataraw[:, 2, :] /= real_time_ch3[:, np.newaxis]
                    dataraw[:, 3, :] /= real_time_ch4[:, np.newaxis]

                except TypeError:
                    print(f"Warning: Could not load real-time data for {os.path.basename(file_name)}. Plotting XRF without time normalization.")
                    pass # dataraw remains un-normalized for time in this case
                
                # Sum over all energy points (axis 0) and all channels (axis 1)
                # to get a single spectrum vs MCA bins
                current_sum = np.sum(dataraw, axis=(0, 1))
                if sum_spectra_all_files is None:
                    sum_spectra_all_files = current_sum
                else:
                    sum_spectra_all_files += current_sum

        if sum_spectra_all_files is not None:
            ax.plot(sum_spectra_all_files, label=f'Sum Spectra for ROI Selection')
            ax.set_xlabel("MCA Channel (for ROI)")
            ax.set_ylabel("Total Integrated Counts")
            ax.set_title("Click and drag to zoom. Right-click to set ROI to visible range.")


        ax.legend()
        self.canvas.draw()

    def onclick(self, event):
        # This allows setting the ROI by right-clicking on the "Plot Sum Spectra" view
        if event.button == MouseButton.RIGHT and event.inaxes:
            ax = event.inaxes
            xlim = ax.get_xlim()
            # Ensure indices are integers and within reasonable bounds (0 to max MCA channel)
            start_val = max(0, int(xlim[0]))
            end_val = int(xlim[1]) # Allow end to be slightly outside if user clicks past
            if end_val <= start_val: # If click resulted in invalid range, default to full range
                start_val = 0
                end_val = 4000 # Assuming 4000 is a typical max channel
            self.start_idx_edit.setText(str(start_val))
            self.end_idx_edit.setText(str(end_val))
            self.plot_data() # Automatically update the main plot with the new ROI

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())