# 180719 MBJ
# Contains functions used to talk to Keysight 34460A Multimeter
# and Keysight B2901A Source Measure Unit (SMU)
# as well as some functions used in general device testing
import time
import csv
import os

# Executes a linear IV sweep and returns IV output
def LinSweep(SMUName, Vbegin, Vend, samplePoints, stepT, maxCurr):
    totalTime = stepT * samplePoints
    SMU.write('*RST')
    SMU.write(':SOUR:FUNC:MODE VOLT')
    SMU.write(':SOUR:VOLT:MODE SWE')
    SMU.write(':SOUR:VOLT:RANG 20')
    SMU.write(':SOUR:VOLT:STAR {}'.format(Vbegin))
    SMU.write(':SOUR:VOLT:STOP {}'.format(Vend))
    SMU.write(':SOUR:VOLT:POIN {}'.format(samplePoints))
    SMU.write(':SOUR:SWE:DIR UP')
    SMU.write(':SOUR:SWE:SPAC LIN')
    SMU.write(':SOUR:SWE:STA SING')
    SMU.write(':SENS:FUNC ""CURR""')
    SMU.write(':SENS:CURR:RANG:AUTO ON')
    SMU.write(':SENS:CURR:APER {}'.format(stepT))
    SMU.write(':SENS:CURR:PROT {}'.format(maxCurr))
    SMU.write(':FORM:DATA ASC')
    SMU.write(':TRIG:SOUR AINT')
    SMU.write(':TRIG:COUN {}'.format(samplePoints))
    SMU.write(':OUTP ON')
    SMU.write(':INIT (@1)')
    time.sleep(totalTime + 10)
    measCurr = SMU.query(':FETC:ARR:CURR? (@1)').split(',')
    sourceVolts = SMU.query(':FETC:ARR:VOLT? (@1)').split(',')
    VIpairs = list(zip(sourceVolts,measCurr))
    return VIpairs

# Returns a string of the current time: "YYYYMMDD-HH-mm-ss"
def stringTime():
    startTime = time.localtime()
    s = str(startTime.tm_year) + str(startTime.tm_mon).zfill(2) + str(startTime.tm_mday).zfill(2) + '-' + str(
        startTime.tm_hour).zfill(2) + '-' + str(startTime.tm_min).zfill(2) + '-' + str(startTime.tm_sec).zfill(2)
    return s

# Creates a directory (if none exists) with today's date: "YYYYMMDD"
# then moves cwd to that directory
def makeTodayDir():
    todayName = stringTime()[0:8]
    if not os.path.exists(todayName):
        os.mkdir(todayName)
        print("Created Directory for today: {}\\{}".format(os.getcwd(),todayName))
    os.chdir(todayName)
    print("Changed Directory to: {}".format(os.getcwd()))
    return

# Outputs IV data to a .csv
def writeMobility(fn,data):
        with open(fn, 'w',newline='') as csvfile:
            writer = csv.writer(csvfile)
            row1 = ["Voltage (V)","Current (A)"]
            writer.writerow(row1)
            for row in data:
                writer.writerow(row)
