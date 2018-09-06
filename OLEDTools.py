# 180719 MBJ
# Contains functions used to talk to Keysight 34460A Multimeter
# and Keysight B2901A Source Measure Unit (SMU)
# as well as some functions used in general device testing
import time
import csv
import os
import visa
import datetime

def currDecay(sourceCurrent,maxTime):
    rm = visa.ResourceManager()
    B2901A = rm.list_resources()[0]
    K34460A = rm.list_resources()[1]
    smu = rm.open_resource(B2901A)
    mm = rm.open_resource(K34460A)
    smu.write("*RST")
    print("SMU: {}".format(smu.query("*IDN?")))
    smu.write(":SOUR:FUNC:MODE CURR")
    smu.write(":SOUR:CURR:RANG 0.01")
    smu.write(":SOUR:CURR {}".format(sourceCurrent))
    smu.write(":SENS:FUNC 'VOLTS'")
    smu.write(":SENS:VOLT:RANG 200")
    smu.write(":SENS:VOLT:NPLC 1")
    smu.write(":SENS:VOLT:PROT 21")
    mm.write("*RST")
    mm.write(":CONF:CURR:DC")
    mm.write(":CURR:DC:NPLC 1")
    print("{} sec left".format(maxTime))
    tbegin = datetime.datetime.now()
    smu.write(":OUTP ON")
    voltList = []
    currList = []
    timeList = []
    brightList = []
    smu.write(":INIT")
    tRun = datetime.datetime.now() - tbegin
    twait = 0
    ret = ""

    while (tRun.seconds<maxTime):
        voltList.append(smu.query(":MEAS:VOLT?").split('\n')[0])
        currList.append(smu.query(":MEAS:CURR?").split('\n')[0])
        brightTemp = mm.query(":MEAS:CURR?").split('\n')[0]
        brightList.append(brightTemp)
        if float(brightTemp) < .005e-6:
            print("No Output! Breaking Decay Loop...")
            ret = "fail"
            break
        tRun = datetime.datetime.now() - tbegin
        timeList.append(tRun.seconds+(1E-6)*tRun.microseconds)
        time.sleep(twait)
    smu.write(":OUTP OFF")
    outList = list(zip(timeList,voltList,currList,brightList))
    smu.write(":OUTP OFF")
    if ret != "fail":
        return outList
    if ret == "fail":
        return "fail"

def IVBSweep(Vbegin, Vend, step, maxCurr, newSweep):
    rm = visa.ResourceManager()
    B2901A_address = rm.list_resources()[0]
    MM_34460_address = rm.list_resources()[1]
    smu = rm.open_resource(B2901A_address)
    mm = rm.open_resource(MM_34460_address)
    mm.timeout = 5000000
    smu.timeout = 5000000
    aperture = .15
    nplcTime = 1
    if newSweep == 1:
        smu.write(":SOUR:FUNC:MODE VOLT")
        smu.write(":SOUR:VOLT:MODE SWE")
        smu.write(":SOUR:VOLT:RANG 20")
        smu.write(":SOUR:VOLT:STAR {}".format(Vbegin))
        smu.write(":SOUR:VOLT:STOP {}".format(Vend))
        smu.write(":SOUR:VOLT:POIN {}".format(step))
        smu.write(":SOUR:SWE:DIR UP")
        smu.write(":SOUR:SWE:SPAC LOG")

        mm.write('*RST')
        mm.write(':CONF:CURR:DC')
        mm.write(':CURR:DC:NPLC {}'.format(nplcTime))
        mm.write(':TRIG:COUN {}'.format(step))
        mm.write(':TRIG:SOUR EXT')
        mm.write(':TRIG:DEL .01')
        mm.write(':INIT')

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

        brightCurr = mm.query(":FETC?").split(',')
        measCurr = smu.query(':FETC:ARR:CURR? (@1)').split(',')
        sourceVolts = smu.query(':FETC:ARR:VOLT? (@1)').split(',')

        smu.write(':OUTP OFF')
        VIBList = list(zip(sourceVolts,measCurr,brightCurr))
        return VIBList

# Executes a linear IV sweep and returns IV output
def LinSweepSMU(Vbegin, Vend, samplePoints, stepT, maxCurr):
    rm = visa.ResourceManager()
    B2901A_address = rm.list_resources()[0]
    smu = rm.open_resource(B2901A_address)
    totalTime = (stepT+.005)*samplePoints
    smu.write('*RST')
    print("SMU: {}".format(smu.query("*IDN?")))
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
    time.sleep(totalTime)
    measCurr = smu.query(':FETC:ARR:CURR? (@1)').split(',')
    sourceVolts = smu.query(':FETC:ARR:VOLT? (@1)').split(',')
    VIpairs = list(zip(sourceVolts,measCurr))
    return VIpairs

# Closes connection to SMU:
def SMUclose():
    rm = visa.ResourceManager()
    B2901A_address = rm.list_resources()[0]
    MM_34460_address = rm.list_resources()[1]
    mm = rm.open_resource(MM_34460_address)
    smu = rm.open_resource(B2901A_address)
    smu.write(':OUTP OFF')
    smu.close()
    mm.close()

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

# Outputs IV-Brightness data to a .csv
def writeIVB(fn,data):
    with open(fn, 'w',newline='') as csvfile:
        writer = csv.writer(csvfile)
        row1 = ["Voltage (V)","Current (A)","Brightness Current (A)"]
        writer.writerow(row1)
        for row in data:
            writer.writerow(row)

# Outputs IV-Brightness Decay data to a .csv
def writeIVBDecay(fn,data):
    with open(fn, 'w',newline='') as csvfile:
        writer = csv.writer(csvfile)
        row1 = ["Time (sec)","Voltage (V)","Current (A)","Brightness Current (A)"]
        writer.writerow(row1)
        for row in data:
            writer.writerow(row)
