from math import cos, sin, atan, tan, sqrt
import numpy as np

class Vehicle(object):
    def __init__(self, maxMa=6, maxDelta=1):
        self._x = 0     #x position street R.S.
        self._y = 0     #y position street R.S.
        self._dotx = 0  #x velocity street R.S.
        self._doty = 0  #y velocity street R.S.

        self._beta = 0  #angle between the velocity and the car assex
        self._delta = 0 #angle between the front wheel and the car assex
        self._dotdelta = 0 #delta angular speed
        self._psi = 0   #angle of the car assex from the x assex
        self._dotpsi = 0 #psi angular speed
        self._Ma = 0    #motor acceleration
        self._Vx = 0 #x velocity car R.S.
        self._Vy = 0 #y velocity car R.S.
        self._maxMa = maxMa #maximum motor acceleration
        self._maxDelta = maxDelta #maximum delta angol
        self._massa = 10 #vehicle mass
        self._LF = 1.5 #distance from front assex
        self._LR = 1.5 #distance from rear assex
        self._wheelRadius = 0.4 #wheel radius
        self._previewsx = 0 #x position in the previous integration
        self._previewsy = 0 #y position in the previous integration
        self._slipF = 0 #slip angle front wheel
        self._slipR = 0 #slip angle rear wheel

    def integrate(self, dt):
        #evaluation of velocities on the car assix and normal of the car assix
        self._Vx = self._dotx*cos(self._psi)+self._doty*sin(self._psi)
        self._Vy = self._doty*cos(self._psi)-self._dotx*sin(self._psi)

        #evaluation of slip angles
        if self._Vx==0:
            self._slipF = 0
            self._slipR = 0
        else:
            self._slipF = atan((self._Vy+self._LF*self._dotpsi)/(self._Vx))-self._delta
            self._slipR = atan((self._Vy-self._LR*self._dotpsi)/(self._Vx))

        #evaliation of speed
        v = sqrt(self._Vx*self._Vx  +  self._Vy*self._Vy)

        #integration of velocities
        if v>0:
            self._Vx = (self._Ma-v*v*0.01)*dt + self._Vx
        else:
            self._Vx = (self._Ma-v*0.05)*dt + self._Vx

        #come back to the street R.S.
        self._dotx = self._Vx*cos(self._psi) - self._Vy*sin(self._psi)
        self._doty = self._Vx*sin(self._psi) + self._Vy*cos(self._psi)

        #evaliation of speed
        v = sqrt(self._dotx*self._dotx + self._doty*self._doty)

        #evaluation of angular momentum
        dotpsinew = self._Vx*tan(self._delta)/(self._LR+self._LF)
        angularmomentum = 35.0*(dotpsinew-self._dotpsi)

        #application of Pacejka forces
        self._dotpsi = (angularmomentum-self.CalcPacejkaFront()*self._LF*cos(self._delta)-self.CalcPacejkaRear()*self._LR)*dt + self._dotpsi

        #integration of psi
        self._psi = dotpsinew*dt + self._psi

        #evaluation of new velocity
        self._dotx = v*cos(self._beta+self._psi)
        self._doty = v*sin(self._beta+self._psi)

        #evaluation of new position
        self._previewsx = self._x
        self._previewsy = self._y
        self._x = self._dotx*dt + self._x
        self._y = self._doty*dt + self._y

        #uncoment for keyboard control

        # if abs(self._delta)>0.1:
        #     self._dotdelta = -10.0*self._wheelRadius*self._delta*dt + self._dotdelta
        #     self._delta = self._dotdelta*dt + self._delta
        #     if self._delta<-self._maxDelta:
        #         self._delta=-self._maxDelta
        #     elif self._delta>self._maxDelta:
        #         self._delta=self._maxDelta

    def setAcceleration(self, MaCoff):
        #MaCoff is a value between -1 and 1
        #set the acceleration value in range [0;_maxMa]
        if MaCoff>1:
            MaCoff = 1
        elif MaCoff<-1:
            MaCoff = -1
        self._Ma = MaCoff*self._maxMa

    def setSteering(self, deltaCoff):
        #deltaCoff is a value between -1 and 1
        #set the steering value in range [-_maxDelta;_maxDelta]
        if deltaCoff>1:
            deltaCoff = 1
        elif deltaCoff<-1:
            deltaCoff = -1
        self._delta = deltaCoff*self._maxDelta

    #usefull for keyboard control
    #----------BEGIN KEYBORD SECTION----------
    def littleSteeringLeft(self):
        deltaCoff = self._delta/self._maxDelta
        deltaCoff -= 0.1
        if deltaCoff>1:
            deltaCoff = 1
        elif deltaCoff<-1:
            deltaCoff = -1
        self._delta = deltaCoff*self._maxDelta

    def littleSteeringRight(self):
        deltaCoff = self._delta/self._maxDelta
        deltaCoff += 0.1
        if deltaCoff>1:
            deltaCoff = 1
        elif deltaCoff<-1:
            deltaCoff = -1
        self._delta = deltaCoff*self._maxDelta

    def littleAccelleration(self):
        MaCoff = self._Ma/self._maxMa
        MaCoff += 0.03
        if MaCoff>1:
            MaCoff = 1
        elif MaCoff<-1:
            MaCoff = -1
        self._Ma = MaCoff*self._maxMa

    def littleDecelleration(self):
        MaCoff = self._Ma/self._maxMa
        MaCoff -= 0.15
        if MaCoff>1:
            MaCoff = 1
        elif MaCoff<-1:
            MaCoff = -1
        self._Ma = MaCoff*self._maxMa
    #----------END KEYBORD SECTION----------

    #return velocity in car R.S.
    def getVelocities(self):
        return [self._Vx, self._Vy]

    #return position in street R.S.
    def getPosition(self):
        return [self._x, self._y]

    #return psi and delta angles
    def getAngles(self):
        return [self._psi, self._delta]

    #reset position and angle
    def reset(self, x0, y0, psi0):
        self._x = x0
        self._y = y0
        self._psi = psi0

        self._dotx = 0  #x velocity street R.S.
        self._doty = 0  #y velocity street R.S.

        self._beta = 0  #angle between the velocity and the car assex
        self._delta = 0 #angle between the front wheel and the car assex
        self._dotdelta = 0 #delta angular speed
        self._dotpsi = 0 #psi angular speed
        self._Ma = 0    #motor acceleration
        self._Vx = 0 #x velocity car R.S.
        self._Vy = 0 #y velocity car R.S.
        self._massa = 10 #vehicle mass
        self._LF = 1.5 #distance from front assex
        self._LR = 1.5 #distance from rear assex
        self._wheelRadius = 0.4 #wheel radius
        self._previewsx = 0 #x position in the previous integration
        self._previewsy = 0 #y position in the previous integration
        self._slipF = 0 #slip angle front wheel
        self._slipR = 0 #slip angle rear wheel

    #evaluation of front Pacejka force
    def CalcPacejkaFront(self):
        B = 10  #10 Dry, 12 Wet, 5 Snow, 4 Ice
        C = 1.3 #1.9 Dry, 2.3 Wet, 2 Snow, 2 Ice (1.3 is the defaul value for the lateral force)
        D = 1   #1 Dry, 0.82 Wet, 0.3 Snow, 0.1 Ice
        E = 0.97 #0.97 Dry, 1 Wet, 1 Snow, 1 Ice
        return D*self._massa*4.905*self._LR/(self._LR+self._LF)*sin(C*atan(B*self._slipF-E*(B*self._slipF-atan(B*self._slipF))))

    #evaluation of rear Pacejka force
    def CalcPacejkaRear(self):
        B = 10  #10 Dry, 12 Wet, 5 Snow, 4 Ice
        C = 1.3 #1.9 Dry, 2.3 Wet, 2 Snow, 2 Ice
        D = 1   #1 Dry, 0.82 Wet, 0.3 Snow, 0.1 Ice
        E = 0.97 #0.97 Dry, 1 Wet, 1 Snow, 1 Ice
        return D*self._massa*4.905*self._LF/(self._LR+self._LF)*sin(C*atan(B*self._slipR-E*(B*self._slipR-atan(B*self._slipR))))

    #function to find circoference radius from three points
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
