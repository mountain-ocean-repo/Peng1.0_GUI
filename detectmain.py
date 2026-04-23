# This Python file uses the following encoding: utf-8

import sys
import os
from PySide6.QtWidgets import (QMainWindow, QFileDialog,QColorDialog, QComboBox,
                                QDialog, QFontComboBox,QTextEdit, QInputDialog,
                                QLineEdit, QMenu, QMessageBox,QProgressBar, QToolBar,
                                QVBoxLayout, QWidget, QTreeView, QTableView, QFileSystemModel,
                                QHeaderView)
from PySide6.QtGui import (QAction, QGuiApplication, QIcon, QKeySequence, QStandardItemModel,
                            QStandardItem, QImage, QPixmap)
from PySide6.QtCore import (QUrl, Qt, Slot, Signal, QDir)

from PySide6.QtPrintSupport import (QAbstractPrintDialog, QPrinter,
                                    QPrintDialog, QPrintPreviewDialog)
from PySide6.QtSql import QSqlTableModel
from PySide6.QtGui import QIcon
#from tr import tr
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from scipy import stats
import openpyxl

from ui import ui_detectmain
from camera import Camera


class DetectMain(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = ui_detectmain.Ui_Form()
        self.ui.setupUi(self)

#        #put the cameraWidget in cameraMainlVLayout
        self.mainCamera = Camera()
#        self.ui.cameraMainGroupBox.setWidget(self.mainCamera._ui.cameraWidget)
        self.ui.cameraMainlVLayout.addWidget(self.mainCamera._ui.cameraWidget)
        self.ui.cameraMainlVLayout.setContentsMargins(0,0,0,0)


        #
        self.layout = QVBoxLayout()
        self.ui.widgetChart.setLayout(self.layout)

        # canvas
#        self.figure = plt.figure()
        self.figure, self.ax = plt.subplots(figsize=(15,15), dpi=100)#nrows=1, ncols=1,figsize=(15,10))#figsize=(20,15))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.layout.addWidget(self.canvas)
#        self.layout.addWidget(self.toolbar)




        # Linear regression: read source data (full precision for the fit)
        lin_headers, lin_rows = self._read_excel('./interface/linear/table/linear_regression_table.xlsx')
        ycol = self._first_color_index(lin_headers)
        con_lin = [r[lin_headers.index("Con.")] for r in lin_rows]
        y_channel = [r[ycol] for r in lin_rows]
        y_label = lin_headers[ycol]
        channel_color = self.CHANNEL_COLORS.get(y_label, '#2ca02c')

        # Linear regression display table: read from only_table/
        disp_headers, disp_rows = self._read_excel(
            './interface/linear/only_table/linear_regression_table.xlsx')
        self._populate_tableview(self.ui.tabviewOrig, disp_headers, disp_rows)



        # plot the Chart
        font = {'family': 'serif',
                'color':  'black',
                'weight': 'normal',
                'size': 13,
                }

        x = con_lin
        y = y_channel
        slope, intercept, r, p, std_err = stats.linregress(x, y)
        R2 = pow(r, 2)
        def myfunc(x):
            return slope*x+intercept
        mymodel = list(map(myfunc, x))

        text = "Y = {:.4f}*X+{:.2f}".format(slope, intercept)
#        print('text=', text)
#        print("y = {:.2f}*x+{:.2f}".format(slope, intercept))

        # Detection: read detection-source data, compute predicted concentrations
        det_headers, det_rows = self._read_excel('./interface/detect/table/detection_table.xlsx')
        dcol = self._first_color_index(det_headers)
        det_channel = [r[dcol] for r in det_rows]
        con_pred = [(v - intercept) / slope for v in det_channel]
        print('con: ', con_pred)

#        plt.plot(x, y, 'k')
        plt.title('Linear Regression and ML-assisted HT-Detection', fontdict=font, fontsize=15)

        # Formula overlay: keep clear of the regression line by docking to the
        # corner opposite the slope direction; axes-fraction coords keep it
        # stable across data scales.
        if slope >= 0:
            tx, ha = 0.02, 'left'
        else:
            tx, ha = 0.98, 'right'
        self.ax.text(tx, 0.96,
                "Y = {:.4f} * X+{:.2f} ,  R$^2$ = {:.4f}".format(slope, intercept, R2),
                transform=self.ax.transAxes,
                ha=ha, va='top',
                fontsize=16, fontstyle='italic', fontfamily='times new roman',
                color=(0, 0, 0, 1),
                bbox=dict(facecolor=channel_color, alpha=0.5, edgecolor='none',
                          boxstyle='round,pad=0.3'))
        # plt.text(61, 143, r'$\cos(2 \pi t) \exp(-t)$', fontdict=font)
        plt.xlabel('Concentration of AA (μM)', fontdict=font, fontsize=13) #'Concentration of Hg$^{2+}$ (μM)'
        plt.ylabel('{} Value'.format(y_label), fontdict=font, fontsize=13)



        plt.scatter(x, y, color=channel_color, linewidths=4, zorder=1)
        plt.plot(x, mymodel, color=channel_color, linewidth=3, linestyle='--', alpha=0.7, zorder=2)
        plt.scatter(con_pred, det_channel, color='#ff7f0e', linewidths=4, zorder=3)




        plt.legend(('experimental data', 'linear regression', 'detection result'),
                   loc='lower right', shadow=True)

        marker_color = '#ff7f0e'
        marker_size = 10
        # Offset annotations in pixel space so labels never land on top of the marker,
        # regardless of the data range.
        for cx, cy in zip(con_pred, det_channel):
            plt.annotate('({:.2f},{:.2f})'.format(cx, cy),
                         xy=(cx, cy), xytext=(8, 8),
                         textcoords='offset points',
                         fontsize=marker_size, color=marker_color)


        # for x, y in zip(con[0:3], rgb_G[0:3]):
        #     plt.text(x+1, y, '({:.2f},{:.2f})'.format(x,y),fontsize=10,rotation=0,color='#ff7f0e') #f'(x: {x}, y: {y})')
        # for x, y in zip(con[3:6], rgb_G[3:6]):
        #     plt.text(x+1, y, '({:.2f},{:.2f})'.format(x,y),fontsize=10,rotation=0,color='#ff7f0e') #f'(x: {x}, y: {y})')
        plt.show()



        # Detection display table: read from only_table/
        det_disp_headers, det_disp_rows = self._read_excel(
            './interface/detect/only_table/detection_table.xlsx')
        self._populate_tableview(self.ui.tabviewRecg, det_disp_headers, det_disp_rows)


        self.origImg = self._resolve_image('./interface/linear/image/linear_regression_image')
        self.recgImg = self._resolve_image('./interface/detect/image/detection_image')
        self._origPixmap = QPixmap(self.origImg)
        self._recgPixmap = QPixmap(self.recgImg)
        self.ui.labelOrigImg.setMinimumSize(1, 1)
        self.ui.labelRecgImg.setMinimumSize(1, 1)
        self.ui.labelOrigImg.setAlignment(Qt.AlignCenter)
        self.ui.labelRecgImg.setAlignment(Qt.AlignCenter)
        self._update_image_scales()

        self.ui.progressBar.setValue(100)
        try:
            with open('./interface/detect/time.txt', 'r', encoding='utf-8') as f:
                raw = f.read().strip()
            digits = ''.join(ch for ch in raw if ch.isdigit())
            if digits:
                self.ui.lcdNumber.display(int(digits))
        except OSError:
            pass

    CHANNEL_COLORS = {
        'Red':   '#d62728',
        'Green': '#2ca02c',
        'Blue':  '#1f77b4',
    }

    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_image_scales()

    def _update_image_scales(self):
        for label, pix in ((getattr(self.ui, 'labelOrigImg', None), getattr(self, '_origPixmap', None)),
                           (getattr(self.ui, 'labelRecgImg', None), getattr(self, '_recgPixmap', None))):
            if label is None or pix is None or pix.isNull():
                continue
            label.setPixmap(pix.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    @classmethod
    def _resolve_image(cls, base_no_ext):
        for ext in cls.IMAGE_EXTENSIONS:
            candidate = base_no_ext + ext
            if os.path.exists(candidate):
                return candidate
        return base_no_ext + cls.IMAGE_EXTENSIONS[0]

    @staticmethod
    def _read_excel(path):
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active
        it = ws.iter_rows(values_only=True)
        headers = [str(h) for h in next(it)]
        rows = [r for r in it if any(c is not None for c in r)]
        return headers, rows

    @staticmethod
    def _first_color_index(headers):
        return headers.index("Con.") + 1

    @staticmethod
    def _populate_tableview(view, headers, rows):
        model = QStandardItemModel()
        model.setColumnCount(len(headers))
        for c, h in enumerate(headers):
            model.setHeaderData(c, Qt.Horizontal, h)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                if headers[c] == "No.":
                    text = str(int(val))
                elif isinstance(val, (int, float)):
                    text = "{:.2f}".format(round(float(val), 2))
                else:
                    text = "" if val is None else str(val)
                model.setItem(r, c, QStandardItem(text))
        view.setModel(model)
        view.verticalHeader().hide()
        for c in range(len(headers)):
            view.setColumnWidth(c, view.width() // 2)


# self.ui.labelOrigImg.width(),

#class Camera(QMainWindow):
#class ImageSettings(QDialog):
