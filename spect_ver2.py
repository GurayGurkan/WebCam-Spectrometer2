# -*- coding: utf-8 -*-
"""

@author: vGurkan
"""

import PyQt4
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
import gui_spectver2
import pyqtgraph as pg
import numpy as np
import cv2
import time

class Spect(QMainWindow,gui_spectver2.Ui_MainWindow):
    def __init__(self,parent=None):
        super(Spect,self).__init__(parent)
        self.setupUi(self)


        self.cropped_image = pg.ImageItem()
        self.raw_image = pg.ImageItem()
        
        self.roiImage = ''
     
        self.figure1.addItem(self.cropped_image)    # Cropped Image
        
        self.figure3.addItem(self.raw_image)    #ROI Video
        
       
        self.row = pg.PlotDataItem(background='w')
        
        self.figure2.addItem(self.row)          # Spectrum Plot
        self.figure2.plotItem.setLabels(bottom='Wavelength (nm)')
        #self.figure2.plotItem.setLabels(bottom='Index')
        self.figure2.plotItem.setTitle('Spectrum')

        self.timer1 = QTimer()
        self.timer1.timeout.connect(self.updateImage)


        self.buttonStart.clicked.connect(self.startCapture)
        self.buttonStop.clicked.connect(self.stopCapture)
        self.buttonGrab.clicked.connect(self.grabImage)
        self.buttonCalibrate.clicked.connect(self.calibrate)
        self.buttonUpdateROI.clicked.connect(self.updateRoi)
        self.buttonUpdateProjection.clicked.connect(self.updateProjections)
        self.figure3.installEventFilter(self)
        
        try:
            # load ROI settings and update LineEdits
            self.roiRect = np.loadtxt('roi_settings.txt',dtype='int')
            self.line_mincol.setText(str(self.roiRect[0]))
            self.line_maxcol.setText(str(self.roiRect[1]))
            self.line_minrow.setText(str(self.roiRect[2]))
            self.line_maxrow.setText(str(self.roiRect[3]))
            self.spectLength = self.roiRect[1]-self.roiRect[0]
        except IOError:
            self.roiRect = np.array([20,20,100,100])
            QMessageBox.critical(self,"ROI Settings Not Found!","Please Re-Calibrate ROI")
        
        try:
            self.laserParams=np.loadtxt('projection_settings.txt',dtype='float')
            self.laserHigh.setText(str(self.laserParams[2]))
            self.laserLow.setText(str(self.laserParams[0]))
            self.projHigh.setText(str(self.laserParams[3]))
            self.projLow.setText(str(self.laserParams[1]))
            
        except IOError:
            self.laserParams = np.array([450,100,700,200])
            QMessageBox.critical(self,"Projection Settings Not Found!","Please Adjust Projections")
            

        
        self.genWavelenLabel()
        self.globalSpectrum = np.zeros((self.spectLength), dtype='float')
        self.rawSpectrum = np.zeros((self.spectLength), dtype='float')  
        self.calibVect = np.ones((self.spectLength), dtype='float')        
        self.updateFigureLimits()
        
        
        
        self.vid_obj =''


    def startCapture(self):
        self.vid_obj = cv2.VideoCapture(0)
        while not self.vid_obj:
            continue
        if self.vid_obj:
            
            self.getCamParameters()
#            self.vid_obj.set(cv.CV_CAP_PROP_FRAME_WIDTH,640)
#            self.vid_obj.set(cv.CV_CAP_PROP_FRAME_HEIGHT,480)
            self.vid_obj.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH,1024)
            self.vid_obj.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT,768)
#           self.vid_obj.set(4,640)
#           self.vid_obj.set(5,480)
           
            
            #self.vid_obj.set(17,5000.)
            
            self.timer1.start(50)
           
            

    def stopCapture(self):
        self.timer1.stop()
        self.vid_obj.release()
        self.cropped_image.hide()
        self.row.hide()
        self.raw_image.hide()
       
    def grabImage(self):
        self.timer1.stop()
        veri=time.localtime()
