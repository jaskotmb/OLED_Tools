# 180719 MBJ
# Contains functions used to talk to Keysight 34460A Multimeter
# and Keysight B2901A Source Measure Unit (SMU)
# as well as some functions used in general device testing
import time
import csv
import os
import visa
import datetime
import scipy.integrate

def integrateSpectrum(wavelengthList,intensityList,minWvl,maxWvl):
    relevantWvls = [x for x in wavelengthList if x > minWvl and x < maxWvl]
    for index in range(len(intensityList)):
        if relevantWvls[0] == wavelengthList[index]:
            break
    relevantIntens = intensityList[index:index+len(relevantWvls)]
    auc = scipy.integrate.cumtrapz(relevantIntens,relevantWvls)
    intBegin = relevantWvls[0]
    intEnd = relevantWvls[len(relevantWvls)-1]
    intAvg = auc[len(auc)-1]/(intEnd-intBegin)
    # print("Integration from {} to {} = {}".format(intBegin,intEnd,intSum)))
    return [intAvg,intBegin,intEnd]

def getSpectrum(fileName):
    # given a filename for an OO spectrum file, returns [(wavelength, intensity),...] tuple list

    file = open(fileName,"r")
    header= []
    begchar = ''
    while begchar != '>':
        temp = file.readline()
        header.append(temp)
        begchar = temp[0]

    fname = header[0].split('from ')[1].split(' ')[0]
    #print("Filename: {}".format(fname))
    date = header[2].split(': ')[1].split('\n')[0]
    #print("Date: {}".format(date))
    inttime = float(header[6].split(': ')[1].split('\n')[0])
    #print("Integration Time: {} seconds".format(inttime))
    scansavg = header[7].split(': ')[1].split('\n')[0]
    #print("Scans Averaged: {}".format(scansavg))

    wvl = []
    intens = []
    line = "Test"
    for line in file:
        lsplit = line.split('\t')
        wvl.append(float(lsplit[0]))
        intens.append(float(lsplit[1].split('\n')[0]))

    return list(zip(wvl,intens))

def iDevice():
    rm = visa.ResourceManager()
    for i in rm.list_resources():
        if "0x0957" in i:
            B2901A_address = i
    for i in rm.list_resources():
        if "0x2A8D" in i:
            MM_34460_address = i
    smu = rm.open_resource(B2901A)
    smu.write("*RST")
    print("SMU: {}".format(smu.query("*IDN?")))

def currDecay(sourceCurrent,maxTime):
    rm = visa.ResourceManager()
    for i in rm.list_resources():
        if "0x0957" in i:
            B2901A_address = i
    for i in rm.list_resources():
        if "0x2A8D" in i:
            MM_34460_address = i
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

def biasVoltsTime(totalTime,bias):
    rm = visa.ResourceManager()
    for i in rm.list_resources():
        if "0x0957" in i:
            B2901A_address = i
    smu = rm.open_resource(B2901A_address)
    smu.timeout = 5000000
    print("Reverse Biasing at {}V for {}sec".format(bias,totalTime))
    smu.write("*RST")
    print("SMU: {}".format(smu.query("*IDN?")))
    tbegin = datetime.datetime.now()
    smu.write(":OUTP ON")
    smu.write(":SOUR:FUNC:MODE VOLT")
    smu.write(":SOUR:VOLT:RANG 20")
    smu.write(":SOUR:VOLT {}".format(bias))
    smu.write(":SENS:FUNC 'CURR'")
    smu.write(":SENS:CURR:NPLC 1")
    smu.write(":SENS:CURR:PROT .005")
    tRun = datetime.datetime.now() - tbegin
    twait = .5
    smu.write(':INIT')
    while (tRun.seconds<totalTime):
        smu.query(":MEAS:CURR?")
        tRun = datetime.datetime.now() - tbegin
        time.sleep(twait)
    smu.write(':OUTP OFF')

