import os
import glob
import OLEDTools

os.chdir('C:\\Users\\Jerry\\IdeaProjects\\OceanOpticsSpectrum\\PLQ_200407_data_Mx\\Mx100\\rat2')
files = os.listdir(os.getcwd())
print(files)
for file in files:
    OLEDTools.quenchAnalyzePLwV("V",file,0,1,"V")
