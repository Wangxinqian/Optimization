import math
import random
from gurobipy import *
random.seed (3)
def Distance(p1, p2):
  return int(math.hypot(p1[0] - p2[0], p1[1] - p2[1]) + 0.5)

EPS = 0.00001

nTrips = 60
nLocs = 150
nDepots = 5
nFuels = 5
Trips = range(nTrips)
Locs = range(nLocs)
Depots = range(nDepots)
Fuels = range(nFuels)

Square = 150
BusCost = 15000
ReFuelCharge = 500
FuelCapacity = 600
DepotCapacity = 20

# Set up random locations but set some of the positions to be corners
# of the grid.  The depots are the first nDepots positions
Pos = [(random.randint(0,Square), random.randint(0,Square)) for i in Locs]
Pos[0] = (0,0)
Pos[1] = (Square,Square)
Pos[2] = (0, Square)
Pos[3] = (Square, 0)
Pos[4] = (Square/2, Square/2)
D = [[Distance(Pos[i], Pos[j]) for j in Locs] for i in Locs]

TripLoc = [(random.choice(Locs), random.choice(Locs)) for i in Trips]
FuelLoc = [(random.choice(Locs)) for i in Fuels]
DepotLoc = [(random.choice(Locs)) for i in Depots]

def GenerateTimes_Fuel(i):
  # Generate a start and end time for a trip
  start = random.randint(240,1440 - D[TripLoc[i][0]][TripLoc[i][1]] - 60)
  end = start + D[TripLoc[i][0]][TripLoc[i][1]] + random.randint(0,30)
  return (start, end, 2*(D[TripLoc[i][0]][TripLoc[i][1]]))

#Trip i
TripTime = [GenerateTimes_Fuel(i)[:-1] for i in Trips]

#AverageWorkingTime = sum(i[1]-i[0] for i in TripTime)/len(TripTime)
#BreakInterval = int(AverageWorkingTime*0.3)
BreakInterval=10

TripFuel = [GenerateTimes_Fuel(i)[-1] for i in Trips]
TripData = sorted((tt,tl,tf) for (tt,tl,tf) in zip(TripTime,TripLoc,TripFuel))
TripTime = [tt for (tt,_,_) in TripData]
TripLoc = [tl for (_,tl,_) in TripData]
TripFuel = [tf for (_,_,tf) in TripData]

#Trip i 到 Trip j
Trip_TripFuel = [[2*D[TripLoc[i][1]][TripLoc[j][0]] for j in Trips] for i in Trips]
Trip_TripTime = [[D[TripLoc[i][1]][TripLoc[j][0]] for j in Trips] for i in Trips]

#Trip i 到 Depot
Trip_DepotFuel = [[2*D[TripLoc[i][1]][DepotLoc[j]] for j in Depots] for i in Trips]
Trip_DepotTime = [[D[TripLoc[i][1]][DepotLoc[j]] for j in Depots] for i in Trips]

#Trip i 到 FuelStation
Trip_FuelStationFuel = [[2*D[TripLoc[i][1]][FuelLoc[j]] for j in Fuels] for i in Trips]
Trip_FuelStationTime = [[D[TripLoc[i][1]][FuelLoc[j]] for j in Fuels] for i in Trips]

#Fuel Station to Trip i 
FuelStation_TripFuel = [[2*D[FuelLoc[i]][TripLoc[j][0]] for j in Trips] for i in Fuels]
FuelStation_TripTime = [[D[FuelLoc[i]][TripLoc[j][0]] for j in Trips] for i in Fuels]

#Fuel Station to Depot
FuelStation_DepotFuel = [[2*D[FuelLoc[i]][DepotLoc[j]] for j in Depots] for i in Fuels]
FuelStation_DepotTime = [[D[FuelLoc[i]][DepotLoc[j]] for j in Depots] for i in Fuels]