def findTurnOnVoltage(Vbegin, Vend, stepVolts, maxCurr, brThreshold):
    #Does Linear sweep until V_TurnOn, then returns linear data with V_TurnOn as last data point
    rm = visa.ResourceManager()
    for i in rm.list_resources():
        if "0x0957" in i:
            B2901A_address = i
    for i in rm.list_resources():
        if "0x2A8D" in i:
            MM_34460_address = i
    smu = rm.open_resource(B2901A_address)
    mm = rm.open_resource(MM_34460_address)
    step = abs(round((Vend-Vbegin) / stepVolts)) + 1
    print("step: {}".format(step))
    print("StepVolts: {}".format(stepVolts))
    mm.timeout = 5000000
    smu.timeout = 5000000
    aperture = .15
    nplcTime = 1
    smu.write(":SOUR:FUNC:MODE VOLT")
    smu.write(":SOUR:VOLT:MODE SWE")
    smu.write(":SOUR:VOLT:RANG 20")
    smu.write(":SOUR:VOLT:STAR {}".format(Vbegin))
    smu.write(":SOUR:VOLT:STOP {}".format(Vend))
    smu.write(":SOUR:VOLT:POIN {}".format(step))
    smu.write(":SOUR:SWE:DIR UP")
    smu.write(":SOUR:SWE:SPAC LIN")

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

    indexThr = False
    if [x for x in brightCurr if float(x)>brThreshold]:
        indexThr = brightCurr.index([x for x in brightCurr if float(x)>brThreshold][0])
        print("indexThr = {}".format(indexThr))
        print("brightCurr at this index = {}".format(brightCurr[indexThr]))
        print("sourceVolts at this index = {}".format(sourceVolts[indexThr]))
    else:
        print("Turn-on Voltage not in range!")

    smu.write(':OUTP OFF')
    VIBList = list(zip(sourceVolts,measCurr,brightCurr))
    if [x for x in brightCurr if float(x)>brThreshold]:
        return sourceVolts[indexThr]

def IVBSweep(step, maxCurr, voltList):
    rm = visa.ResourceManager()
    for i in rm.list_resources():
        if "0x0957" in i:
            B2901A_address = i
    for i in rm.list_resources():
        if "0x2A8D" in i:
            MM_34460_address = i
    smu = rm.open_resource(B2901A_address)
    mm = rm.open_resource(MM_34460_address)
    mm.timeout = 50000000
    smu.timeout = 50000000
    aperture = .04
    nplcTime = 1
    newSweep = 1
    listString = ','.join(str(x) for x in voltList)
    if newSweep == 1:
        smu.write("*RST")
        smu.write(":SOUR:FUNC:MODE VOLT")
        smu.write(":SOUR:VOLT:RANG 20")
        smu.write(":SOUR:VOLT:MODE LIST")
        smu.write(":SOUR:LIST:VOLT {}".format(listString))

        print("Foo1")

        mm.write('*RST')
        mm.write(':CONF:CURR:DC')
        mm.write(':CURR:DC:NPLC {}'.format(nplcTime))
        mm.write(':TRIG:COUN {}'.format(len(voltList)))
        mm.write(':TRIG:SOUR EXT')
        mm.write(':TRIG:DEL .005')
        mm.write(':SAMP:SOUR TIM')
        mm.write(':SAMP:TIM 0.01')
        mm.write(':SAMP:COUN 1')
        mm.write(':INIT')

        print("Foo2")

        smu.write(':SENS:FUNC ""CURR""')
        smu.write(':SENS:CURR:RANG:AUTO ON')
        smu.write(':SENS:CURR:APER {}'.format(aperture))
        smu.write(':SENS:CURR:PROT {}'.format(maxCurr))
        smu.write(':FORM:DATA ASC')
        smu.write(':TRIG:SOUR AINT')
        smu.write(':TRIG:TIM .1')
        smu.write(':TRIG:COUN {}'.format(len(voltList)))
        smu.write(":TRIG:MEAS:DEL .005")
        smu.write(':OUTP ON')
        smu.write(":SOUR:TOUT:STAT ON")
        smu.write(":SOUR:TOUT:SIGN EXT3")
        smu.write(":SOUR:DIG:EXT3:FUNC DIO")
        smu.write(":SOUR:DIG:EXT3:TOUT:EDGE:POS BEF")
        smu.write(':INIT (@1)')

        print("Foo3")

        brightCurr = mm.query(":FETC?").split(',')
        print(brightCurr)
        print(len(brightCurr))
        measCurr = smu.query(':FETC:ARR:CURR? (@1)').split(',')
        sourceVolts = smu.query(':FETC:ARR:VOLT? (@1)').split(',')
        #sourceVolts = [item for item in sourceVolts for i in range(3)]
        #measCurr = [item for item in measCurr for i in range(3)]
        print(measCurr)
        print(len(measCurr))
        print(sourceVolts)
        print(len(sourceVolts))

        print("Foo4")

        smu.write(':OUTP OFF')
        VIBList = list(zip(sourceVolts,measCurr,brightCurr))
        return VIBList

