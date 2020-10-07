import os
import OLEDTools

os.chdir("C:\\Users\\Jerry\\Desktop\\PaulNiy")
paulList = OLEDTools.getSpectrum("190823Qz3_Subt2_00001.txt")

OLEDTools.writeOOSpectrum(paulList,"C190823Qz3.txt")