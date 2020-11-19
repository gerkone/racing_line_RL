from math import cos, sin, atan, tan, sqrt, floor
import numpy as np
import time
import os
import re

from simulation.model import Vehicle

class TrackEnvironment(object):
    """
    State array of 6 elements
    state[0] left distance from track side
    state[1] right distance from track side
    state[2] front distance from track side (capped at 100)
    state[3] longitudinal velocity
    state[4] transversal velocity
    state[5] angle with track axis

    Action array of 2 elements
    [0] combined Throttle/Break
    [1] steering
    """
    def __init__(self, trackpath, width = 1, dt = 0.01, maxMa=6, maxDelta=1,
                    render = True, videogame = True, eps = 0.5, max_front = 10,
                    min_speed = 5 * 1e-3, bored_after = 50, discrete = False, discretization_steps = 3):
        # vehicle model settings
        self.car = Vehicle(maxMa, maxDelta)
        self.dt = dt

        # if set use the discretizer method to emulate a discrete action space
        self.n_states = 5
        self.discrete = discrete
        if(not self.discrete):
            # continuous action setting
            # state/action settings
            self.n_actions = 2
            #[Break/Throttle], [Steering]
            self.action_boundaries = [[-1,1], [-1,1]]
        else:
            # discrete action setting
            self.discretization_steps = discretization_steps
            # 2 steps for throttle, n steps for steering
            self.n_actions = 3 * self.discretization_steps

        # track settings
        # track width
        self.width = width
        # load track array
        self._track = np.load(trackpath)

        # agent/training parameters
        self._still = 0
        self._min_speed = min_speed
        self._bored_after = bored_after


        # sensors parameters
        # rangefinder tolerance
        self.eps = eps
        # rangefinder distance cap
        self.max_front = max_front

        # message passing connetion
        self._render = render
        if self._render:
            self._videogame = videogame
        if self._render:
            # input from the rendering program mode
            import zmq
            context = zmq.Context()
            self._socket = context.socket(zmq.REP)
            self._socket.bind("tcp://*:55555")
            # TODO fork visualizer
            # wait for visualizer client ack
            print("Waiting on port 55555 for visualizer handshake...")
            self._socket.recv()
            print("Communication OK!")

    def _nearest_point(self):
        """
        return the index in the track array of the nearest point to the current car position
        """
        return min(range(len(self._track)), key = lambda i : self._dist(self._track[i]))

    def _nearest_point_line(self, angle, q):
        """
        return the index in the track array of the nearest point to the line
        """
        # ax + by + c
        a = tan(angle)
        b = -1
        c = -a * q[0] + q[1]

        def dist_line(p, a, b, c):
            """
            distance between point and line
            """
            return abs(a * p[0] + b * p[1] + c)/sqrt(pow(a, 2) + pow(b, 2))
        # TODO distance projection to the track border ( now middle line )
        closest_point = min(range(len(self._track)), key = lambda i : dist_line(self._track[i], a, b, c))
        # introduce tolerance
        if dist_line(self._track[closest_point], a, b, c) > self.eps:
            return None
        else:
            return closest_point

    def _dist(self, q_track, q_point = None):
        """
        pithagorean distance between two points
        """
        if(q_point is None):
            q_point = self.car.getPosition()
        return sqrt(pow(q_point[0] - q_track[0], 2) + pow(q_point[1] - q_track[1], 2))

    def _angle2points(self, q1, q2):
        return atan((q2[1] - q1[1]) / (q2[0] - q1[0]))

    def _inside_track(self, q):
        """
        ray-casting algorithm for point in polygon
        """
        i = 0
        j = len(self._track) - 1
        hits = 0
        while i < len(self._track):
            xi = self._track[i][0]
            yi = self._track[i][1]
            xj = self._track[j][0]
            yj = self._track[j][1]
            j = i
            i += 1
            intersect = ((yi > q[1]) != (yj > q[1])) and (q[0] < (xj - xi) * (q[1] - yi) / (yj - yi) + xi)
            if (intersect):
                hits += 1
        # odd hits = inside, even hits inside
        return hits % 2

    def _get_track_sensors(self, nearest_point_index):
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
        if self._inside_track(carpos):
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
        car_angle = self.car.getAngles()[0]
        angle = car_angle - track_angle
        # sensor 2 -- front rangefinder
        closest_point = self._nearest_point_line(car_angle, carpos)
        if closest_point is not None:
            track_front = self._track[closest_point]
            d_front = self._dist(track_front)
            # cap front distance to max_front
            d_front = min(d_front, self.max_front)
        else:
            d_front = self.max_front
        return (d_sx, d_dx, d_front, angle)


    def _transition(self, action, nearest_point_index):
        """
        apply the action on the model and return sensory (state) value
        """
        #update model paramters with new action
        self.car.setAcceleration(action[0] )
        self.car.setSteering(action[1] / 3)
        #step forward model by dt
        self.car.integrate(self.dt)
        #get new state sensor values
        state_new = np.zeros(shape = self.n_states)
        # state_new[0], state_new[1], state_new[2], state_new[5] = self._get_track_sensors(nearest_point_index)
        # state_new[3], state_new[4] = self.car.getVelocities()
        sensors = self._get_track_sensors(nearest_point_index)
        state_new[0] = sensors[0]
        state_new[1] = sensors[1]
        state_new[2] = sensors[3]
        state_new[3], state_new[4] = self.car.getVelocities()
        return state_new

    def _reward(self, speed_x, angle, terminal, index):
        """
        reward function as longitudinal speed along the track parallel
        """
        reward = 20 * (index / len(self._track)) #+ speed_x * cos(angle)
        # discourage standing still (lazy, afraid of barriers)
        if(reward < self._min_speed):
            reward = -1
        # crashed or bored
        if(terminal):
            reward -= 1000
        return reward

    def _bored(self):
        """
        terminate if car was still too long
        """
        if sqrt(pow(self.car.getVelocities()[0], 2) + pow(self.car.getVelocities()[1], 2)) < self._min_speed:
            if self._still > self._bored_after:
                self._still = 0
                return True
            else:
                self._still += 1
        else:
            self._still = 0
        return False

    def _discretizer(self, discrete_action):
        """
        convert discrete to continous action
        """
        # TODO complete mapping with steps
        # now 4 fixed actions
        if (discrete_action == 0):
            return [-1, -1]
        elif (discrete_action == 1):
            return [-1, 0]
        elif (discrete_action == 2):
            return [-1, 1]
        elif (discrete_action == 3):
            return [0, -1]
        elif (discrete_action == 4):
            return [0, 0]
        elif (discrete_action == 5):
            return [0, 1]
        elif (discrete_action == 6):
            return [1, -1]
        elif (discrete_action == 7):
            return [1, 0]
        elif (discrete_action == 8):
            return [1, 1]

    def _is_terminal(self, nearest_point_index):
        """
        state is terminal if car has crashed
        (distance from track centre is greater than its width)
        """
        if self._dist(self._track[nearest_point_index]) > self.width:
            return True
        return self._bored()

    def step(self, action):
        """
        advance the system
        """
        if(self.discrete) :
            action = self._discretizer(action)
        nearest_point_index = self._nearest_point()
        state_new = self._transition(action, nearest_point_index)
        terminal = self._is_terminal(nearest_point_index)
        reward = self._reward(state_new[3], state_new[2], terminal, nearest_point_index)
        return state_new, reward, terminal

    def reset(self):
        """
        set the car on the starting line
        """
        q1 = self._track[0]
        # take a couple of points after to avoid superposition
        q2 = self._track[3]
        track_angle = self._angle2points(q1, q2)
        self.car.reset(q1[0], q1[1], track_angle)
        state_new = np.zeros(shape = self.n_states)
        state_new[0], state_new[1] = self.car.getPosition()
        state_new[2] = self.car.getAngles()[0]
        state_new[3], state_new[4] = self.car.getVelocities()
        return state_new

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
            data = re.findall('(\d+)/(\d+)', message.decode("utf-8"))
            #set value on the model
            if data[0][0]=='1':
                self.car.setAcceleration(1.0)
            elif data[0][0]=='2':
                self.car.setAcceleration(-1.0)
            else:
                self.car.setAcceleration(0.0)
            if data[0][1]=='1':
                self.car.littleSteeringLeft()
            elif data[0][1]=='2':
                self.car.littleSteeringRight()
            #step forward model by dt
            self.car.integrate(self.dt)

def manual(path):
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

    o = TrackEnvironment(path)
    o.reset()
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

        print(o.step([throttle, steering])[0])
        o.render()
        # o.get_action_videogame()

if __name__ == "__main__":
    manual()