def IVBSweepCurr(step, maxVolts, currList):
    rm = visa.ResourceManager()
    for i in rm.list_resources():
        if "0x0957" in i:
            B2901A_address = i
    for i in rm.list_resources():
        if "0x2A8D" in i:
            MM_34460_address = i
    smu = rm.open_resource(B2901A_address)
    mm = rm.open_resource(MM_34460_address)
    mm.timeout = 5000000
    smu.timeout = 5000000
    aperture = .04
    nplcTime = .2
    newSweep = 1
    listString = ','.join(str(x) for x in currList)
    if newSweep == 1:
        smu.write(":SOUR:FUNC:MODE CURR")
        smu.write(":SOUR:CURR:RANG 1e-2")
        smu.write(":SOUR:CURR:MODE LIST")
        smu.write(":SOUR:LIST:CURR {}".format(listString))

        mm.write('*RST')
        mm.write(':CONF:CURR:DC')
        mm.write(':CURR:DC:NPLC {}'.format(nplcTime))
        mm.write(':TRIG:COUN {}'.format(len(currList)))
        mm.write(':TRIG:SOUR EXT')
        mm.write(':TRIG:DEL .005')
        mm.write(':SAMP:SOUR TIM')
        mm.write(':SAMP:TIM 0.01')
        mm.write(':SAMP:COUN 1')
        mm.write(':INIT')

        smu.write(':SENS:FUNC ""VOLT""')
        smu.write(':SENS:VOLT:RANG:AUTO ON')
        smu.write(':SENS:VOLT:APER {}'.format(aperture))
        smu.write(':SENS:VOLT:PROT {}'.format(maxVolts))
        smu.write(':FORM:DATA ASC')
        smu.write(':TRIG:SOUR AINT')
        smu.write(':TRIG:TIM .1')
        smu.write(':TRIG:COUN {}'.format(len(currList)))
        smu.write(":TRIG:MEAS:DEL .005")
        smu.write(':OUTP ON')
        smu.write(":SOUR:TOUT:STAT ON")
        smu.write(":SOUR:TOUT:SIGN EXT3")
        smu.write(":SOUR:DIG:EXT3:FUNC DIO")
        smu.write(":SOUR:DIG:EXT3:TOUT:EDGE:POS BEF")
        smu.write(':INIT (@1)')

        brightCurr = mm.query(":FETC?").split(',')
        print(brightCurr)
        print(len(brightCurr))
        measCurr = smu.query(':FETC:ARR:CURR? (@1)').split(',')
        sourceVolts = smu.query(':FETC:ARR:VOLT? (@1)').split(',')
        #sourceVolts = [item for item in sourceVolts for i in range(3)]
        #measCurr = [item for item in measCurr for i in range(3)]
        print(measCurr)
        print(len(measCurr))
        print(sourceVolts)
        print(len(sourceVolts))

        smu.write(':OUTP OFF')
        VIBList = list(zip(sourceVolts,measCurr,brightCurr))
        return VIBList

# Executes a linear IV sweep and returns IV output
def LinSweepSMU(Vbegin, Vend, samplePoints, stepT, maxCurr):
    rm = visa.ResourceManager()
    for i in rm.list_resources():
        if "0x0957" in i:
            B2901A_address = i
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
    for i in rm.list_resources():
        if "0x0957" in i:
            B2901A_address = i
    for i in rm.list_resources():
        if "0x2A8D" in i:
            MM_34460_address = i
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
