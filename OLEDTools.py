# 180719 MBJ
# Contains functions used to talk to Keysight 34460A Multimeter
# and Keysight B2901A Source Measure Unit (SMU)
# as well as some functions used in general device testing
import time
import csv
import os
import visa

# Executes a linear IV sweep and returns IV output
def LinSweepSMU(Vbegin, Vend, samplePoints, stepT, maxCurr):
    rm = visa.ResourceManager()
    B2901A_address = rm.list_resources()[0]
    smu = rm.open_resource(B2901A_address)
    totalTime = stepT * samplePoints
    smu.write('*RST')
    smu.write(':SOUR:FUNC:MODE VOLT')
    smu.write(':SOUR:VOLT:MODE SWE')
    smu.write(':SOUR:VOLT:RANG 20')
    smu.write(':SOUR:VOLT:STAR {}'.format(Vbegin))
    smu.write(':SOUR:VOLT:STOP {}'.format(Vend))
    smu.write(':SOUR:VOLT:POIN {}'.format(samplePoints))
    smu.write(':SOUR:SWE:DIR UP')
    smu.write(':SOUR:SWE:SPAC LIN')
    smu.write(':SOUR:SWE:STA SING')
    smu.write(':SENS:FUNC ""CURR""')
    smu.write(':SENS:CURR:RANG:AUTO ON')
    smu.write(':SENS:CURR:APER {}'.format(stepT))
    smu.write(':SENS:CURR:PROT {}'.format(maxCurr))
    smu.write(':FORM:DATA ASC')
    smu.write(':TRIG:SOUR AINT')
    smu.write(':TRIG:COUN {}'.format(samplePoints))
    smu.write(':OUTP ON')
    smu.write(':INIT (@1)')
    time.sleep(totalTime + 10)
    measCurr = smu.query(':FETC:ARR:CURR? (@1)').split(',')
    sourceVolts = smu.query(':FETC:ARR:VOLT? (@1)').split(',')
    VIpairs = list(zip(sourceVolts,measCurr))
    return VIpairs

# Closes connection to SMU:
def SMUclose():
    rm = visa.ResourceManager()
    B2901A_address = rm.list_resources()[0]
    smu = rm.open_resource(B2901A_address)
    smu.write(':OUTP OFF')
    smu.close()


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
