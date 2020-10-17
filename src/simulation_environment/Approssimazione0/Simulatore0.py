from math import cos, sin, atan, tan, sqrt

MAMAX = 1       #m/s^2
DELTAMAX = 1    #rad = 57°

class Motorcycle:
    def __init__(self, Ma, delta):
        self._x = 0     #x position
        self._y = 0     #y positionx
        self._dotx = 0  #x velocity
        self._doty = 0  #y velocity
        self._beta = 0  #angle of the velocity from the car assex
        self._delta = 0 #angle of the front wheel from the car assex
        self._psi = 0   #angle of the car assex from the x assex
        self._dotpsi = 0
        self._Ma = 0    #Motor accelleration
        self.setMa(Ma)
        self.setDelta(delta)
    
    def Integrate(self, t):
        dotX = self._dotx*cos(self._psi)+self._doty*sin(self._psi)
        dotY = self._doty*cos(self._psi)-self._dotx*sin(self._psi)
        dotX = self._Ma*dt + dotX
        self._dotx = dotX*cos(self._psi) - dotY*sin(self._psi)
        self._doty = dotX*sin(self._psi) + dotY*cos(self._psi)
        self._beta = atan(tan(self._delta)/2)
        v = sqrt(self._dotx*self._dotx + self._doty*self._doty)
        self._dotpsi = v/0.03*sin(self._beta)
        self._psi = self._dotpsi*dt + self._psi
        self._dotx = v*cos(self._beta+self._psi)
        self._doty = v*sin(self._beta+self._psi)
        self._x = self._dotx*dt + self._x
        self._y = self._doty*dt + self._y
    
    def setMa(self, MaCoff):          #MaCoff is a value between -1 and 1
        if MaCoff>1:
            MaCoff = 1
        elif MaCoff<-1:
            MaCoff = -1
        self._Ma = MaCoff*MAMAX
    
    def setDelta(self, deltaCoff):    #deltaCoff is a value between -1 and 1
        if deltaCoff>1:
            deltaCoff = 1
        elif deltaCoff<-1:
            deltaCoff = -1
        self._delta = deltaCoff*DELTAMAX;


#Examples:
print("Examples:")
print("18 degrees of inclination and costant acceleration for 10 step")
print("-29 degrees of inclination and 0 acceleration for 10 step")
print("--------------------------------------")
m1 = Motorcycle(0.1, 0.3)
dt = 0.01

for i in range(1,10):
    print("s[",i,"] = ", end="")
    print("(", end="")
    print(m1._x, m1._y, sep=", ", end="")
    print(")")
    m1.Integrate(dt)
m1.setMa(0)
m1.setDelta(-0.5)
for i in range(1,10):
    print("s[",i,"] = ", end="")
    print("(", end="")
    print(m1._x, m1._y, sep=", ", end="")
    print(")")
    m1.Integrate(dt)
print("Auf Wiedersehen!")
