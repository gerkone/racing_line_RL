from math import cos, sin, atan, tan, sqrt
import numpy as np

class Vehicle(object):
    def __init__(self, maxMa=1, maxDelta=0.3):
        self._x = 0     #x position
        self._y = 0     #y positionx
        self._dotx = 0  #x velocity
        self._doty = 0  #y velocity
        self._beta = 0  #angle of the velocity from the car assex
        self._delta = 0 #angle of the front wheel from the car assex
        self._psi = 0   #angle of the car assex from the x assex
        self._dotpsi = 0
        self._alpha = 0 #wheel rolling angle
        self._Ma = 0    #Motor accelleration
        self._Vx = 0
        self._Vy = 0
        self._maxMa = maxMa
        self._maxDelta = maxDelta
        self._massa = 1000 #vehicle mass
        self._LF = 1.5 #distance from front assex
        self._LR = 1.5 #distance from rear assex
        self._wheelRadius = 0.4 #wheel radius
        self._previewsx = 0 #x position in the previous integration
        self._previewsy = 0 #y position in the previews integration

    #Mettere a posto
    def integrate(self, dt):
        self.Vx = self._dotx*cos(self._psi)+self._doty*sin(self._psi)
        self.Vy = self._doty*cos(self._psi)-self._dotx*sin(self._psi)
        self.Vx = self._Ma*dt + self.Vx
        self._dotx = self.Vx*cos(self._psi) - self.Vy*sin(self._psi)
        self._doty = self.Vx*sin(self._psi) + self.Vy*cos(self._psi)
        self._beta = atan(tan(self._delta)/2)
        v = sqrt(self._dotx*self._dotx + self._doty*self._doty)
        self.alpha = v*dt/self._wheelRadius
        self._dotpsi = v/0.03*sin(self._beta)
        self._psi = self._dotpsi*dt + self._psi
        self._dotx = v*cos(self._beta+self._psi)
        self._doty = v*sin(self._beta+self._psi)
        self._previewsx = self._x
        self._previewsy = self._y
        self._x = self._dotx*dt + self._x
        self._y = self._doty*dt + self._y

    def setAcceleration(self, MaCoff):          #MaCoff is a value between -1 and 1
        if MaCoff>1:
            MaCoff = 1
        elif MaCoff<-1:
            MaCoff = -1
        self._Ma = MaCoff*self._maxMa

    def setSteering(self, deltaCoff):    #deltaCoff is a value between -1 and 1
        if deltaCoff>1:
            deltaCoff = 1
        elif deltaCoff<-1:
            deltaCoff = -1
        self._delta = deltaCoff*self._maxDelta

    def littleSteeringLeft(self):
        deltaCoff = self._delta/self._maxDelta
        deltaCoff -= 0.005
        if deltaCoff>1:
            deltaCoff = 1
        elif deltaCoff<-1:
            deltaCoff = -1
        self._delta = deltaCoff*self._maxDelta

    def littleSteeringRight(self):
        deltaCoff = self._delta/self._maxDelta
        deltaCoff += 0.005
        if deltaCoff>1:
            deltaCoff = 1
        elif deltaCoff<-1:
            deltaCoff = -1
        self._delta = deltaCoff*self._maxDelta

    def littleAccelleration(self):
        MaCoff = self._Ma/self._maxMa
        MaCoff += 0.01
        if MaCoff>1:
            MaCoff = 1
        elif MaCoff<-1:
            MaCoff = -1
        self._Ma = MaCoff*self._maxMa

    def littleDecelleration(self):
        MaCoff = self._Ma/self._maxMa
        MaCoff -= 0.05
        if MaCoff>1:
            MaCoff = 1
        elif MaCoff<-1:
            MaCoff = -1
        self._Ma = MaCoff*self._maxMa

    def getVelocities(self):
        return [self.Vx, self.Vy]

    def getPosition(self):
        return [self._x, self._y]

    def getAngles(self):
        return [self._psi, self._delta]

    def reset(self, x0, y0, psi0):
        self._x = x0;
        self._y = y0;
        self._psi = psi0

    def CalcPacejkaFront(self):
        B = 10  #10 Dry, 12 Wet, 5 Snow, 4 Ice
        C = 1.3 #1.9 Dry, 2.3 Wet, 2 Snow, 2 Ice (1.3 is the defaul value for the lateral force)
        D = 1   #1 Dry, 0.82 Wet, 0.3 Snow, 0.1 Ice
        E = 0.97 #0.97 Dry, 1 Wet, 1 Snow, 1 Ice
        if self._Vx == 0:
            slip = 0
        else:
            slip = (self._wheelRadius*self._alpha-self._Vx)/(abs(self._Vx))
        return D*self._massa*4.905*self._LR/(self._LR+self._LF)*sin(C*atan(B*slip-E*(B*slip-atan(B*slip))))

    def CalcPacejkaRear(self):
        B = 10  #10 Dry, 12 Wet, 5 Snow, 4 Ice
        C = 1.3 #1.9 Dry, 2.3 Wet, 2 Snow, 2 Ice
        D = 1   #1 Dry, 0.82 Wet, 0.3 Snow, 0.1 Ice
        E = 0.97 #0.97 Dry, 1 Wet, 1 Snow, 1 Ice
        if self._Vx == 0:
            slip = 0
        else:
            slip = (self._wheelRadius*self._alpha-self._Vx)/(abs(self._Vx))
        return D*self._massa*4.905*self._LF/(self._LR+self._LF)*sin(C*atan(B*slip-E*(B*slip-atan(B*slip))))

    def define_circle(p1, p2, p3):
        temp = p2[0] * p2[0] + p2[1] * p2[1]
        bc = (p1[0] * p1[0] + p1[1] * p1[1] - temp) / 2
        cd = (temp - p3[0] * p3[0] - p3[1] * p3[1]) / 2
        det = (p1[0] - p2[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p2[1])

        if abs(det) < 1.0e-6:
            return (None, np.inf)

        # Center of circle
        cx = (bc*(p2[1] - p3[1]) - cd*(p1[1] - p2[1])) / det
        cy = ((p1[0] - p2[0]) * cd - (p2[0] - p3[0]) * bc) / det

        radius = np.sqrt((cx - p1[0])**2 + (cy - p1[1])**2)
        return radius

v = Vehicle();
v.CalcPacejkaFront()
v.CalcPacejkaRear()
