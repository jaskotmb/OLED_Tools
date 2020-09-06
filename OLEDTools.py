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
import matplotlib.pyplot as plt


def multipleQuenchPlot(JorV, fileList, cols, JorVsource):
    for i in range(len(fileList)):
        datatemp = quenchAnalyzePLwV('V', fileList[i], 0, 0, JorVsource)
        if JorV == "J":
            xs = list(zip(*datatemp))[0]
        if JorV == "V":
            xs = list(zip(*datatemp))[1]
        ys = list(zip(*datatemp))[2]
        if JorV == "J":
            plt.semilogx(xs, ys, linestyle="", marker="o", color=cols[i])
            plt.xlabel('Drive Current (A)')
            plt.xlim(.9e-7,1e-2)
        if JorV == "V":
            plt.plot(xs, ys, linestyle="", marker="o", color=cols[i])
            plt.xlabel('Voltage (V)')
            plt.xlim(0,20)
        plt.ylim(0.7,1.01)
        plt.ylabel('Normalized PL')
    plt.show()

def quenchAnalyzePLwV(JorV, filename, plotting, outPutFile, JorVsource):
    with open(filename, 'r') as readFile:
        lines = readFile.read().splitlines()

    stringData = [x for x in lines if x != '']
    stringData = stringData[:-5]
    currData = [abs(float(x.split(',')[0])) for x in stringData]
    voltData = [float(x.split(',')[1]) for x in stringData]
    intensData = [float(x.split(',')[2]) for x in stringData]
    stitchedData = list(zip(currData, voltData, intensData))

    indexBreaks = [0]
    currBreaks = []
    voltBreaks = []
    for i in range(1, len(stitchedData)):
        if(JorVsource == "V"):
            indexTest = 1
        if(JorVsource == "J"):
            indexTest = 0
        if round(stitchedData[i][indexTest], 2) != round(stitchedData[i - 1][indexTest], 2):
            indexBreaks.append(i)
            currBreaks.append(round(stitchedData[i - 1][0], 7))
            voltBreaks.append(round(stitchedData[i - 1][1], 7))
    #print(indexBreaks)

    totalDataAvg = []
    onOrOff = 0
    xnumFront = 1
    xnumEnd = 1
    for k in range(len(indexBreaks) - 1):
        meanData = 0
        if onOrOff%2 == 1: #this means current is on
            for i in range(indexBreaks[k], indexBreaks[k + 1]):
                meanData = meanData + stitchedData[i][2]
            meanData = meanData - stitchedData[indexBreaks[k]][2] - stitchedData[indexBreaks[k + 1] - 1][2]
            # above line subtracts out first and last points in measurement series
            avgdPts = (indexBreaks[k + 1] - indexBreaks[k] - 2)
            if avgdPts == 0:
                avgdPts = 1
            meanData = meanData / avgdPts  # divide by number of elements for mean value
            totalDataAvg.append(meanData)
        if onOrOff%2 == 0: #this means current is off
            for i in range(indexBreaks[k], indexBreaks[k + 1]):
                meanData = meanData + stitchedData[i][2]
            #print(stitchedData[indexBreaks[k+1]-1][2])
            for m in range(1,xnumEnd+1):
                #print("subtracting: {}".format(stitchedData[indexBreaks[k+1]-m][2]))
                meanData = meanData - stitchedData[indexBreaks[k+1]-m][2]
                #print(meanData)
            for m in range(0,xnumFront):
                meanData = meanData - stitchedData[indexBreaks[k]+m][2]
            # above lines subtract out first xnumFront and last xnumEnd points in measurement series
                #print("subtracting: {}".format(stitchedData[indexBreaks[k]+m][2]))
                #print(meanData)
            avgdPts = (indexBreaks[k + 1] - indexBreaks[k] - xnumEnd - xnumFront)
            if avgdPts == 0:
                avgdPts = 1
            print(avgdPts)
            meanData = meanData / avgdPts  # divide by number of elements for mean value
            totalDataAvg.append(meanData)
        onOrOff = onOrOff + 1
        if plotting == 2:
            print("Pulse: {:4}, Current: {:5.2}mA, Mean Intensity: {:8.6}, Averaged Points: {:2}".format(k, currBreaks[
                k] * 1e3,meanData,avgdPts))

    totalData = list(zip(currBreaks, voltBreaks, totalDataAvg))
    ratio = []
    ratioCurr = []
    ratioVolt = []
    for i in range(1, len(totalData)):
        if (totalData[i-1][2]) != 0:
            ratio.append(totalData[i][2] / totalData[i - 1][2])
            ratioCurr.append(totalData[i][0])
            ratioVolt.append(totalData[i][1])
    ratioList = []
    ratioListTemp = list(zip(ratioCurr, ratioVolt, ratio))
    for i in range(len(ratioListTemp)):
        if ratioListTemp[i][0] != 0:
            ratioList.append(ratioListTemp[i])
    if plotting == 2:
        print(ratioList)

    if (plotting == 1 or plotting == 2) and (JorV == 'J'):
        xs = list(zip(*ratioList))[0]
        ys = list(zip(*ratioList))[2]
        plt.semilogx(xs, ys, linestyle="", marker="o")
        plt.xlabel('Drive Current (A)')
        plt.ylabel('Normalized PL')
        plt.title(filename)
        plt.show()

    if (plotting == 1 or plotting == 2) and (JorV == 'V'):
        xs = list(zip(*ratioList))[1]
        ys = list(zip(*ratioList))[2]
        plt.plot(xs, ys, linestyle="", marker="o")
        plt.xlabel('Voltage (V)')
        plt.ylabel('Normalized PL')
        plt.title(filename)
        plt.show()

    if outPutFile == 1:
        xs = list(zip(*ratioList))[0]
        ys = list(zip(*ratioList))[1]
        zs = list(zip(*ratioList))[2]
        data = list(zip(xs,ys,zs))
        with open(filename.strip(".csv")+"_Ratio.csv", 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            row1 = ["Drive Current (A)", "Voltage (V)", "PL Ratio"]
            writer.writerow(row1)
            for row in data:
                writer.writerow(row)
    return ratioList


def integrateSpectrum(wavelengthList, intensityList, minWvl, maxWvl):
    relevantWvls = [x for x in wavelengthList if x > minWvl and x < maxWvl]
    for index in range(len(intensityList)):
        if relevantWvls[0] == wavelengthList[index]:
            break
    relevantIntens = intensityList[index:index + len(relevantWvls)]
    auc = scipy.integrate.cumtrapz(relevantIntens, relevantWvls)
    intBegin = relevantWvls[0]
    intEnd = relevantWvls[len(relevantWvls) - 1]
    intAvg = auc[len(auc) - 1] / (intEnd - intBegin)
    # print("Integration from {} to {} = {}".format(intBegin,intEnd,intSum)))
    return [intAvg, intBegin, intEnd]


def getSpectrum(fileName):
    # given a filename for an OO spectrum file, returns [(wavelength, intensity),...] tuple list

    file = open(fileName, "r")
    header = []
    begchar = ''
    while begchar != '>':
        temp = file.readline()
        header.append(temp)
        begchar = temp[0]

    fname = header[0].split('from ')[1].split(' ')[0]
    # print("Filename: {}".format(fname))
    date = header[2].split(': ')[1].split('\n')[0]
    # print("Date: {}".format(date))
    inttime = float(header[6].split(': ')[1].split('\n')[0])
    # print("Integration Time: {} seconds".format(inttime))
    scansavg = header[7].split(': ')[1].split('\n')[0]
    # print("Scans Averaged: {}".format(scansavg))

    wvl = []
    intens = []
    line = "Test"
    for line in file:
        lsplit = line.split('\t')
        wvl.append(float(lsplit[0]))
        intens.append(float(lsplit[1].split('\n')[0]))

    return list(zip(wvl, intens))


def iDevice():
    rm = visa.ResourceManager()
    B2901A = rm.list_resources()[0]
    smu = rm.open_resource(B2901A)
    smu.write("*RST")
    print("SMU: {}".format(smu.query("*IDN?")))


def currDecay(sourceCurrent, maxTime):
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

    while (tRun.seconds < maxTime):
        voltList.append(smu.query(":MEAS:VOLT?").split('\n')[0])
        currList.append(smu.query(":MEAS:CURR?").split('\n')[0])
        brightTemp = mm.query(":MEAS:CURR?").split('\n')[0]
        brightList.append(brightTemp)
        if float(brightTemp) < .005e-6:
            print("No Output! Breaking Decay Loop...")
            ret = "fail"
            break
        tRun = datetime.datetime.now() - tbegin
        timeList.append(tRun.seconds + (1E-6) * tRun.microseconds)
        time.sleep(twait)
    smu.write(":OUTP OFF")
    outList = list(zip(timeList, voltList, currList, brightList))
    smu.write(":OUTP OFF")
    if ret != "fail":
        return outList
    if ret == "fail":
        return "fail"


def biasVoltsTime(totalTime, bias):
    rm = visa.ResourceManager()
    B2901A_address = rm.list_resources()[0]
    MM_34460_address = rm.list_resources()[1]
    smu = rm.open_resource(B2901A_address)
    smu.timeout = 5000000
    print("Reverse Biasing at {}V for {}sec".format(bias, totalTime))
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
    while (tRun.seconds < totalTime):
        smu.query(":MEAS:CURR?")
        tRun = datetime.datetime.now() - tbegin
        time.sleep(twait)
    smu.write(':OUTP OFF')


def findTurnOnVoltage(Vbegin, Vend, stepVolts, maxCurr, brThreshold):
    # Does Linear sweep until V_TurnOn, then returns linear data with V_TurnOn as last data point
    rm = visa.ResourceManager()
    B2901A_address = rm.list_resources()[0]
    MM_34460_address = rm.list_resources()[1]
    smu = rm.open_resource(B2901A_address)
    mm = rm.open_resource(MM_34460_address)
    step = abs(round((Vend - Vbegin) / stepVolts)) + 1
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
    if [x for x in brightCurr if float(x) > brThreshold]:
        indexThr = brightCurr.index([x for x in brightCurr if float(x) > brThreshold][0])
        print("indexThr = {}".format(indexThr))
        print("brightCurr at this index = {}".format(brightCurr[indexThr]))
        print("sourceVolts at this index = {}".format(sourceVolts[indexThr]))
    else:
        print("Turn-on Voltage not in range!")

    smu.write(':OUTP OFF')
    VIBList = list(zip(sourceVolts, measCurr, brightCurr))
    if [x for x in brightCurr if float(x) > brThreshold]:
        return sourceVolts[indexThr]


def IVBSweep(step, maxCurr, voltList):
    rm = visa.ResourceManager()
    B2901A_address = rm.list_resources()[0]
    MM_34460_address = rm.list_resources()[1]
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
        # sourceVolts = [item for item in sourceVolts for i in range(3)]
        # measCurr = [item for item in measCurr for i in range(3)]
        print(measCurr)
        print(len(measCurr))
        print(sourceVolts)
        print(len(sourceVolts))

        print("Foo4")

        smu.write(':OUTP OFF')
        VIBList = list(zip(sourceVolts, measCurr, brightCurr))
        return VIBList


def IVBSweepCurr(step, maxVolts, currList):
    rm = visa.ResourceManager()
    B2901A_address = rm.list_resources()[0]
    MM_34460_address = rm.list_resources()[1]
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
        # sourceVolts = [item for item in sourceVolts for i in range(3)]
        # measCurr = [item for item in measCurr for i in range(3)]
        print(measCurr)
        print(len(measCurr))
        print(sourceVolts)
        print(len(sourceVolts))

        smu.write(':OUTP OFF')
        VIBList = list(zip(sourceVolts, measCurr, brightCurr))
        return VIBList


# Executes a linear IV sweep and returns IV output
def LinSweepSMU(Vbegin, Vend, samplePoints, stepT, maxCurr):
    rm = visa.ResourceManager()
    B2901A_address = rm.list_resources()[0]
    smu = rm.open_resource(B2901A_address)
    totalTime = (stepT + .005) * samplePoints
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
    VIpairs = list(zip(sourceVolts, measCurr))
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
        print("Created Directory for today: {}\\{}".format(os.getcwd(), todayName))
    os.chdir(todayName)
    print("Changed Directory to: {}".format(os.getcwd()))
    return

def writeOOSpectrum(tupleList, fn):
    with open(fn, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        row1 = ["Wavelength (nm)","Intensity"]
        writer.writerow(row1)
        for row in tupleList:
            writer.writerow(row)

# Outputs IV data to a .csv
def writeMobility(fn, data):
    with open(fn, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        row1 = ["Voltage (V)", "Current (A)"]
        writer.writerow(row1)
        for row in data:
            writer.writerow(row)


# Outputs IV-Brightness data to a .csv
def writeIVB(fn, data):
    with open(fn, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        row1 = ["Voltage (V)", "Current (A)", "Brightness Current (A)"]
        writer.writerow(row1)
        for row in data:
            writer.writerow(row)


# Outputs IV-Brightness Decay data to a .csv
def writeIVBDecay(fn, data):
    with open(fn, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        row1 = ["Time (sec)", "Voltage (V)", "Current (A)", "Brightness Current (A)"]
        writer.writerow(row1)
        for row in data:
            writer.writerow(row)

def formatTRPL(bin_wave,vpos,vscale,voff):
    import numpy as np
    # Condition 2-byte data
    bin_wave2 = [0]*len(bin_wave)
    for i in range(1,len(bin_wave)):
        if i%2:
            bin_wave2[i] = bin_wave2[i] + bin_wave[i]*256
        if not(i%2):
            bin_wave2[i-1] = bin_wave2[i-1] + bin_wave[i]
    bin_wave3 = [v for i, v in enumerate(bin_wave2) if i%2==1]

    # create scaled vectors
    # horizontal (time)

    # vertical (voltage)
    unscaled_wave = np.array(bin_wave3, dtype='double') # data type conversion
    scaled_wave = (unscaled_wave - vpos) * vscale + voff
    return scaled_wave


def npArrayWriteCsv(filename,xList,yList,header):
    pyList = yList.tolist()
    pyList = zip(xList,[str(x) for x in pyList])
    with open(filename,'w',newline='') as outFile:
        wr = csv.writer(outFile)
        wr.writerow([header])
        for item in pyList:
            wr.writerow(item)
