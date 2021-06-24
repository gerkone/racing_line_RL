from math import cos, sin, tan, sqrt, floor, pi, asin
import numpy as np
import collections as col
import time
import os
import re
import matplotlib.pyplot as plt
import cv2
import pyclipper
from shapely.geometry import LineString, Point

from src.simulation.model import Vehicle

class TrackEnvironment(object):
    """
    State array of 6 elements
    state[0] left distance from track side
    state[1] right distance from track side
    state[2:12] rangefinders
    state[12:22] curvature fronteer
    state[22] angle
    state[23:25] longitudinal and transversal velocities

    Action array of 2 elements
    [0] combined Throttle/Break
    [1] steering
    """
    def __init__(self, trackpath, width = 1.5, dt = 0.03, maxMa = 6, maxDelta=1, render = True, videogame = True, vision = True, fronteer_size = 10,
                    n_beams = 25, rangefinder_cap = 5, curvature_step = 10, min_speed = 0.1, bored_after = 100, discrete = False, discretization_steps = 4):
        # vehicle model settings
        self.car = Vehicle(maxMa, maxDelta)
        self.dt = dt

        # message passing connetion
        self._render = render

        self._vision = vision

        # add state to accomodate image
        self.discrete = discrete
        # if set use the discretizer method to emulate a discrete action space
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

        # -- sensor related params --
        self._curvature_step = curvature_step
        self._fronteer_size = fronteer_size
        self._n_beams = n_beams
        # rangefinder distance cap
        self._rangefinder_cap = rangefinder_cap
        # get n_beams lines in the range (160 degrees range)
        self._beam_space = np.linspace(-80/180 * pi, 80/180 * pi, self._n_beams, endpoint = True)

        self.n_states = 2 + self._fronteer_size + self._n_beams + 1 + 2

        # inner and outer borders
        offsetter = pyclipper.PyclipperOffset()
        scaled = pyclipper.scale_to_clipper(self._track)
        offsetter.AddPath(scaled, pyclipper.JT_SQUARE, pyclipper.ET_CLOSEDPOLYGON)
        inner_offset = pyclipper.scale_from_clipper(offsetter.Execute(pyclipper.scale_to_clipper(-self.width)))[0]
        outer_offset = pyclipper.scale_from_clipper(offsetter.Execute(pyclipper.scale_to_clipper(self.width)))[0]

        self._inner_border = LineString(inner_offset)
        self._outer_border = LineString(outer_offset)

        # agent/training parameters
        self._still = 0
        self._min_speed = min_speed
        self._bored_after = bored_after
        self._start = 0

        self._steps = 0

        if self._render:
            self._videogame = videogame

    def setup_comms(self):
        if self._render:
            # input from the rendering program mode
            import zmq
            from subprocess import Popen

            # run the visualizer
            os.chdir("src/visualizer/")
            visualizer_proc = Popen(["./racing_line_rl"], shell=True,
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
            return visualizer_proc.pid

    def _nearest_point(self):
        """
        return the index in the track array of the nearest point to the current car position
        """
        return min(range(len(self._track)), key = lambda i : self._dist(self._track[i]))


    def _dist(self, q_start, q_end = None):
        """
        pithagorean distance between two points
        """
        if(q_end is None):
            q_end = self.car.getPosition()
        return sqrt(pow(q_end[0] - q_start[0], 2) + pow(q_end[1] - q_start[1], 2))

    def _angle2points(self, q1, q2):
        angle = abs(asin((q2[1] - q1[1]) / self._dist(q1, q2)))
        if(q2[0] >= q1[0]):
            # right
            if(q2[1] >= q1[1]):
                # first quadrant
                angle = angle
            elif(q2[1] < q1[1]):
                # fourth quandrant
                angle = 2 * pi - angle
        elif(q2[0] < q1[0]):
            # left
            if(q2[1] >= q1[1]):
                # second quadrant
                angle = pi - angle
            elif(q2[1] < q1[1]):
                # third quandrant
                angle = pi + angle

        return angle % (2 * pi)

    def _menger_curvature(self, p1, p2, p3, atol=1e-3):
        """
        Inverse of the radius of the circle passing through p1,p2,p3
        """

        vec21 = np.array([p1[0]-p2[0], p1[1]-p2[1]])
        vec23 = np.array([p3[0]-p2[0], p3[1]-p2[1]])

        norm21 = np.linalg.norm(vec21)
        norm23 = np.linalg.norm(vec23)

        v = np.dot(vec21, vec23)/(norm21*norm23)

        if(v <= 1.0 and v >= -1.0):
            theta = np.arccos(v)
            if np.isclose(theta - np.pi, 0.0, atol=atol):
                theta = 0.0

            dist13 = np.linalg.norm(vec21-vec23)

            return 2 * np.sin(theta) / dist13
        else:
            # TODO: fix the impossible shape, brobaly not easily solvable
            return 0.0

    def _curvature(self, start_idx):
        """
        get curvature of track at start_idx
        """
        p1 = self._track[start_idx]
        p2 = self._track[(start_idx + self._curvature_step) % len(self._track)]
        p3 = self._track[(start_idx + self._curvature_step * 2) % len(self._track)]

        return self._menger_curvature(p1, p2, p3)

    def _line_angle(self, x, y, angle, length):
        """
        returns a shapely line from start, angle and lenght
        """
        start = Point(x, y)
        end_x = x + length * cos(angle)
        end_y = y + length * sin(angle)
        end = Point(end_x, end_y)

        return LineString([start, end])

    def _horizontal_distances(self, car_x, car_y, car_angle):
        # car always runnig clockwise
        # lines perpendicular to car
        # pi/2 to the left
        line_l = self._line_angle(car_x, car_y, car_angle - pi / 2, self.width * 2)
        # pi/2 to the right
        line_r = self._line_angle(car_x, car_y, car_angle + pi / 2, self.width * 2)

        # should only be one interesction point
        try:
            if not line_l.is_valid:
                raise Exception
            q_outer = list(line_l.intersection(self._outer_border).coords)[0]
            d_l = self._dist([q_outer[0], q_outer[1]], [car_x, car_y])
        except Exception:
            # car is out of track
            d_l = -1
        try:
            if not line_r.is_valid:
                raise Exception
            q_inner = list(line_r.intersection(self._inner_border).coords)[0]
            d_r = self._dist([q_inner[0], q_inner[1]], [car_x, car_y])
        except Exception:
            # car is out of track
            d_r = -1
        return d_l, d_r

    def _rangefinders(self, car_x, car_y, car_angle, bounds = (-pi/3, pi/3)):
        """
        returns n_beams distances in between the bounds, from the car to the track limits
        """

        beams = [self._line_angle(car_x, car_y, angle, self._rangefinder_cap) for angle in self._beam_space]
        # for each line get the closest intersect
        # must consider both inner and outer track limits, car may be turned
        ranges = []
        for b in beams:
            try:
                inner_intersect = b.intersection(self._inner_border)
                outer_intersect = b.intersection(self._outer_border)
                intersects = list(inner_intersect.coords) + list(outer_intersect.coords)
                if len(intersects) > 0:
                    # get the distances of all the intersections
                    distances = [self._dist([q[0], q[1]], [car_x, car_y]) for q in intersects]
                    ranges.append(min(distances))
                else:
                    # nothing in range - capping
                    ranges.append(self._rangefinder_cap)
            except Exception:
                # TODO: fix, may not be solvable
                ranges.append(0.0)
        return ranges

    def _get_sensors(self, nearest_point_index):
        np.seterr('raise')
        """
        return distances and angle sensory values
        """
        sensors = []
        car_x, car_y = (self.car.getPosition()[0], self.car.getPosition()[1])
        car_angle = self.car.getAngles()[0] % (2 * pi)

        # left, right distance
        d_l, d_r = self._horizontal_distances(car_x, car_y, car_angle)
        outside_track = d_l < 0 or d_r < 0

        sensors.extend([d_l, d_r])
        # 10 rangefinders front
        if not outside_track:
            ranges = self._rangefinders(car_x, car_y, car_angle)
        else:
            ranges = [0.0] * self._n_beams

        sensors.extend(ranges)
        # curvature fronteer, curvature of the next fronteer_size points
        # between each point curvature_step * 2 to cover more track

        curvature_fronteer = [self._curvature((nearest_point_index + (i * self._curvature_step * 2)) % len(self._track))
                                for i in range(self._fronteer_size)]
        sensors.extend(curvature_fronteer)
        # track-relative angle
        q2 = self._track[nearest_point_index]
        # take a couple of points before to avoid superposition
        q1 = self._track[(nearest_point_index - 2) % len(self._track)]
        track_angle = self._angle2points(q1, q2)
        angle = car_angle - track_angle
        sensors.append(angle)
        # speeds
        vx, vy = self.car.getVelocities()
        sensors.extend([vx, vy])

        sensors = [round(x, 6) for x in sensors]
        return np.array(sensors), outside_track


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
        sensors, outside_track = self._get_sensors(nearest_point_index)
        if self._render: image = self.render_and_vision()
        if self._vision:
            state_new = {}
            state_new["sensors"] = sensors
            state_new["image"] = image
            return state_new
        else:
            state_new = {}
            state_new["sensors"] = sensors
            return state_new, outside_track

    def _reward(self, terminal, nearest_point_index, steering):
        # car_angle = self.car.getAngles()[0] % (2 * pi)
        speed_x = self.car.getVelocities()[0]
        # q2 = self._track[nearest_point_index]
        # q1 = self._track[(nearest_point_index - 2) % len(self._track)]
        # track_angle = self._angle2points(q1, q2)
        # angle = car_angle - track_angle
        #
        # d = self._dist(self._track[nearest_point_index])
        reward = 1
        if speed_x < self._min_speed:
            reward = -1

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

    def _is_terminal(self, nearest_point_index, outside_track):
        """
        state is terminal if car has crashed
        (distance from track centre is greater than its width)
        """
        if outside_track == True:
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
        state_new, outside_track = self._transition(action, nearest_point_index)
        terminal = self._is_terminal(nearest_point_index, outside_track)
        sensors = state_new["sensors"]
        reward = self._reward(terminal, nearest_point_index, action[0])
        return state_new, reward, terminal

    def reset(self):
        """
        set the car on the starting line
        """
        self._steps = 0

        q2 = self._track[self._start]
        # take a couple of points before to avoid superposition
        q1 = self._track[(self._start + 5) % len(self._track)]
        track_angle = self._angle2points(q1, q2)
        self.car.reset(q2[0], q2[1], track_angle)
        # closest point is starting position
        sensors, outside_track = self._get_sensors(self._start)
        if self._render: image = self.render_and_vision()
        if self._vision:
            state_new = {}
            state_new["sensors"] = sensors
            state_new["image"] = image
            return state_new
        else:
            state_new = {}
            state_new["sensors"] = sensors
            return state_new

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
            raw = np.frombuffer(data, dtype=np.uint8)
            square = 100
            image = np.array(raw.reshape((square, square, 3)))
            image = np.flip(image, axis = 0)
            if (square > self.img_width) :
                image = cv2.resize(image, dsize=(self.img_width, self.img_height), interpolation=cv2.INTER_CUBIC)
                # plt.imshow(resized)
                # plt.show()
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            image = np.expand_dims(image, axis = -1)
            image = image.astype(np.uint8)
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
