import OLEDTools
import time
import serial
import visa
import datetime

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
