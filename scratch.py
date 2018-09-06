import OLEDTools
import time
import serial
import visa
import datetime

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
# ser = serial.Serial('COM3',9600,timeout=0)
# time.sleep(0.5)
# ser.write(b'+0')
# time.sleep(2)
# ser.write(b'-1')
# time.sleep(2)
#
# VIBList = OLEDTools.IVBSweep(5,0,51,0.02,1)
# OLEDTools.writeIVB("foo3.csv",VIBList)
#ser.write(b'+1')

xOut = [x*1E-2 for x in range(0,150)]

print(xOut)
