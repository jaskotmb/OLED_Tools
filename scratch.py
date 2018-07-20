Vstart = 1
Vend = 10
step = .5
countList = []
countTemp = Vstart
for i in range(int(1+(Vend-Vstart)/step)):
    countList.append(countTemp)
    countTemp = countTemp + step
print(countList)

