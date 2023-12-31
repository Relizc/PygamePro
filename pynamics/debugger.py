import threading
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkmsg
from .logger import Logger
from .events import EventType
import datetime
import time
import inspect
import random

def change(s, a, b, c):
    print(c)
    a.__dict__[b[0]] = c
    s.parent._workspace_select(None)
    s.tk.destroy()


class DebugPropertyEditor:

    SUPPORTED_TYPES = {
        "int": int,
        "str": str,
        "float": float
    }

    def __init__(self, parent, fro, path):
        property = fro.__dict__[path[0]]

        self.parent = parent
        self.tk = tk.Toplevel()
        self.tk.title(f"Property Editor of {property.__class__.__name__}")
        self.tk.geometry("300x200")



        self.property = property

        self.tk.columnconfigure(0, weight=1)

        tk.Label(self.tk, text=f"Changing property of", pady=0).grid(row=0)
        tk.Label(self.tk, text=f"<{property.__class__.__name__}> {property}", pady=0).grid(row=1)

        self.ok = tk.StringVar(value=property.__class__.__name__)
        gg = []
        for i in self.SUPPORTED_TYPES:
            gg.append(i)
        self.option = tk.OptionMenu(self.tk, self.ok, *gg)
        self.option.grid(row=2)

        self.e = tk.StringVar(value=str(property))

        self.entry = tk.Entry(self.tk, textvariable=self.e)
        self.entry.grid(row=3)

        self.sure = tk.Button(self.tk, text="Change Property", command=lambda: change(self, fro, path, self.SUPPORTED_TYPES[self.ok.get()](self.e.get())))
        self.sure.grid(row=5, columnspan=2)