#Depot to Trip i 
Depot_TripFuel = [[2*D[DepotLoc[i]][TripLoc[j][0]] for j in Trips] for i in Depots]
Depot_TripTime = [[D[DepotLoc[i]][TripLoc[j][0]] for j in Trips] for i in Depots]

# Check if need to refuel
#def checknext(d,k,):

# Start time from depot d
#StartDep = [[TripTime[t][0]-D[d][TripLoc[t][0]] for d in Depots] for t in Trips]
# End time at depot d
#EndDep = [[TripTime[t][1]+D[TripLoc[t][1]][d] for d in Depots] for t in Trips]


# What trips can I reach if I start at depot d with trip k
#First Filter
import time
start = time.clock()

#如果我在trip k 准备去 trip t
def CanFuel(k,t,f):
    # 我不能再回过去k 开一遍 且 我不能开 时间上不满足的
    if k!=t and TripTime[t][0]-TripTime[k][1]-BreakInterval>=Trip_TripTime[k][t]:
        #油刚好够，不去加油，就去trip t,返回(t,结束t后的油量)
        if TripFuel[t] + Trip_TripFuel[k][t] + min(Trip_FuelStationFuel[t][station] for station in Fuels) <= f:
            f=f-TripFuel[t]-Trip_TripFuel[k][t]
            return (t,f)
        else:
            #去加油
            Station_list = []
            for station in Fuels:
                # trip t 开始时间 大于 trip k到加油站的时间 加上 从加油站开到 trip t的时间
                if TripTime[t][0] - Trip_FuelStationTime[k][station] - FuelStation_TripTime[station][t] -BreakInterval>= 0:
                    #油量能到
                    if f >= Trip_FuelStationFuel[k][station]:
                        #且加完油跑完trip-t 之后可以去下一个加油站
                        if FuelStation_TripFuel[station][t] <= FuelCapacity - TripFuel[t] - min(Trip_FuelStationFuel[t][s] for s in Fuels):
                            f=FuelCapacity - FuelStation_TripFuel[station][t] - TripFuel[t]
                            Station_list.append((FuelStation_TripFuel[station][t],t,station,f))
            if len(Station_list)>0:
                return min(Station_list)
            return False
    return False

#Trips 这边可以优化，我们不用每次遍历 所有Trips
def CanFuel_Decomposition(Trips,k,f):
    kd = []
    for t in Trips:
        Judge = CanFuel(k,t,f)
        if Judge != False:
            if len(Judge)==2:
                kd.append([Judge[0],Judge[-1]]) #返回 trip t  和  开完后剩下的油量
            elif len(Judge)==4:
                kd.append([Judge[1],Judge[2],Judge[-1]])
            else:
                xxxxxxxxxx
    return kd


CanReach = {(d,k):
    [[k,FuelCapacity-Depot_TripFuel[d][k]-TripFuel[k]]]
    +[r for r in CanFuel_Decomposition([i for i in Trips],k,FuelCapacity-Depot_TripFuel[d][k]-TripFuel[k])]
    for d in Depots for k in Trips if TripFuel[k] <= FuelCapacity-Depot_TripFuel[d][k]
                                        and min(Trip_FuelStationFuel[k][station] for station in Fuels)<=FuelCapacity-Depot_TripFuel[d][k]-TripFuel[k]}
    
