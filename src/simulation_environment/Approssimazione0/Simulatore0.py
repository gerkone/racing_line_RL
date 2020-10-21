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
        self._Ma = 0    #Motor accelleration
        self.Vx = 0
        self.Vy = 0
        self.maxMa = maxMa
        self.maxDelta = maxDelta

    #Mettere a posto
    def integrate(self, t):
        self.Vx = self._dotx*cos(self._psi)+self._doty*sin(self._psi)
        self.Vy = self._doty*cos(self._psi)-self._dotx*sin(self._psi)
        self.Vx = self._Ma*dt + self.Vx
        self._dotx = self.Vx*cos(self._psi) - self.Vy*sin(self._psi)
        self._doty = self.Vx*sin(self._psi) + self.Vy*cos(self._psi)
        self._beta = atan(tan(self._delta)/2)
        v = sqrt(self._dotx*self._dotx + self._doty*self._doty)
        self._dotpsi = v/0.03*sin(self._beta)
        self._psi = self._dotpsi*dt + self._psi
        self._dotx = v*cos(self._beta+self._psi)
        self._doty = v*sin(self._beta+self._psi)
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

    # def render():


a = TrackEnvironment()
