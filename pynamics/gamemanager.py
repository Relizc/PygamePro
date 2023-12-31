import tkinter

from .gameobject import *
from .interface import PyNamical
from .events import EventType, Executable, KeyEvaulator, change_debug_attacher
from .debugger import Debugger
from .logger import Logger
import ctypes
import threading
import random
import time


class Event:
    def __init__(self, func, typeC=None, condition=None, ):
        self.func = func
        self.type = typeC
        self.condition = condition

    def type_down(self) -> str:
        # theType = self.type
        # if theType == EventType.KEYPRESSED:
        #     return keyboard.read_key()
        pass

    def type_bool_down(self) -> bool:
        # theKey = self.type
        # if theKey == EventType.APRESSED:
        #     return keyboard.is_pressed("a")
        pass


class GameManager(PyNamical):
    def __init__(self,
                 dimensions: Dimension,
                 tps: int = 128,
                 fps: int = 0,
                 event_tracker: bool = False):

        super().__init__(None, no_parent=True)
        self.dimensions = dimensions
        self.width = dimensions.x
        self.length = dimensions.y
        self.object_count = 0
        self.objects = []
        self.objectpointers = {}
        self.updates = []
        self.listeners = []
        self.tpu = 1
        self.ticks = 0
        self.tpl = 1
        self.tps = tps
        self._epoch_tps = 1 / self.tps
        self.listenthread = threading.Thread(target=self.listen)
        self.framethread = threading.Thread(target=self.frame)
        self.event_track = event_tracker
        if fps == 0:
            self.fps = 0
            self._epoch_fps = 0.001
        else:
            self.fps = fps
            self._epoch_fps = 1 / self.fps
        self.updatethread = threading.Thread(target=self.update)
        self.terminated = False
        self.f = 0
        self.t = 0
        self.uptick = 0
        self.parent = None
        self.children = []
        self.starttime = 0
        self.ghosts = []
        self.pressed = {}

        self.debug = None

        self._timedifferencetick = time.time()
        self.deltatime = 0

        self.ticksteplisteners = 1

        @self.add_event_listener(event=EventType.KEYDOWN, condition=KeyEvaulator("quoteleft"))
        def open_debugger(n):

            if self.debug == None:
                Logger.print("Debugger not found! Creating window instance", channel=5)
                self.debug = Debugger(self, enable_event_listener=self.event_track)

                change_debug_attacher(self.debug._call_callevent)

            self.debug.run()

    def _key(self, e):
        eventCode = int(e.type)
        if eventCode == 2:
            # KeyPress
            self.pressed[e.keysym] = True
            self.call_event_listeners(EventType.KEYDOWN, str(e.keysym))
        elif eventCode == 3:  # KeyUp
            self.pressed[e.keysym] = False
            self.call_event_listeners(EventType.KEYUP, str(e.keysym))
        pass

    def start(self):
        self.updatethread.start()
        self.listenthread.start()

        try:
            self.window
        except AttributeError:
            err = RuntimeError(
                "No ViewPort Object found for this specific GameManager instance. Create a viewport by using pynamics.ProjectWindow.")
            raise err

        self.starttime = time.time()

        self.window._tk.after(100, self.frame)
        self.window._tk.bind("<KeyPress>", self._key)
        self.window._tk.bind("<KeyRelease>", self._key)
        self.window.start()

    def update(self):

        while True:

            if self.terminated: break

            while self.debug != None and self.debug.tickchanger_paused:
                time.sleep(0.01)
                if self.debug.tickchanger_stepping > 0:
                    self.debug.tickchanger_stepping -= 1
                    break
                continue





            self.deltatime = time.time() - self._timedifferencetick
            self._timedifferencetick = time.time()

            self.call_event_listeners(EventType.TICK)

            for i in self.pressed:
                if self.pressed[i]:
                    self.call_event_listeners(EventType.KEYHOLD, i)

            self.ticks += 1
            self.t += 1

            for i in self.updates:
                i()

            time.sleep(self._epoch_tps)
            # time.sleep(0.0001)
            # time.sleep(random.randint(0, 100) / 1000)

    def listen(self):
        while True:

            if self.terminated: break

            for i in self.listeners:
                if isinstance(i, Event):
                    if i.condition is not None and i.condition():
                        i.func()
                    elif i.condition is None:
                        if i.type_bool_down():
                            i.func()
            time.sleep(self._epoch_tps)

    def test(self):
        print(1)

    def frame(self):
        self.call_event_listeners(EventType.FRAME)
        self.f += 1
        self.window.blit()
        self.window.surface.after(int(self._epoch_fps * 1000), self.frame)

    def add_tick_update(self, function):
        self.events[EventType.TICK].append(Executable(function, lambda i: True))

    def set_ticks_per_update(self, tick: int):
        self.tpu = tick

    def set_ticks_per_listener(self, tick: int):
        self.tpl = tick

    def add_object(self, object: GameObject):
        self.objects.append(object)
        a = self.objects[-1]
        self.objectpointers[object.id] = id(a)
