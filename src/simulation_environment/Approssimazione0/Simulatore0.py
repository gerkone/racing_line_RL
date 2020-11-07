from math import cos, sin, atan, tan, sqrt, floor
import numpy as np
from scipy.spatial import Delaunay
import time
import zmq


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
    def integrate(self, dt):
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
        self._Ma = MaCoff*self.maxMa

    def setSteering(self, deltaCoff):    #deltaCoff is a value between -1 and 1
        if deltaCoff>1:
            deltaCoff = 1
        elif deltaCoff<-1:
            deltaCoff = -1
        self._delta = deltaCoff*self.maxDelta

    def getVelocities(self):
        return [self.Vx, self.Vy]

    def getPosition(self):
        return [self._x, self._y]

    def getAngles(self):
        return [self._psi, self._delta]

    def reset(self, x0, y0):
        self._x = x0;
        self._y = y0;


class TrackEnvironment(object):
    """
    State array of 6 elements
    state[0] left distance from track side
    state[1] right distance from track side
    TODO : state[2] front distance from track side (capped at 100)
    state[3] longitudinal velocity
    state[4] transversal velocity
    state[5] angle with track axis

    Action array of 2 elements
    [0] combined Throttle/Break
    [1] steering
    """
    def __init__(self, dt = 0.01, maxMa=1, maxDelta=1, sections=100):
        self.car = Vehicle(maxMa, maxDelta)
        self.dt = dt
        self.n_states = 6
        self.n_actions = 2
        #[Break/Throttle], [Steering]
        self.action_boundaries = [[-1,1], [-1,1]]
        # track width
        self.width = 5
        # load track array
        self._track = np.load("track_1142901636653201649.npy")
        # mapping function: divide the track vertically in sections
        # reduce the closest point search to only a couple of points in the same section
        self._leftmost = min([x for x,_ in self._track])
        track_extension = max([x for x,_ in self._track]) - self._leftmost
        self._section_frame = (track_extension) / sections
        # discrete mapping between x values and candidate nearest points
        self._section_mapping = [[] for _ in range(sections)]
        for track_index, q in enumerate(self._track):
            self._section_mapping[self._sectionMapper(q)].append(track_index)
        # message passing connetion
        context = zmq.Context()
        self._socket = context.socket(zmq.REP)
        self._socket.bind("tcp://*:55555")

    def _sectionMapper(self, q):
        """
        return the index of the relative frame in the mapping
        """
        return int((q[0] - self._leftmost) // self._section_frame)

    def _nearest_point(self):
        """
        return the index in the track array of the nearest point to the current car position
        """
        carpos = self.car.getPosition()
        candidates = self._section_mapping[self._sectionMapper(carpos)]
        return min(candidates, key = lambda i : self._dist(self._track[i]))

    def _dist(self, q_track):
        """
        pithagorean distance between two points
        """
        carpos = self.car.getPosition()
        return sqrt(pow(carpos[0] - q_track[0], 2) + pow(carpos[1] - q_track[1], 2))

    def _inTrack(self, q):
        """
        return true if point is inside the track middle line
        """
        try:
            if not isinstance(self._triangulated, Delaunay):
                self._triangulated = Delaunay(self._track)
        except AttributeError:
            self._triangulated = Delaunay(self._track)

        return self._triangulated.find_simplex(q) >= 0

    def _getSensors(self, nearest_point_index):
        """
        return distances and angle sensory values
        """
        carpos = self.car.getPosition()
        d = self._dist(self._track[nearest_point_index])
        if self._inTrack(carpos):
            # inside
            d_dx = d + self.width
            d_sx = self.width - d
        else:
            # outside
            d_dx = self.width - d
            d_sx = d + self.width

        q2 = self._track[nearest_point_index]
        q1 = self._track[(nearest_point_index - 1) % len(self._track)]
        track_angle = atan((q2[1] - q1[1]) / (q2[0] - q1[0]))
        angle = self.car.getAngles()[0] - track_angle
        return (d_sx, d_dx, 0, angle)


    def _transition(self, action, nearest_point_index):
        """
        apply the action on the model and return sensory (state) value
        """
        #update model paramters with new action
        self.car.setAcceleration(action[0])
        self.car.setSteering(action[1])
        #step forward model by dt
        self.car.integrate(self.dt)
        #get new state sensor values
        state_new = np.zeros(shape = self.n_states)
        state_new[0], state_new[1], state_new[2], state_new[5] = self._getSensors(nearest_point_index)
        state_new[3], state_new[4] = self.car.getVelocities()
        return state_new

    def _reward(self, speed_x, angle, terminal):
        """
        reward function as longitudinal speed along the track parallel
        """
        reward = 0
        reward = speed_x * cos(angle)
        if(terminal):
            reward -= 100
        return reward

    def _isTerminal(self, nearest_point_index):
        """
        state is terminal if car has crashed
        (distance from track centre is greater than its width)
        """
        if self._dist(self._track[nearest_point_index]) > self.width:
            return True
        return False

    def step(self, action):
        """
        advance the system
        """
        nearest_point_index = self._nearest_point()
        state_new = self._transition(action, nearest_point_index)
        terminal = self._isTerminal(nearest_point_index)
        reward = self._reward(state_new[3], state_new[5], terminal)
        return state_new, reward, terminal

    def reset(self):
        """
        set the car on the starting line
        """
        self.car.reset(self._track[0][0], self._track[0][1])

    def render(self):
        """
        send data to the 3D visualizer to render the current state
        """
        # wait for renderer ready
        self._socket.recv()
        # send data to client as / separed list
        # formatted as {x}/{y}/{car_angle}/{front_tyres_angle}
        data = self.car.getPosition()[1] + "/" + self.car.getPosition()[1] + "/" + self.car.getAngles()[0] + "/" + self.car.getAngles()[1]
        self._socket.send_string(data)

o = TrackEnvironment()
o.reset()
o.step([0,0])
o.render()
