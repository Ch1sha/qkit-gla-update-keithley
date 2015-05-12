import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from time import sleep

#from tip_gui_lib import DATA, AcquisitionThread, remote_client
from qviewkit_cover import Ui_MainWindow
import pyqtgraph as pg
#from pyqtgraph import ImageView

import argparse
import ConfigParser
import numpy as np
import h5py

class DATA(object):
    pass

class MainWindow(QMainWindow, Ui_MainWindow):

    # custom slot

    def myquit(self):
        exit()

    def __init__(self,data):
        self.data = data

        QMainWindow.__init__(self)
        # set up User Interface (widgets, layout...)
        self.setupUi(self)
        self.graphicsView = pg.ImageView(self.centralwidget,view=pg.PlotItem())
        self.graphicsView.setObjectName("graphicsView")
        self.graphicsView.view.setAspectLocked(False)
        self.graphicsView2 = pg.ImageView(self.centralwidget,view=pg.PlotItem())
        self.graphicsView2.setObjectName("graphicsView2")
        self.graphicsView2.view.setAspectLocked(False)
        #self.graphicsView
        
        self.verticalLayout.addWidget(self.graphicsView)
        self.verticalLayout.addWidget(self.graphicsView2)
        
        
        #self.menubar.setNativeMenuBar(False)
        self._setup_signal_slots()
        self.setup_timer()
        #self._setup_views()
        
    def setup_timer(self):
         self.timer = QTimer()
         self.timer.timeout.connect(self.update_plots)
    def live_update_onoff(self):
        if self.liveCheckBox.isChecked():
            print "start timer"
            self.timer.start(2000) # 1000 ms repetation
        else:
            print "stop timer"
            self.timer.stop()
        
    def _setup_signal_slots(self):
        
        self.live_signal = pyqtSignal()
        #QObject.connect(self.newT_SpinBox,SIGNAL("valueChanged(double)"),self._update_newT)
        
        #QObject.connect(self.P_SpinBox,SIGNAL("valueChanged(double)"),self._update_P)
        #QObject.connect(self.I_SpinBox,SIGNAL("valueChanged(double)"),self._update_I)
        #QObject.connect(self.D_SpinBox,SIGNAL("valueChanged(double)"),self._update_D)
        
        QObject.connect(self.updateButton,SIGNAL("released()"),self.update_plots)
        
        #QObject.connect(self.Quit,SIGNAL("released()"),self._quit_tip_gui)
        #QObject.connect(self.live_sig,SIGNAL("").self.liveBeat)
        self.FileButton.clicked.connect(self.selectFile)
        self.liveCheckBox.clicked.connect(self.live_update_onoff)
    
    
    def _setup_views(self):
        self.Temp_view.setLabel('left',"Temperature / K")
        self.Temp_view.setLabel('bottom',"Time")
        self.Temp_view.plt = self.Temp_view.plot(pen='y')
        

        self.Heat_view.setLabel('left',"Heat / uW")
        self.Heat_view.setLabel('bottom',"Time")
        self.Heat_view.plt = self.Heat_view.plot(pen='y')
        


    def _quit_tip_gui(self):
        self.data.wants_abort = True
        sleep(0.5)
        exit()
        
    @pyqtSlot(float)
    def _update_Error(self,Error):
        self.Errors=numpy.delete(numpy.append(self.Errors,Error*1e6),0)
        self.Error_view.plt.setData(self.times, self.Errors)
        
    def update_plots(self):
        #self.live_signal.emit()
        
        self.h5file= h5py.File(str(self.DataFilePath))
        
        self.display_2D_data("amp_0",graphicsView = self.graphicsView)
        self.display_2D_data("pha_0",graphicsView = self.graphicsView2)
        
        self.h5file.close()
        print "updated"

    def selectFile(self):
        #lineEdit.setText(
        self.DataFilePath=QFileDialog.getOpenFileName(filter="*.h5")
        print self.DataFilePath
        self.statusBar().showMessage(self.DataFilePath)
 
        
    def display_2D_data(self,dataset,graphicsView):
        ds_path = '/entry/data/'+str(dataset)
        ds = self.h5file[ds_path]
        fill = ds.attrs.get("fill")
        data = np.array(ds[:fill])
        
        xmin = ds.attrs.get("xmin")
        ymin = ds.attrs.get("ymin")
        xmax = ds.attrs.get("xmax")
        ymax = ds.attrs.get("ymax")
        pos = (xmin,ymin)
        
        scale=(xmax/float(data.shape[0]),ymax/float(data.shape[1]))
        #scale=(100,100)
        
        #print len(data)
        
        graphicsView.setImage(data,pos=pos,scale=scale)
        # Fixme roi ...
        graphicsView.roi.setPos([xmin,ymin])
        graphicsView.roi.setSize([xmax,ymax])
        graphicsView.show()
        
    def display_amplitude(self):
       
        data =np.array(self.h5file['/entry/data/pha_0'])
        
        self.graphicsView.setImage(data)#,pos=pos,scale=scale)
        self.graphicsView.show()
        
        
    def populate_data_list(self):
        for i,v in enumerate(self.h5file["/entry/data"].keys()):
             self.data_list.insertItem(i,v)   


# Main entry to program.  Sets up the main app and create a new window.
def main(argv):
    # some configuration boilerplate
    data = DATA()
    """
    parser = argparse.ArgumentParser(
        description="TIP Is not Perfect // HR@KIT 2011-2015")

    parser.add_argument('ConfigFile', nargs='?', default='settings_local.cfg',
                        help='Configuration file name')
    args=parser.parse_args()

    data.Conf = ConfigParser.RawConfigParser()
    data.Conf.read(args.ConfigFile)
    """
    # create Qt application
    app = QApplication(argv,True)
    # create main window
    wnd = MainWindow(data) # classname
    wnd.show()
    
    # Connect signal for app finish
    app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
    
    # Start the app up
    sys.exit(app.exec_())
 
if __name__ == "__main__":
    main(sys.argv)
