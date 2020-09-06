import os
import glob
import OLEDTools
import csv

# Format for mobility extraction

os.chdir('C:\\Users\\Jerry\\IdeaProjects\\OceanOpticsSpectrum\\f')
files = os.listdir(os.getcwd())
print(files)
for file in files:
    with open(file, 'r') as readFile:
        lines = readFile.read().splitlines()

    stringData = [x for x in lines if x != '']
    stringData = stringData[:-5]
    stringData.pop(0)

    currData = [abs(float(x.split(',')[0])) for x in stringData]
    voltData = [float(x.split(',')[1]) for x in stringData]
    ratioData = [float(x.split(',')[2]) for x in stringData]
    stitchedData = list(zip(currData, voltData, ratioData))

    xs = list(zip(*stitchedData))[1]
    ys = list(zip(*stitchedData))[0]
    zs = list(zip(*stitchedData))[2]
    data = list(zip(xs,ys,zs))
    with open(file.strip(".csv")+"_RatioMobility.csv", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        row1 = ["Voltage (V)", "Drive Current (A)", "PL Ratio"]
        writer.writerow(row1)
        for row in data:
            writer.writerow(row)
