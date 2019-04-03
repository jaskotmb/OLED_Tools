import OLEDTools
import time
import serial
import visa
import datetime
import numpy
import math

<<<<<<< Updated upstream
aperture = .01
maxCurr = .001
step = 0.1
rm = visa.ResourceManager()
B2901A = rm.list_resources()[0]
smu = rm.open_resource(B2901A)
smu.write("*RST")
print("SMU: {}".format(smu.query("*IDN?")))
time.sleep(3)
smu.write(':SENS:FUNC ""CURR""')
smu.write(':SENS:CURR:RANG:AUTO ON')
smu.write(':SENS:CURR:APER {}'.format(aperture))
smu.write(':SENS:CURR:PROT {}'.format(maxCurr))
smu.write(':FORM:DATA ASC')
smu.write(':TRIG:SOUR AINT')
smu.write(':TRIG:COUN {}'.format(step))
smu.write(":TRIG:DEL .01")
smu.write(':OUTP ON')
smu.write(":SOUR:TOUT:STAT ON")
smu.write(":SOUR:TOUT:SIGN EXT3")
smu.write(":SOUR:DIG:EXT3:FUNC DIO")
smu.write(":SOUR:DIG:EXT3:TOUT:EDGE:POS BEF")
smu.write(':INIT (@1)')
=======
# mux = [1,2,3,4,5,6,7,8]
# ser = serial.Serial('COM3', 9600, timeout=0)
# for i in mux:
#     time.sleep(.5)
#     ser.write(b'+0')
#     time.sleep(2)
#     ser.write(str.encode('-' + str(i)))
#     print(i)
#     time.sleep(15)
#
#     OLEDTools.currDecay(-5e-3,5)
ser = serial.Serial('COM3',9600,timeout=0)
time.sleep(0.5)
ser.write(b'+0')
time.sleep(2)
ser.write(b'-7')
time.sleep(2)
voltsTurnOn = 11
voltsEnd = 3.5
voltSteps = 100
samplesEachPoint = 5
inputList = list(numpy.logspace(math.log10(voltsTurnOn),math.log10(voltsEnd),num=voltSteps))
inputList = [-x for x in inputList]
inputList = [x for x in inputList for i in range(samplesEachPoint)]
print(inputList)

#VIBList = OLEDTools.findTurnOnVoltage(-3.5,-3.8,0.001,0.02,1.5E-8)
VIBList5 = OLEDTools.IVBSweep(3,.02,inputList)
OLEDTools.writeIVB("ff1.csv",VIBList5)
ser.write(b'+7')

>>>>>>> Stashed changes
