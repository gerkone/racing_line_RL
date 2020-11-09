from math import cos, sin, atan, tan, sqrt, floor
import numpy as np
from scipy.spatial import Delaunay
import time
import os

from model import Vehicle

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
    def __init__(self, dt = 0.01, maxMa=1, maxDelta=1, sections=100, render = True):
        self.car = Vehicle(maxMa, maxDelta)
        self.dt = dt
        self.n_states = 6
        self.n_actions = 2
        #[Break/Throttle], [Steering]
        self.action_boundaries = [[-1,1], [-1,1]]
        # track width
        self.width = 5
        # load track array
        self._track = np.load("track_4387235659010134370.npy")
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
        self._render = render
        if render:
            import zmq
            context = zmq.Context()
            self._socket = context.socket(zmq.REP)
            self._socket.bind("tcp://*:55555")
            # TODO fork visualizer
            # wait for visualizer client ack
            self._socket.recv()

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

    def _angle2points(self, q1, q2):
        return atan((q2[1] - q1[1]) / (q2[0] - q1[0]))

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
        # take a couple of points before to avoid superposition
        q1 = self._track[(nearest_point_index - 3) % len(self._track)]
        track_angle = self._angle2points(q1, q2)
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
        q1 = self._track[0]
        # take a couple of points after to avoid superposition
        q2 = self._track[3]
        track_angle = self._angle2points(q1, q2)
        self.car.reset(0, 0, track_angle)

    def render(self):
        """
        send data to the 3D visualizer to render the current state
        """
        if self._render:
            # wait for renderer ready
            # send data to client as / separed list
            # formatted as {x}/{y}/{car_angle}/{front_tyres_angle}
            carpos = self.car.getPosition()
            carangles = self.car.getAngles()
            data = "{}/{}/{}/{}".format(carpos[0], carpos[1], carangles[0], carangles[1])
            self._socket.send_string(data)
            # wait for confirmation
            self._socket.recv()

o = TrackEnvironment()
o.reset()
while True:
    # o.step([0,0])
    o.render()
