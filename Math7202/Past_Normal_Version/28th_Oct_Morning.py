import math
import random
from gurobipy import *
random.seed (3)
def Distance(p1, p2):
  return int(math.hypot(p1[0] - p2[0], p1[1] - p2[1]) + 0.5)

nTrips = 100
nLocs = 100
nDepots = 5
nFuels = 5
Trips = range(nTrips)
Locs = range(nLocs)
Depots = range(nDepots)
Fuels = range(nFuels)

Square = 150
BusCost = 15000
ReFuelCharge = 500
FuelCapacity = 1000
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

#From tripi to trip j which fuel is used
#因为油耗的路程 正比 于时间， 油耗最小 在这个问题中，我们设定为 就是时间最小
Trip_Fuel_Trip = [[[Trip_FuelStationFuel[i][s]+FuelStation_TripFuel[s][j] for s in Fuels].index(min([Trip_FuelStationFuel[i][s]+FuelStation_TripFuel[s][j] for s in Fuels]))for j in Trips]for i in Trips]

Trip_Trip_Cost = [[[Trip_TripFuel[i][j], Trip_FuelStationFuel[i][Trip_Fuel_Trip[i][j]]+FuelStation_TripFuel[Trip_Fuel_Trip[i][j]][j]]for j in Trips]for i in Trips]
import time
start = time.clock()
#不谈油量，先耍流氓
# What trips can I reach if I start at depot d with trip k
CanReach = {(d,k):
    [k]+[t for t in Trips if all([k!=t,TripTime[t][0]-TripTime[k][1]>=Trip_TripTime[k][t]])]
    for d in Depots for k in Trips}

# If I started at depot d with trip k and I'm at trip t, what can I do next
Successors = {(d,k,t):
    [t2 for t2 in CanReach[d,k] 
     if TripTime[t2][0]-TripTime[t][1]>=Trip_TripTime[t][t2]]
    for (d,k) in CanReach for t in CanReach[d,k]}

    #Check if have time to fuel
def FuelTimeConstrain(LastTrip,NextTrip):
    FeasibleStation = Trip_Fuel_Trip[LastTrip][NextTrip]
    if TripTime[NextTrip][0]>=TripTime[LastTrip][1]+Trip_FuelStationTime[LastTrip][FeasibleStation]+FuelStation_TripTime[FeasibleStation][NextTrip]:
        return True
    return False
    
NoComplible = 13928372893
def Cost(d,tList,f,expense):
    if len(tList)>=2:
        LastTrip = tList[-2]
        NextTrip = tList[-1]
        #如果当前不需要加油就可以完成下一段trip
        if f>=Trip_TripFuel[LastTrip][NextTrip]+TripFuel[NextTrip]:
            expense = expense + TripFuel[NextTrip] + Trip_Trip_Cost[LastTrip][NextTrip][0]
            f = f - Trip_TripFuel[LastTrip][NextTrip] - TripFuel[NextTrip]
            return f,expense
            #Cost(d,tList[1:],f,expense)
        #如果需要加油且够时间完成下一段trip
        elif FuelTimeConstrain(LastTrip,NextTrip):
            expense = expense + ReFuelCharge + TripFuel[NextTrip] + Trip_Trip_Cost[LastTrip][NextTrip][1]
            f = FuelCapacity - FuelStation_TripFuel[Trip_Fuel_Trip[LastTrip][NextTrip]][NextTrip]
            return f,expense
            #Cost(d,tList[1:],f,expense)
        else:
            return 0,NoComplible
    else:
        NextTrip = tList[-1]
        expense = expense + TripFuel[NextTrip]
        f = f - TripFuel[NextTrip]
        return f,expense
        '''
        if f>=TripFuel[LastTrip]+Trip_DepotFuel[LastTrip][d]:
            expense = expense + TripFuel[LastTrip]+Trip_DepotFuel[LastTrip][d]
            return 0,expense
        '''
            
AllTours = {}

def Generate(d, Tour,f,expense):
    f,expense = Cost(d, Tour,f,expense)
    if expense==NoComplible or f<Trip_DepotFuel[Tour[-1]][d]:
        return
    AllTours[d,Tour] = expense + Trip_DepotFuel[Tour[-1]][d]
    # Short cut to get initial tours
    if len(Tour)>=2:
        return
    for t in Successors[d,Tour[0],Tour[-1]]:
        Generate(d, Tour+(t,),f,expense)

for d,k in CanReach:
    Generate(d, (k,),FuelCapacity-Depot_TripFuel[d][k],BusCost+Depot_TripFuel[d][k])
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
m.optimize()
def GenColumns():
    for d,i in CanReach:
        Short = [[(GRB.INFINITY,None) for FuelCondition in [0,1]]for _ in Trips]
        Short[i][0] = (BusCost+Depot_TripFuel[d][i]-Cover[i].pi,None)
        
        for j in CanReach[d,i]:
            
            for FuelCondition in [0,1]:
                if Short[j][FuelCondition][0]+Trip_DepotFuel[j][d] < -0.00001:
                    tCol = []
                    upto = j
                    while upto!=None:
                        tCol.append(upto)
                        upto = Short[upto][FuelCondition][1]
                    tCol.reverse()
                    print('New Column at j',d,tCol)
                    
            if min(Short[j][FuelCondition][0] for FuelCondition in [0,1])==GRB.INFINITY:
                print('Failed at',d,i,j)
                xxxxxxxx
            for t in Successors[d,i,j]:
                LastTrip = j
                NextTrip = t
                if TripTime[NextTrip][0]-TripTime[LastTrip][1]>=Trip_TripTime[LastTrip][NextTrip]:
                    tCost = Short[LastTrip][0][0]+Trip_Trip_Cost[LastTrip][NextTrip][0]-Cover[NextTrip].pi
                    if tCost<Short[t][0][0]:
                        Short[t][0]=(tCost,j)
        break
                    
GenColumns()    
                
# for k in Z:
#     if Z[k].x>0.01:
#         print(k,Z[k].x,AllTours[k])
        
# end = time.clock()
# print(end-start,'运行时间')