AllTours = {}
def Generate(Tour,d):
    #开了太多路程了
    if len(Tour)>2:
        return False
    ##能够回去 从哪里来 回哪里去
    # if Tour[-1][-1]< Trip_DepotFuel[Tour[-1][0]][d] and len(Tour)>2:
    #     return False
    # if TripTime[Tour[-1][0]][1]+max(Trip_DepotTime[Tour[-1][0]][j] for j in Depots)>1550:
    #     return False
    k = ()
    cost = BusCost
    for x in Tour:
        k = k + (x[0],)
        if len(x)==2:
            cost = cost + FuelCapacity - x[-1]
        else:
            cost = cost + FuelCapacity - x[-1] + ReFuelCharge
    cost = BusCost
    AllTours[d,k] = cost + 800*len(k)
    # #Like a filter
    if (d,k[-1]) in CanReach and len(CanReach[d,k[-1]]) > 1:
        TTTTT = [i[0] for i in CanReach[d,k[-1]][1:]]
        for r in CanFuel_Decomposition(TTTTT,Tour[-1][0],Tour[-1][-1]):
            Generate(Tour+(r,),d)
    
    # # Slowest
    # for r in CanFuel_Decomposition(Trips,Tour[-1][0],Tour[-1][-1]):
    #     Generate(Tour+(r,),d)

for d,k in CanReach:
    for j in CanReach[d,k]:
        if j[0]==k:
            Tour = (j,)
        else:
            Tour = (CanReach[d,k][0],j)
        Generate(Tour,d)
    print(d,k,len(AllTours))

m = Model('ColGen')

Z = {k: m.addVar() for k in AllTours}

m.setObjective(quicksum(AllTours[k]*Z[k] for k in Z))

VarsForT = {t:[] for t in Trips}
for k in Z:
    for t in k[1]:
        VarsForT[t].append(Z[k])

Cover = {t:
    m.addConstr(quicksum(VarsForT[t])==1)
    for t in Trips}

m.setParam('MIPGap', 0)

def GenColumns():
    Added = 0
    for d,k in CanReach:
        Short = [(GRB.INFINITY,None) for _ in Trips]
        v = CanReach[d,k][0]
        if len(CanReach[d,k][0])==2:
            Short[k] = (BusCost+800-Cover[k].pi,(v,))
        elif len(CanReach[d,k][0])==3:
            Short[k] = (BusCost+800+ReFuelCharge-Cover[k].pi,(v,))
        else:
            xxxxxxxxxxx
        for j in CanReach[d,k]:
            if Short[j[0]][0]< -EPS:
                tCol = Short[j[0]][1]
                kk = ()
                cost = BusCost
                for x in tCol:
                    kk = kk + (x[0],)
                    if len(x)==2:
                        cost = BusCost + 800*len(kk)
                    elif len(x)==3:
                        cost = BusCost + 800*len(kk)
                    else:
                        print(tCol,'ddddd')
                if cost==BusCost:
                    xxxxxxxxx
                if (d,kk) in Z:
                    xxxxxxxxxxxxxxxxxxx
                Z[(d,kk)] = tVar = m.addVar(obj=cost)
                for tt in tCol:
                    m.chgCoeff(Cover[tt[0]],tVar,1)
                Added += 1
            for r in CanFuel_Decomposition(Trips,j[0],j[-1]):
                # if r==[14, 250]:
                #     print(j,d,k,CanReach[d,k])
                #     xxxxxxxxxxxx
                if len(r)==2:
                    tCost = Short[j[0]][0]+r[-1]-Cover[r[0]].pi
                    if tCost < Short[r[0]][0]:
                        Short[r[0]] = (tCost,Short[j[0]][1]+(r,))
                elif len(r)==3:
                    tCost = Short[j[0]][0]+r[-1]-Cover[r[0]].pi
                    if tCost < Short[r[0]][0]:
                        Short[r[0]] = (tCost,Short[j[0]][1]+(r,))
                else:
                    CRASH
                
    # xxxxxxxxxxxxxxxx
    return Added

m.setParam("OutputFlag",0)
while True:
    m.optimize()
    print('Obj val:', m.objVal)
    Added = GenColumns()
    print(Added)
    if Added == 0:
        break
for v in m.getVars():
    v.vtype = GRB.BINARY
for v in m.getVars():
    v.lb = 0
m.optimize()
print('Obj val:', m.objVal)
for k in Z:
    if Z[k].x>0.01:
        print(k,Z[k].x)