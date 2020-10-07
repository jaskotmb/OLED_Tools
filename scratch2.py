<<<<<<< Updated upstream
import os
import glob
import OLEDTools

os.chdir('C:\\Users\\Jerry\\IdeaProjects\\OceanOpticsSpectrum\\PLQ_200407_data_Mx\\Mx100\\rat2')
files = os.listdir(os.getcwd())
print(files)
for file in files:
    OLEDTools.quenchAnalyzePLwV("V",file,0,1,"V")
=======
import numpy
import math
import OLEDTools
import serial
import time

ser = serial.Serial('COM3',9600,timeout=0)
time.sleep(0.5)
ser.write(b'+0')
time.sleep(2)
ser.write(b'-8')
time.sleep(2)

#print(list(numpy.logspace(math.log10(3.55),math.log10(11),num=10)))

#tv = OLEDTools.findTurnOnVoltage(-3.5,-4.5,.01,5e-3,3e-8)
#tv = OLEDTools.findTurnOnVoltage(5,10,.005,5e-3,3e-8)
#print(tv)

OLEDTools.biasVoltsTime(5,-4)
#OLEDTools.currDecay(.005,10)
>>>>>>> Stashed changes