#        ad = '{}-{}-{}-{}-{}-{}'.format(veri[0],veri[1],veri[2],veri[3],veri[4],veri[5])
        
        ad = self.lineFilename.text()
        if ad == '': 
            ad = '{}-{}-{}-{}-{}-{}'.format(veri[0],veri[1],veri[2],veri[3],veri[4],veri[5])
            
        if cv2.imwrite(ad+'.jpeg', self.grabbed):
            np.savetxt(ad+'.txt', np.vstack((self.wavelengths,self.globalSpectrum)).T, fmt='%.3f',delimiter=',')
            self.timer1.start(50)
        else:
            print 'Failed'
            
    
    def calibrate(self):
        self.timer1.stop()
        while self.timer1.isActive():
            continue
        
        self.calibVect = 1/self.rawSpectrum
        self.timer1.start(50)
       
       
    def updateImage(self):
        t, frame = self.vid_obj.read()
        # transpose and convert color space
        frame = cv2.transpose(cv2.cvtColor(frame,cv2.cv.CV_RGB2BGR))
        
      
        if t:
            self.raw_image.setImage(image=frame)
            self.roiImage = frame[self.roiRect[0]:self.roiRect[1],self.roiRect[2]:self.roiRect[3],:]
            
            #self.grabbed = frame ??
            self.cropped_image.setImage(image=self.roiImage, autolevels=True)
            
            raw = np.sum(self.roiImage,2)
            
            #raw = raw[45:125,:] # 26.04.2018
            spectrum =np.sum(raw,1).astype('float')
            spectrum_n = spectrum/(raw.shape[0]*3*255.)
            self.rawSpectrum = spectrum
            self.globalSpectrum = self.rawSpectrum # * self.calibVect
            
        
            self.row.setData(self.wavelengths,self.globalSpectrum)
            
            
        else:
            print "No image"
            
            
 # VIDEO CONTROLS
    
    def changeGain(self,val):
        if self.vid_obj:
            self.vid_obj.set(14,np.uint8(val))
    def changeExpo(self,val):
        if self.vid_obj:
            self.vid_obj.set(15,-1*val)
    def changeBright(self,val):
        if self.vid_obj:
            self.vid_obj.set(10,val)
    def changeCont(self,val):
        if self.vid_obj:
            self.vid_obj.set(11,val)
    def changeWB(self,val):
        if self.vid_obj:
            self.vid_obj.set(17,val)
    def changeSat(self,val):
        if self.vid_obj:
            self.vid_obj.set(12,val)
            
    def getCamParameters(self):
        
        self.sliderExpo.setValue(-1*self.vid_obj.get(15))
        self.sliderGain.setValue(self.vid_obj.get(14))
        self.sliderCont.setValue(self.vid_obj.get(11))
        self.sliderBright.setValue(self.vid_obj.get(10))
        self.sliderWB.setValue(self.vid_obj.get(17))
        self.sliderSat.setValue(self.vid_obj.get(12))
        
        self.sliderExpo.valueChanged.connect(self.changeExpo)
        self.sliderGain.valueChanged.connect(self.changeGain)
        self.sliderCont.valueChanged.connect(self.changeCont)
        self.sliderBright.valueChanged.connect(self.changeBright)
        self.sliderWB.valueChanged.connect(self.changeWB)
        self.sliderSat.valueChanged.connect(self.changeSat)
    
    #¶ 18.06.2018
    def updateRoi(self):
        self.roiRect=np.array([int(self.line_mincol.text()),\
                              int(self.line_maxcol.text()),\
                              int(self.line_minrow.text()),\
                              int(self.line_maxrow.text())])
        
        try:
            np.savetxt('roi_settings.txt',self.roiRect,fmt='%d')
        except:
            pass
        self.updateFigureLimits()
        QMessageBox.critical(self,"ROI Settings Changed...","ROI Settings Saved...Please Re-Calibrate Projections...")
        
    def eventFilter(self,obj,event):
        
        if event.type()==2:
            self.coor.setText("(" + str(event.x()) + "," + str(event.y()) + ")")
        
        return False
    
    def updateFigureLimits(self):
        self.figure1.setGeometry(QRect(60, 30, self.roiRect[1]-self.roiRect[0], self.roiRect[3]-self.roiRect[2]))
        self.figure2.setGeometry(QRect(10, 50+self.roiRect[3]-self.roiRect[2], (self.roiRect[1]-self.roiRect[0])+60, 250))
        self.figure2.setLineWidth(3)
    
    def updateProjections(self):
        self.laserParams[2] = float(self.laserHigh.text())
        self.laserParams[0] = float(self.laserLow.text())
        self.laserParams[1] = int(self.projLow.text())
        self.laserParams[3] = int(self.projHigh.text())
        self.genWavelenLabel()
        np.savetxt('projection_settings.txt',self.laserParams,fmt='%.2f')
        
    def genWavelenLabel(self):
        bias = self.roiRect[0]
        length = self.roiRect[1]-bias
        x1 = self.laserParams[1] - bias # Lower Wavelength Laser Proj. Val.
        x2 = self.laserParams[3] - bias # Higher Wavelength Laser Proj. Val.
        L1 = self.laserParams[0] # Lower Wavelength Val.
        L2 = self.laserParams[2] # Lower Wavelength Val.
        
        a = (L1 - L2)/(float(x1-x2))
        b = (L2*x1-L1*x2)/float(x1-x2)
        Lmin = b
        Lmax = a*(length-1)+b
        self.wavelengths = np.linspace(Lmin,Lmax,length)
        
        
        
                
        
            
        

app=QApplication(sys.argv)
form=Spect()
form.show()
app.exec_()