class Debugger:

    def __init__(self, parent, enable_event_listener: bool=False, allow_edits: bool=False):
        self.event_update = enable_event_listener
        self.tk = tk.Toplevel()
        self.opened = False
        self.display = True
        self.parent = parent

        self._eps = 0
        self.eps = 0

        self.tk.geometry("800x500")
        self.tk.title("Debug Tools")

        self.nb = ttk.Notebook(self.tk)
        self.nb.pack(fill='both', expand=True)
        self.editor = None

        ### General ###

        self.general = tk.Frame(self.nb)
        self.general.pack(fill='both', expand=True)
        self.nb.add(self.general, text="General Information")

        self._fps = tk.Label(self.general, text=f"FPS: ? (Set: {self.parent.fps})")
        self._fps.grid(row=0, column=0, sticky="w")

        self._tps = tk.Label(self.general, text=f"TPS: ? (Set: {self.parent.tps})")
        self._tps.grid(row=1, column=0, sticky="w")

        ### Event Tracker ###
        self.events = ttk.Frame(self.nb)
        self.events.pack(fill='both', expand=True)
        self.nb.add(self.events, text="Event Tracker")

        if self.event_update:


            self.l = tk.Label(self.events, text="4700 Events Called. EPS: 370")
            self.l.grid(row=1, column=0, sticky="ew")

            self.event = ttk.Treeview(self.events, columns=("epoch", "type", "source"), show='headings')

            self.event.column("epoch", anchor=tk.W, width=100)
            self.event.heading("epoch", text="Time", anchor=tk.W)

            self.event.column("type", anchor=tk.W, width=100)
            self.event.heading("type", text="Event Type", anchor=tk.W)

            self.event.column("source", anchor=tk.W, width=200)
            self.event.heading("source", text="Function Source", anchor=tk.W)

            self.event.grid(row=2, column=0, sticky="ewns")

            self.events.columnconfigure(0, weight=1)
            self.events.rowconfigure(2, weight=1)

            self.event_iid = 0
            self.await_push = []

            self.log = 0
        else:
            tk.Label(self.events, text="Event Tracker is currently disabled due to resource optimization.\nYou can enable Event Tracker by creating a pynamics.debug.Debugger class with enable_event_listener = True.").pack()






        ### Workspace ###

        self.lastLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL = None
        self.wspath = {}

        self.exp = tk.Frame(self.nb)
        self.exp.pack(fill='both', expand=True)
        self.nb.add(self.exp, text="Workspace")
        self.q = {}

        self.explorer = ttk.Treeview(self.exp)
        self.explorer.heading("#0", text="Workspace")

        self.explorer.insert('', tk.END, text="GameManager", open=False, iid=0)
        self._workspace_iid = 0
        self.q[self._workspace_iid] = self.parent
        for i in self.parent.children:
            self._workspace_dfs(i, 0)

        self.explorer.grid(row=0, column=0, sticky="ns")

        self.data_viewer = ttk.Frame(self.exp)
        self.info = tk.Label(self.data_viewer, text="Select an item to view its properties")
        self.info.pack(anchor="w")
        self.data_viewer.grid(row=0, column=1, sticky="nesw")

        self.explorer.bind('<ButtonRelease-1>', self._workspace_select)

        self.exp.rowconfigure(0, weight=1)
        self.exp.columnconfigure(0, weight=0)
        self.exp.columnconfigure(1, weight=1)

        # Tick Manager

        self.tickman = tk.Frame(self.nb)
        self.tickman.pack(fill="both", expand=True)
        self.nb.add(self.tickman, text="Tick Manager")

        self.tickinfo = tk.Label(self.tickman, text=f"Tick Epoch: {self.parent.ticks}\nUptime: {self.parent.starttime}", font=("Courier", 14))
        self.tickinfo.pack()

        self.insttps = tk.Label(self.tickman, text=f"Instantaneous TPS: ?", font=("Courier", 14))
        self.insttps.pack()

        self.statusgraph = tk.Canvas(self.tickman, width=700,height=100,bg="green")
        self.statusgraph.pack()

        self.pp = tk.Button(self.tickman, text="Pause Tick", command=self._tickman_pause)
        self.pp.pack()

        self.ticknext = tk.Button(self.tickman, text="Tick Step", command=self._tickman_stepnext)
        self.ticknext.pack()

        tk.Label(self.tickman, text="Change game tick:")

        self._tickinput = tk.IntVar()
        self._tickinput.set(self.parent.tps)

        self.tickinput = tk.Entry(self.tickman, textvariable=self._tickinput)
        self.tickinput.pack()

        self.submittickinput = tk.Button(self.tickman, command=self._tickman_change_tps, text="Change TPS")
        self.submittickinput.pack()

        self.tickchanger_paused = False
        self.tickchanger_stepping = 0

        self.points = [0]
        self.graph_x = 0
        self.graph_x_factor = 5
        self.last = 0
        self.graph_measure = 0

    def _tickman_change_tps(self):
        f = self._tickinput.get()
        #print(f)
        self.parent.tps = f
        self.parent._epoch_tps = 1 / self.parent.tps
        Logger.print(f"Changed TPS to {f} (DeltaTime:{self.parent._epoch_tps})", channel=5)

    def await_tickchanger_continue(self):
        if self.tickchanger_stepping:
            self.tickchanger_paused = False
        time.sleep(0.01)
        pass

    def _tickman_stepnext(self):
        self.tickchanger_stepping = self.parent.ticksteplisteners

    def _tickman_unpause(self):
        self.pp.config(text="Pause Tick", command=self._tickman_pause)
        self.tickchanger_paused = False

    def _tickman_pause(self):
        self.pp.config(text="Resume Tick", command=self._tickman_unpause)
        self.tickchanger_paused = True



    def _tickman_update(self):
        #print(f"update {random.randint(1, 1000)}")
        t = max(time.time() - self.parent.starttime, 1)
        c = "%.2f" % (self.parent.ticks / t)
        self.tickinfo.config(text=f"""Tick Epoch: {self.parent.ticks}
Uptime: {int(t * 1000)}ms since startup
Avg TPS: {c} (Target: {self.parent.tps})
Tick DeltaTime: {self.parent.deltatime}""", font=("Courier", 14))
        self.tk.after(1, self._tickman_update)

    def _tickman_graph_update(self):
        self.graph_x += self.graph_x_factor
        #self.statusgraph.create_line(self.graph_x, 10, self.graph_x + 1, 10, fill="red")

        asdf = round(((1 / self.parent.deltatime) / (self.parent.tps + int(self.parent.tps * 0.5))) * 100)
        self.points.append(asdf)

        if self.graph_x > 700: self.points.pop(0)

        self.statusgraph.delete("all")

        for x in range(1, len(self.points)):
            point_a = 100 - self.points[x - 1]
            point_b = 100 - self.points[x]

            self.statusgraph.create_line((x - 1) * self.graph_x_factor, point_a, x * self.graph_x_factor, point_b, fill="red")

        self.last = asdf
        self.tk.after(10, self._tickman_graph_update)

        

    def _workspace_property_dfs(self, start, fr, path):
        #print(start)

        if not isinstance(start, (dict, list)):
            return

        ind = 0
        r = list(path)

        for i in start:
            self._ws_prop_iid += 1
            if isinstance(start, list):
                bb = f"ListIndex({ind})<{i.__class__.__name__}> = {i}"
                item = i
                ind += 1
                r.append(ind)

            elif isinstance(start, dict):
                if isinstance(start[i], list):
                    bb = f"{i}<{start[i].__class__.__name__}> = [Iterable List({len(start[i])})]"
                elif isinstance(start[i], dict):
                    bb = f"{i}<{start[i].__class__.__name__}> = [Iterable Dict({len(start[i])})]"
                else:
                    bb = f"{i}<{start[i].__class__.__name__}> = {start[i]}"
                item = start[i]
                nam = start[i].__class__.__name__
                r.append(i)

            self.m[self._ws_prop_iid] = item
            self.wspath[self._ws_prop_iid] = r

            # if isinstance(item, (dict, list)):
            #     bb = "..."
            self.info.insert('', tk.END, text=bb, open=False, iid=self._ws_prop_iid)
            self.info.move(self._ws_prop_iid, fr, 2147483647)
            self._workspace_property_dfs(item, self._ws_prop_iid, r)

    def _workspace_property_change(self, e):
        stuff = self.m[int(self.info.focus())]

        if not isinstance(stuff, (int, float, str)):
            tkmsg.showinfo(f"Unable to edit property", f"The debugger cannot edit the property because the type {stuff.__class__.__name__} is not supported.")
            return

        self.editor = DebugPropertyEditor(self, self.q[int(self.explorer.focus())], self.wspath[int(self.info.focus())])

    def _workspace_select(self, e):
        self.info.pack_forget()

        stuff = self.q[int(self.explorer.focus())]
        if self.lastLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL != None:
            self.lastLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL.debug_unhighlight()
        stuff.debug_unhighlight()
        self.lastLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL = stuff


        self.info = ttk.Treeview(self.data_viewer)
        self.info.heading("#0", text=f"Browsing properties for element {stuff.__class__.__name__}")
        self.info.grid(row=0, column=0, sticky="nesw")
        self.data_viewer.rowconfigure(0, weight=1)
        self.data_viewer.columnconfigure(0, weight=1)

        self.info.bind("<Double-1>", self._workspace_property_change)

        self._ws_prop_iid = 0

        self.m = {}

        for i in stuff.__dict__:
            thing = stuff.__dict__[i]
            if isinstance(thing, list):
                bb = f"[Iterable List({len(thing)})]"
            elif isinstance(thing, dict):
                bb = f"[Iterable Dict({len(thing)})]"
            else:
                bb = str(thing)
            self.info.insert('', tk.END, text=f"{i}<{thing.__class__.__name__}> = {bb}", open=False, iid=self._ws_prop_iid)
            self.m[self._ws_prop_iid] = thing
            self.wspath[self._ws_prop_iid] = [i]
            self._workspace_property_dfs(thing, self._ws_prop_iid, [i])
            self._ws_prop_iid += 1


    def _workspace_dfs(self, next, fr):

        self._workspace_iid += 1
        c = int(self._workspace_iid)

        self.explorer.insert('', tk.END, text=next.__class__.__name__, open=False, iid=self._workspace_iid)
        self.q[self._workspace_iid] = next
        self.explorer.move(self._workspace_iid, fr, 2147483647)

        for i in next.children:
            self._workspace_dfs(i, c)




    def _call_callevent(self, event, obj, func):
        if self.event_update:
            self.await_push.append([
                datetime.datetime.now().strftime("%H:%m:%S.%f"),
                EventType(event).name,
                f"{func.function.__module__}:{inspect.findsource(func.function)[1]}"
            ])
            self.event_iid += 1


    def close(self):
        self.tk.withdraw()
        self.display = False
        if self.editor != None:
            self.editor.tk.destroy()

    def _tick_fps_op(self):
        self._fps.config(text=f"FPS: {self.parent.f} (Set: {self.parent.fps})")
        self.parent.f = 0

        self.tk.after(1000, self._tick_fps_op)

    def _tick_tps_op(self):
        self._tps.config(text=f"TPS: {self.parent.t} (Set: {self.parent.tps})")
        self.insttps.config(text=f"Instantaneous TPS: {self.parent.t}")
        self.parent.t = 0

        self.tk.after(1000, self._tick_tps_op)

    def _tick_event_update(self):
        if not self.event_update: return

        for i in self.await_push:
            self.event.insert(parent='',index='end',text='', values=i)
        self.log += len(self.await_push)
        self._eps += len(self.await_push)
        self.event.yview_moveto(1)
        self.await_push = []

        self.l.config(text=f"{self.log} events called. EPS: {self.eps}")

        self.tk.after(1, self._tick_event_update)

    def _tick_event_update_sec(self):
        self.eps = self._eps
        self._eps = 0
        self.l.config(text=f"{self.log} events called. EPS: {self.eps}")

        self.tk.after(1000, self._tick_event_update_sec)

    def _run(self):
        self.tk.focus_force()

        if not self.opened:
            self.tk.after(1000, self._tick_fps_op)
            self.tk.after(1000, self._tick_tps_op)
            self.tk.after(1, self._tick_event_update)
            self.tk.after(1000, self._tick_event_update_sec)
            self.tk.after(1, self._tickman_update)
            self.tk.after(100, self._tickman_graph_update)
                

            self.tk.protocol("WM_DELETE_WINDOW", self.close)
            self.opened = True

        if not self.display:
            self.display = True
            self.tk.deiconify()

    def run(self):
        self.run_thread = threading.Thread(target=self._run)
        self.run_thread.start()

            