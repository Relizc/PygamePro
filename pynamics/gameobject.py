import time

from .interface import PyNamical
from .dimensions import Dimension
from .events import EventType
import math
import cmath


class GameObject(PyNamical):
    def __init__(self, parent: PyNamical, x: float, y: float, width: float, height: float, contents: str = None,
                 from_points: tuple = None):
        """
        :param x: The position of the GameObject, on X-Axis
        :param y: The position of the GameObject, on Y-Axis
        :param width: The width of the GameObject
        :param height: The height of the GameObject
        """
        super().__init__(parent)
        self.position = Dimension(x, y)
        self.size = Dimension(width, height)
        self.content = contents
        self.absolute = Dimension(x, y)
        self.points = []
        if from_points is not None:
            for i in from_points:
                self.points.append(i)

        self.parent.add_object(self)

    @property
    def topleft(self):
        return self.position

    @property
    def topright(self):
        return self.position.add(self.size.x, 0)

    @property
    def bottomleft(self):
        return self.position.add(0, self.size.y)

    @property
    def bottomright(self):
        return self.position.add_dim(self.size)

    @property
    def center(self):
        return self.position.add(self.size.x / 2, self.size.y / 2)


class PhysicsBody(GameObject):
    def __init__(self, parent: PyNamical, x: float, y: float, width: float, height: float, mass: int,
                 contents: str = None, from_points: tuple = None, row=1.225):
        super().__init__(parent, x, y, width, height, contents, from_points)

        self.mass = mass
        self.velocity = Vector2d(0, 0)
        self.acceleration = Vector2d(0, 0)
        self.coeff = 0.5
        self.row = row
        self.fnet = Vector2d(0, 0)
        self.gravity = -0.1
        #self.timeB = time.time()
       # self.timeA = time.time()

        self.fnet = Vector2d(90, self.gravity * self.mass)

        @self.parent.add_event_listener(event=EventType.TICK)
        def update_self(e):

            self.acceleration.r = self.fnet.r
            self.acceleration.f = self.fnet.f / self.mass

            self.velocity = self.velocity.add(
                Vector2d(self.acceleration.r, self.acceleration.f))

            v = Vector2d(self.velocity.r, self.velocity.f)
            v.f *= self.parent._epoch_tps

            x3, y3 = self.velocity.cart()
            # print(x3,y3)
            self.position.x += x3
            self.position.y -= y3

            self.fnet = Vector2d(90, self.gravity * self.mass)


    def add_force(self, force):
        self.fnet = self.fnet.add(force)

    def clear(self):
        self.fnet.clear()
        self.velocity.clear()
        self.acceleration.clear()


class Vector2d:
    def __init__(self, r, f):
        """

        :param r: the rotation of the object from the origin.
            |
            O
        ----|----           =90 degrees
            |
            |
            |
            |
        --O-|----           =180 degrees
            |
            |
            etc.
        :param f: the value of the vector
        """
        self.r = r
        self.f = f

    def add(self, b):
        x = self.f * math.cos(math.radians(self.r))
        y = self.f * math.sin(math.radians(self.r))

        x1 = b.f * math.cos(math.radians(b.r))
        y1 = b.f * math.sin(math.radians(b.r))

        xf = x + x1
        yf = y + y1



        r = (xf ** 2 + yf ** 2) ** .5
        theta = math.degrees(math.atan2(yf, xf))
        return Vector2d(theta, r)

    def clear(self):
        self.r = 0
        self.f = 0

    def cart(self) -> tuple:
        x = self.f * math.cos(math.radians(self.r))
        y = self.f * math.sin(math.radians(self.r))

        return x, y

    def __repr__(self):
        return f"Vector2d(Rotation={self.r}, Value={self.f})"
