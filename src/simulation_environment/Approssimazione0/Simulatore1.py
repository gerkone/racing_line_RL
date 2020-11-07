from math import cos, sin, atan, tan, sqrt
import numpy as np

class Vehicle(object):
    def __init__(self, maxMa=1, maxDelta=1):
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
    def integrate(self, t):
        self.Vx = self._dotx*cos(self._psi)+self._doty*sin(self._psi)
        self.Vy = self._doty*cos(self._psi)-self._dotx*sin(self._psi)
        self.Vx = self._Ma*dt + self.Vx
        self._dotx = self.Vx*cos(self._psi) - self.Vy*sin(self._psi)
        self._doty = self.Vx*sin(self._psi) + self.Vy*cos(self._psi)
        self._beta = atan(tan(self._delta)/2)
        v = sqrt(self._dotx*self._dotx + self._doty*self._doty)
        self.alpha = v*t/self._wheelRadius
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
        self._Ma = MaCoff*MAMAX

    def setSteering(self, deltaCoff):    #deltaCoff is a value between -1 and 1
        if deltaCoff>1:
            deltaCoff = 1
        elif deltaCoff<-1:
            deltaCoff = -1
        self._delta = deltaCoff*DELTAMAX

    def getVelocities():
        return self.Vx, self.Vy

    def reset():
        self._x = 0;

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

class TrackEnvironment(object):
    #Stato: Distanza lato sx, Distanza lato dx, Distanza intersezione davanti,
    #velocità x e y, angolo asse macchina con tracciato
    #Action: Accelerazione/Freno, angolo manubrio
    def __init__(self, dt = 0.01, maxMa=1, maxDelta=1):
        self.car = Vehicle(maxMa, maxDelta)
        self.dt = dt
        self.n_states = 6
        self.n_actions = 2
        self.action_boundaries = [[-1,1], [-1,1]]#[Freno/acceleratore], [Sterzo]
        # self.track # array of points
        self.width = 5

    def reset(self):
        self.car.reset()

    def _transition(self, action):
        #update model paramters with new action
        self.car.setAcceleration(action[0])
        self.car.setSteering(action[1])
        #step forward model by dt
        self.car.integrate(self.dt)
        #get new state sensor values
        state_new = np.zeros_like(self.n_states)
        state_new[0] #distanza sx
        state_new[1] #distanza dx
        state_new[2] #distanza front Dopo 100 metri sempre 100
        state_new[3], state_new[4] = self.car.getVelocitiy() #longitudinal and transversal velocities
        state_new[5] #angolo asse macchina con tracciato
        return state_new

    def _reward(self, state_new, terminal):
        reward = 0
        reward = state_new[3] * cos(state_new[5])
        if(terminal):
            reward -= 100
        return reward

    def _isTerminal(self):
        #if normal(x,y) > width return true
        return False

    def step(self, action):
        state_new = self._transition(action)
        terminal = self._isTerminal()
        reward = self._reward(terminal)
        return state_new, reward, terminal

    #def render():

a = TrackEnvironment()
v = Vehicle();
v.CalcPacejkaDavanti()
v.CalcPacejkaDietro()
