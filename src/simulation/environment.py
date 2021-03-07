from math import cos, sin, tan, sqrt, floor, pi, asin
import numpy as np
import collections as col
import time
import os
import re
import matplotlib.pyplot as plt
import cv2
import pyclipper

from src.simulation.model import Vehicle

class TrackEnvironment(object):
    """
    State array of 6 elements
    state[0] left distance from track side
    state[1] right distance from track side
    state[2] front distance from track side (capped at rangefinder_range)
    state[3] longitudinal velocity
    state[4] transversal velocity
    state[5] angle with track axis

    Action array of 2 elements
    [0] combined Throttle/Break
    [1] steering
    """
    def __init__(self, trackpath, width = 1.5, dt = 0.015, maxMa=6, maxDelta=1, render = True, videogame = True, vision = True,
                    eps = 0.5, max_front = 10, rangefinder_angle = 0.05, rangefinder_range = 20,
                    min_speed = 5 * 1e-3, bored_after = 20, discrete = False, discretization_steps = 4):
        # vehicle model settings
        self.car = Vehicle(maxMa, maxDelta)
        self.dt = dt

        # message passing connetion
        self._render = render

        self._vision = vision

        # if set use the discretizer method to emulate a discrete action space
        self.n_states = 6
        # add state to accomodate image
        self.discrete = discrete
        if(not self.discrete):
            # continuous action setting
            # state/action settings
            self.n_actions = 2
            #[Break/Throttle], [Steering]
            self.action_boundaries = [[-1,1] , [-1,1]]
        else:
            # discrete action setting
            self.discretization_steps = discretization_steps
            # 2 steps for throttle, n steps for steering
            self.n_actions = 10 #2 * self.discretization_steps

        # track settings
        # track width
        self.width = width
        # load track array
        self._track = np.load(trackpath)

        self._rangefinder_range = rangefinder_range
        self._rangefinder_angle = rangefinder_angle

        # inner and outer borders
        offsetter = pyclipper.PyclipperOffset()
        scaled = pyclipper.scale_to_clipper(self._track)
        offsetter.AddPath(scaled, pyclipper.JT_SQUARE, pyclipper.ET_CLOSEDPOLYGON)
        self._inner_border = pyclipper.scale_from_clipper(offsetter.Execute(pyclipper.scale_to_clipper(-self.width)))[0]
        self._outer_border = pyclipper.scale_from_clipper(offsetter.Execute(pyclipper.scale_to_clipper(self.width)))[0]

        # agent/training parameters
        self._still = 0
        self._min_speed = min_speed
        self._bored_after = bored_after
        self._start = 0

        self._steps = 0

        # sensors parameters
        # rangefinder tolerance
        self.eps = eps
        # rangefinder distance cap
        self.max_front = max_front

        if self._render:
            self._videogame = videogame
        if self._render:
            # input from the rendering program mode
            import zmq
            from subprocess import Popen

            # run the visualizer
            os.chdir("src/visualizer/")
            self.visualizer_proc = Popen(["./run"], shell=True,
                        stdin=None, stdout=None, stderr=None, close_fds=True)
            context = zmq.Context()
            self._socket = context.socket(zmq.REP)
            self._socket.bind("tcp://*:55555")
            # wait for visualizer client ack
            print("Waiting on port 55555 for visualizer handshake...")
            self._socket.recv()

            # enable/disable vision
            data = "{}".format(self._vision)
            self._socket.send_string(data)

            self._socket.recv()
            print("Communication OK!")

    def _nearest_point(self):
        """
        return the index in the track array of the nearest point to the current car position
        """
        return min(range(len(self._track)), key = lambda i : self._dist(self._track[i]))

    def _points_in_angle(self, ro, angle, poly, max):
        """
        return the points in the track border inside the angle ro
        """
        carpos = self.car.getPosition()
        l = max / cos(ro)
        # triangle with vertex on car, angle of ro and height of max
        front_triangle = [carpos, [carpos[0] + l * cos(angle - ro), carpos[1] + l * sin(angle - ro)],
            [carpos[0] + l * cos(angle + ro), carpos[1] + l * sin(angle + ro)]]

        inside = [p for p in poly if self._inside_poly(p, front_triangle)]

        return inside


    def _dist(self, q_track, q_point = None):
        """
        pithagorean distance between two points
        """
        if(q_point is None):
            q_point = self.car.getPosition()
        return sqrt(pow(q_point[0] - q_track[0], 2) + pow(q_point[1] - q_track[1], 2))

    def _angle2points(self, q1, q2):
        angle = abs(asin((q2[1] - q1[1]) / self._dist(q1, q2)))
        if(q2[0] >= q1[0]):
            # right
            if(q2[1] >= q1[1]):
                # print("first")
                # first quadrant
                angle = angle
            elif(q2[1] < q1[1]):
                # print("fourth")
                # fourth quandrant
                angle = 2 * pi - angle
        elif(q2[0] < q1[0]):
            # left
            if(q2[1] >= q1[1]):
                # print("second")
                # second quadrant
                angle = pi - angle
            elif(q2[1] < q1[1]):
                # print("third")
                # third quandrant
                angle = pi + angle

        return angle % (2 * pi)

    def _inside_poly(self, q, poly = None):
        """
        ray-casting algorithm for point in polygon
        """
        if(poly is None):
            poly = self._track
        i = 0
        j = len(poly) - 1
        hits = 0
        while i < len(poly):
            xi = poly[i][0]
            yi = poly[i][1]
            xj = poly[j][0]
            yj = poly[j][1]
            j = i
            i += 1
            intersect = ((yi > q[1]) != (yj > q[1])) and (q[0] < (xj - xi) * (q[1] - yi) / (yj - yi) + xi)
            if (intersect):
                hits += 1
        # odd hits = inside, even hits inside
        return hits % 2

    def _get_sensors(self, nearest_point_index):
        """
        return distances and angle sensory values
        """
        # current track angle
        q2 = self._track[nearest_point_index]
        # take a couple of points before to avoid superposition
        q1 = self._track[(nearest_point_index - 2) % len(self._track)]
        track_angle = self._angle2points(q1, q2)
        # distance to track closest point
        carpos = self.car.getPosition()
        d = self._dist(self._track[nearest_point_index])
        # sensor 0 and 1 -- left-right rangefinders
        if self._inside_poly(carpos):
            # inside
            d_dx = d + self.width
            d_sx = self.width - d
        else:
            # outside
            d_dx = self.width - d
            d_sx = d + self.width
        # bound the distances for when outside the track
        d_sx = min(max(0, d_sx), self.width * 2)
        d_dx = min(max(0, d_dx), self.width * 2)
        # sensor 5 -- track-relative angle
        car_angle = self.car.getAngles()[0] % (2 * pi)
        angle = car_angle - track_angle
        # sensor 2 -- front rangefinder
        in_front = self._points_in_angle(self._rangefinder_angle, track_angle, self._inner_border, self._rangefinder_range)
        in_front += self._points_in_angle(self._rangefinder_angle, track_angle, self._outer_border, self._rangefinder_range)
        # closest border point
        try:
            d_front = self._dist(in_front[0])
            for f in in_front[1:]:
                dist = self._dist(f)
                if(dist < d_front):
                    d_front = dist
        except IndexError:
            # no points found
            d_front = self._rangefinder_range

        vx, vy = self.car.getVelocities()
        return np.array([round(d_sx, 3), round(d_dx, 3), round(vx, 2), round(vy, 2), round(d_front, 3), round(angle, 3)])


    def _transition(self, action, nearest_point_index):
        """
        apply the action on the model and return sensory (state) value
        """
        #update model paramters with new action
        self.car.setAcceleration(action[0])
        self.car.setSteering(action[1] * 0.8)
        #step forward model by dt
        self.car.integrate(self.dt)
        #get new state sensor values
        sensors = self._get_sensors(self._start)
        if self._render: image = self.render_and_vision()
        if self._vision:
            state_new = col.namedtuple("observation", ["sensors", "image"])
            return state_new(sensors = sensors,
                            image = image)
        else:
            state_new = col.namedtuple("observation", ["sensors"])
            return state_new(sensors = sensors)

    def _reward(self, speed_x, angle, terminal, nearest_point_index, steering):
        """
        """

        d = self._dist(self._track[nearest_point_index])
        if(d > self.width * 0.4):
            reward = 0.8
        elif(d > self.width * 0.6):
            reward = 0.4
        elif(d > self.width * 0.8):
            reward = 0.1
        else:
            reward = 1

        if(steering >= -0.5 and steering <= 0.5):
            reward += 1

        reward *= pow(speed_x, 2)

        if(d > self.width):
            reward = 0

        return reward

    def _bored(self):
        """
        terminate if car was still too long
        """
        if self._steps > self._bored_after:
            if sqrt(pow(self.car.getVelocities()[0], 2) + pow(self.car.getVelocities()[1], 2)) < self._min_speed:
                return True
        return False

    def _discretizer(self, discrete_action):
        """
        convert discrete to continous action
        """
        if (discrete_action == 0):
            return [-1, 0]
        elif (discrete_action == 1):
            return [-1, 1]
        elif (discrete_action == 2):
            return [-0.5, 0]
        elif (discrete_action == 3):
            return [-0.5, 1]
        elif (discrete_action == 4):
            return [0, 0]
        elif (discrete_action == 5):
            return [0, 1]
        elif (discrete_action == 6):
            return [0.5, 0]
        elif (discrete_action == 7):
            return [0.5, 1]
        elif (discrete_action == 8):
            return [1, 0]
        elif (discrete_action == 9):
            return [1, 1]

    def _is_terminal(self, nearest_point_index):
        """
        state is terminal if car has crashed
        (distance from track centre is greater than its width)
        """
        if self._dist(self._track[nearest_point_index]) > self.width * 1.3:
            # update next starting position
            self._start = nearest_point_index
            return True
        return self._bored()

    def step(self, action):
        """
        advance the system
        """
        self._steps += 1
        if(self.discrete) :
            action = self._discretizer(action)
        nearest_point_index = self._nearest_point()
        q2 = self._track[nearest_point_index]
        # take a couple of points before to avoid superposition
        q1 = self._track[(nearest_point_index - 2) % len(self._track)]
        track_angle = self._angle2points(q1, q2)
        state_new = self._transition(action, nearest_point_index)
        terminal = self._is_terminal(nearest_point_index)
        sensors = state_new.sensors
        reward = self._reward(sensors[3], sensors[2], terminal, nearest_point_index, action[0])
        return state_new, reward, terminal

    def reset(self):
        """
        set the car on the starting line
        """
        self._steps = 0

        q2 = self._track[self._start]
        # take a couple of points before to avoid superposition
        q1 = self._track[(self._start - 2) % len(self._track)]
        track_angle = self._angle2points(q1, q2)
        self.car.reset(q2[0], q2[1], track_angle)
        sensors = self._get_sensors(self._start)
        if self._render: image = self.render_and_vision()
        if self._vision:
            state_new = col.namedtuple("observation", ["sensors", "image"])
            return state_new(sensors = sensors,
                            image = image)
        else:
            state_new = col.namedtuple("observation", ["sensors"])
            return state_new(sensors = sensors)

    def render_and_vision(self):
        """
        send data to the 3D visualizer to render the current state and get image back
        """
        # wait for renderer ready
        # send data to client as / separed list
        # formatted as {x}/{y}/{car_angle}/{front_tyres_angle}
        carpos = self.car.getPosition()
        carangles = self.car.getAngles()
        data = "{}/{}/{}/{}".format(carpos[0], carpos[1], carangles[0], carangles[1])
        self._socket.send_string(data)
        # wait for confirmation
        data = self._socket.recv()
        if self._vision:
            width = 1000
            height = 1000
            image = np.array(np.frombuffer(data, dtype=np.uint8).reshape((width, height, 3)))
            image = np.flip(image, axis = 0)
            resized = cv2.resize(image, dsize=(64, 64), interpolation=cv2.INTER_CUBIC)
            # plt.imshow(resized)
            # plt.show()
            return image

    def get_action_videogame(self):
        if self._videogame:
            #wait until reciving data from client
            #formatted as {acc/dec}/{steering}
            #acc/dec:
            #0 -> do nothing
            #1 -> accellerate
            #2 -> decellerate
            #steering
            #0 -> do nothing
            #1 -> turn left
            #2 -> turn right
            message = self._socket.recv()
            #formatting
            data = re.findall("(\d+)/(\d+)", message.decode("utf-8"))
            #set value on the model
            if data[0][0]=="1":
                self.car.setAcceleration(1.0)
            elif data[0][0]=="2":
                self.car.setAcceleration(-1.0)
            else:
                self.car.setAcceleration(0.0)
            if data[0][1]=="1":
                self.car.littleSteeringLeft()
            elif data[0][1]=="2":
                self.car.littleSteeringRight()
            #step forward model by dt
            self.car.integrate(self.dt)

def manual(path, joystick = True):

    o = TrackEnvironment(path)
    o.reset()

    if joystick:
        import pygame
        pygame.init()
        #Initialize controller
        joysticks = []
        for i in range(pygame.joystick.get_count()):
            joysticks.append(pygame.joystick.Joystick(i))
        for joystick in joysticks:
            joystick.init()
        # 0: Left analog horizonal

        # 2: Left Trigger, 5: Right Trigger
        analog_keys = {0:0, 1:0, 2:0, 3:0, 4:-1, 5: -1 }
        while True:
            for event in pygame.event.get():
                steering = 0
                throttle = 0
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    pass
                if event.type == pygame.JOYAXISMOTION:
                    analog_keys[event.axis] = event.value
                    # Horizontal Analog
                    steering = analog_keys[0]
                    # Triggers
                    throttle = (analog_keys[5] + 1) / 2 - (analog_keys[2] + 1) / 2

            o.step([throttle, steering])
            o.render_and_vision()
            # o.get_action_videogame()
    else:
        import keyboard
        # keyboard mode
        while True:
            steering = 0
            throttle = 0
            # TODO
            o.step([throttle, steering])
            o.render_and_vision()


if __name__ == "__main__":
    manual()
