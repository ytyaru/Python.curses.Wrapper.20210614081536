#!/usr/bin/env python3
# coding: utf8
import os, curses, curses.panel
# cursesライブラリを使いやすくラップする。window/27.pyからPadで使えるよう改修した。
class Curses:
    screen = None
    init = None
    wait_time = 5
    @classmethod
    def run(cls, init=None, wait_time=5):
        cls.init = init
        cls.wait_time = wait_time
        curses.wrapper(Curses.__main)
    @classmethod
    def __main(cls, screen, *args, **kwargs):
        cls.screen = screen
        Cursor.hide()
        Curses.__init_color_pair()
        if cls.init is not None: cls.init()
        Pad.inits()
        cls.__draw()
        cls.__loop()
    @classmethod
    def __init_color_pair(cls):
        curses.setupterm('xterm-256color')
        if not curses.has_colors(): raise Exception('このターミナルは色を表示できません。')
        if not curses.can_change_color(): raise Exception('このターミナルは色を変更できません。')
        curses.use_default_colors()
        for i in range(1, curses.COLORS):
            curses.init_pair(i, i, curses.COLOR_BLACK)
    @classmethod
    def __draw(cls):
#        cls.screen.clear()
        if 0 == len(Pad.Pads): cls.screen.clear()
        for w in Window.Windows: w.Pointer.noutrefresh(); w.draw();
        Pad.draws()
        curses.panel.update_panels()
        curses.doupdate()
    @classmethod
    def __loop(cls):
        cls.__draw()
        if 0 < len(Pad.Pads): Pad.Pads[0].Pointer.keypad(True)
        is_loop = True
        while is_loop:
            if 0 < len(Pad.Pads): key = Pad.Pads[0].Pointer.getch()
            else: key = cls.screen.getch()
            is_loop = Input.inputs(key)
            cls.__draw()
            curses.napms(cls.wait_time)

class Terminal:
    @property
    def Name(self): return curses.termname()
    @Name.setter
    def Name(self, v): curses.setupterm(term=v)
    @property
    def Attrs(self): return curses.termattrs()
    def get_capability(self, capname):
        flag = curses.tigetflag(capname)
        if -1 != flag: return flag
        num = curses.tigetnum(capname)
        if -2 != num : return num
        s = curses.tigetstr(capname)
        return s
    def get_parameter(self, s, *args): # tparm(tigetstr("cup"), 5, 3) -> b'\033[6;4H'
        return curses.tparm(s, *args)
Terminal = Terminal()

class Input:
    Inputs = []
    @classmethod
    def inputs(cls, key):
        if 0 == len(Input.Inputs): return False
        for i in Input.Inputs:
            is_loop = i.input(key)
            if not is_loop: return False
        return True
    def __init__(self):
        Input.Inputs.append(self)
    def input(self, key): return False

class Window:
    Windows = []
    def __init__(self, x=0, y=0, w=-1, h=-1):
        self.__make_win(x, y, w, h)
        self.__subs = []
        self.__cursor = Cursor(self.__window)
        Window.Windows.append(self)
    @property
    def Panel(self): return self.__panel
    @property
    def Pointer(self): return self.__window
    @property
    def Subs(self): return self.__subs
    @property
    def Cursor(self): return self.__cursor

    @property
    def X(self): return self.__window.getbegyx()[1]
    @property
    def Y(self): return self.__window.getbegyx()[0]
    @X.setter
    def X(self, v): self.__panel.move(self.Y, v); curses.panel.update_panels();
    @Y.setter
    def Y(self, v): self.__panel.move(v, self.X); curses.panel.update_panels();
    @property
    def W(self): return self.__window.getmaxyx()[1]
    @property
    def H(self): return self.__window.getmaxyx()[0]
    @W.setter
    def W(self, v): self.__window.resize(self.H, v); curses.panel.update_panels();
    @H.setter
    def H(self, v): self.__window.resize(v, self.W); curses.panel.update_panels();
    def __make_win(self, x=0, y=0, w=-1, h=-1):
        h = h if 0 < h and h <= curses.LINES else curses.LINES
        w = w if 0 < w and w <= curses.COLS else curses.COLS
        y = y if 0 <= y else 0
        y = y if y <= curses.LINES - h else curses.LINES - h
        x = x if 0 <= x else 0
        x = x if x <= curses.COLS - w else curses.COLS - w
        self.__window = curses.newwin(h, w, y, x)
        self.__panel = curses.panel.new_panel(self.__window)
    def make_sub(self, x=0, y=0, w=-1, h=-1, is_derwin=True):
        self.__subs.append(SubWindow(self.Pointer,x=x,y=y,w=w,h=h,is_derwin=is_derwin))
        return self.__subs[-1]
    def show(self): self.__panel.show(); curses.panel.update_panels();
    def hide(self): self.__panel.hide(); curses.panel.update_panels();
    def switch(self):
        if self.__panel.hidden(): self.__panel.show()
        else: self.__panel.hide()
        curses.panel.update_panels()
    def draw(self): pass

class SubWindow:
    def __init__(self, parent, x=0, y=0, w=-1, h=-1, is_derwin=True):
        self.__parent = parent.Pointer
        self.__window = self.__make(x=x, y=y, w=w, h=h, is_derwin=is_derwin)
        self.__cursor = Cursor(self.__window)
        parent.Subs.append(self)
    def __make(self, x=0, y=0, w=-1, h=-1, is_derwin=True):
        ph, pw = self.__parent.getmaxyx()
        h = h if 0 < h and h <= ph else ph
        w = w if 0 < w and w <= pw else pw
        y = y if 0 <= y else 0
        y = y if 0 <= y and y < ph - h else ph - h
        x = x if 0 <= x else 0
        x = x if 0 <= x and x < pw - w else pw - w
        return self.__parent.derwin(h, w, y, x) if is_derwin else self.__parent.subwin(h, w, y, x)
    @property
    def Pointer(self): return self.__window
    @property
    def Cursor(self): return self.__cursor

    @property
    def X(self): return self.__window.getbegyx()[1]
    @property
    def Y(self): return self.__window.getbegyx()[0]
    @X.setter
    def X(self, v): self.__window.mvwin(self.Y, v)
    @Y.setter
    def Y(self, v): self.__window.mvwin(v, self.X)

    @property
    def FromParentX(self): return self.__window.getparyx()[1]
    @property
    def FromParentY(self): return self.__window.getparyx()[0]
    @FromParentX.setter
    def FromParentX(self, v): self.__window.mvderwin(self.Y, v)
    @FromParentY.setter
    def FromParentY(self, v): self.__window.mvderwin(v, self.X)

    @property
    def W(self): return self.__window.getmaxyx()[1]
    @property
    def H(self): return self.__window.getmaxyx()[0]
    @W.setter
    def W(self, v): self.__window.resize(self.H, v)
    @H.setter
    def H(self, v): self.__window.resize(v, self.W)

    def draw(self): pass

class SubPad:
    def __init__(self, parent, x=0, y=0, w=-1, h=-1):
        self.__parent = parent
        self.__make(x, y, w, h)
        self.__cursor = Cursor(self.__window)
        self.__showX = 0
        self.__showY = 0
        parent.Subs.append(self)
    @property
    def Pointer(self): return self.__window
    @property
    def Parent(self): return self.__parent
    @property
    def Cursor(self): return self.__cursor

    @property
    def X(self): return self.__window.getbegyx()[1]
    @property
    def Y(self): return self.__window.getbegyx()[0]
    @X.setter
    def X(self, v): self.__window.derwin(self.Y, v)
    @Y.setter
    def Y(self, v): self.__window.derwin(v, self.X)
#    @X.setter
#    def X(self, v): self.__window.mvwin(self.Y, v)
#    @Y.setter
#    def Y(self, v): self.__window.mvwin(v, self.X)

    @property
    def ShowX(self): return self.__showX
    @property
    def ShowY(self): return self.__showY
    @ShowX.setter
    def ShowX(self, v): self.__showX = v
    @ShowY.setter
    def ShowY(self, v): self.__showY = v

    @property
    def W(self): return self.__window.getmaxyx()[1]
    @property
    def H(self): return self.__window.getmaxyx()[0]
    @W.setter
    def W(self, v): self.__window.resize(self.H, v)
    @H.setter
    def H(self, v): self.__window.resize(v, self.W)
    def __make(self, x=0, y=0, w=-1, h=-1):
        ph, pw = self.__parent.Pointer.getmaxyx()
        h = h if 0 < h and h <= ph else ph
        w = w if 0 < w and w <= pw else pw
        y = y if 0 <= y else 0
        y = y if 0 <= y and y < ph - h else ph - h
        x = x if 0 <= x else 0
        x = x if 0 <= x and x < pw - w else pw - w
        self.__window = self.__parent.Pointer.subpad(h, w, y, x)
        return self.__window
    def noutrefresh(self):
#        self.__window.noutrefresh(self.__showY, self.__showX, 0, 0, curses.LINES-1, curses.COLS-1)
        self.__window.noutrefresh(self.__showY, self.__showX, self.Y, self.X, curses.LINES-1, curses.COLS-1)
    def refresh(self):
#        self.__window.refresh(self.__showY, self.__showX, 0, 0, curses.LINES-1, curses.COLS-1)
        self.__window.refresh(self.__showY, self.__showX, self.Y, self.X, curses.LINES-1, curses.COLS-1)
    def init(self): pass
    def draw(self): pass

class Pad:
    Pads = []
    @classmethod
    def inits(cls):
        for p in Pad.Pads:
            p.init()
            for s in p.Subs:
                s.init()
    @classmethod
    def draws(cls):
        for p in Pad.Pads:
            p.noutrefresh()
            p.draw();
            for s in p.Subs:
                s.noutrefresh()
                s.draw()
    def __init__(self, w=-1, h=-1):
        self.__make_win(w, h)
        self.__subs = []
        self.__cursor = Cursor(self.__window)
        self.__showX = 0
        self.__showY = 0
        Pad.Pads.append(self)
    @property
    def Pointer(self): return self.__window
    @property
    def Subs(self): return self.__subs
    @property
    def Cursor(self): return self.__cursor

    @property
    def X(self): return self.__window.getbegyx()[1]
    @property
    def Y(self): return self.__window.getbegyx()[0]
    @X.setter
    def X(self, v): self.__window.mvwin(self.Y, v)
    @Y.setter
    def Y(self, v): self.__window.mvwin(v, self.X)

    @property
    def ShowX(self): return self.__showX
    @property
    def ShowY(self): return self.__showY
    @ShowX.setter
    def ShowX(self, v): self.__showX = v
    @ShowY.setter
    def ShowY(self, v): self.__showY = v

    @property
    def W(self): return self.__window.getmaxyx()[1]
    @property
    def H(self): return self.__window.getmaxyx()[0]
    @W.setter
    def W(self, v): self.__window.resize(self.H, v); curses.panel.update_panels();
    @H.setter
    def H(self, v): self.__window.resize(v, self.W); curses.panel.update_panels();
    def __make_win(self, w=-1, h=-1):
        h = h if 0 < h else curses.LINES
        w = w if 0 < w else curses.COLS
        self.__window = curses.newpad(h, w)
    def noutrefresh(self):
        self.__window.noutrefresh(self.__showY, self.__showX, self.Y, self.X, curses.LINES-1, curses.COLS-1)
    def refresh(self):
        self.__window.refresh(self.__showY, self.__showX, self.Y, self.X, curses.LINES-1, curses.COLS-1)
    def init(self): pass
    def draw(self): pass

class Cursor:
    @classmethod
    def hide(cls): curses.curs_set(0)
    @classmethod
    def show(cls, is_underline=False):
        if is_underline: curses.curs_set(1)
        else: curses.curs_set(2)
    def __init__(self, window):
        self.__window = window
    @property
    def X(self): return self.__window.getsyx()[1]
    @property
    def Y(self): return self.__window.getsyx()[0]
    @X.setter
    def X(self, v): self.__window.move(self.Y, v)
    @Y.setter
    def Y(self, v): self.__window.move(v, self.X)
    def synchronize(self): self.__window.cursyncup()

if __name__ == "__main__":
    class Pad1(Pad):
        def init(self):
            self.Pointer.clear()
            self.Pointer.bkgd(' ', curses.A_REVERSE | curses.color_pair(4))
            for i in range(0, self.H):
                self.Pointer.addstr(i, 0, f'Pad-1 {i} {self.ShowX},{self.ShowY} ({self.X},{self.Y}) {self.W},{self.H}', curses.A_REVERSE | curses.color_pair(4))
        def draw(self):
            """
            self.Pointer.clear()
            self.Pointer.bkgd(' ', curses.A_REVERSE | curses.color_pair(4))
            for i in range(0, self.H):
                self.Pointer.addstr(i, 0, f'Pad-1 {i} {self.ShowX},{self.ShowY} ({self.X},{self.Y}) {self.W},{self.H}', curses.A_REVERSE | curses.color_pair(4))
            """
    class Window1(Window):
        def draw(self):
            self.Pointer.clear()
            self.Pointer.bkgd(' ', curses.A_REVERSE | curses.color_pair(5))
            self.Pointer.addstr(
                0,0,
#                self.Y, self.X,
                f'Window-1', 
                curses.A_REVERSE | curses.color_pair(5))
            self.Pointer.addstr(
                1,0,
#                1+self.Y, self.X+10,
                f'{Pad.Pads[0].ShowX},{Pad.Pads[0].ShowY} ({self.X},{self.Y}) {self.W},{self.H}', 
                curses.A_REVERSE | curses.color_pair(5))
    class KeyInput(Input):
        def input(self, key):
            if curses.KEY_UP == key: Pad.Pads[0].ShowY -= 1 if 0 < Pad.Pads[0].ShowY else 0
            elif curses.KEY_DOWN == key: Pad.Pads[0].ShowY += 1 if Pad.Pads[0].ShowY < Pad.Pads[0].H-curses.LINES else 0
            elif curses.KEY_LEFT == key: Pad.Pads[0].ShowX -= 1 if 0 < Pad.Pads[0].ShowX else 0
            elif curses.KEY_RIGHT == key: Pad.Pads[0].ShowX += 1 if Pad.Pads[0].ShowX < Pad.Pads[0].W-curses.COLS else 0
            else: return False
            return True

    def init():
#        pad = Pad1(w=curses.COLS*3, h=curses.LINES*3)
#        sub = SubPad1(pad, x=40, y=0, w=curses.COLS-40, h=Pad.Pads[0].H)
        pad = Pad1(w=int(curses.COLS/3), h=curses.LINES*3)
#        sub = SubPad1(pad, x=int(curses.COLS/3)+1, y=0, w=curses.COLS, h=Pad.Pads[0].H)
#        win = Window1(x=int(curses.COLS/3)+1, y=0, w=curses.COLS, h=Pad.Pads[0].H)
#        win = Window1(x=int(curses.COLS/3)+1, y=0, w=curses.COLS, h=min(curses.LINES,Pad.Pads[0].H))
#        win = Window1(x=50, y=10, w=curses.COLS, h=min(curses.LINES,Pad.Pads[0].H))
#        win = Window1(x=50, y=10, w=50, h=20)

#        win = Window1(x=50, y=10, w=50, h=20)
#        win = Window1(x=50, y=0, w=50, h=curses.LINES)
#        win = Window1(x=int(curses.COLS/3)+1, y=0, w=50, h=curses.LINES)
        win = Window1(x=int(curses.COLS/3)+1, y=0, w=curses.COLS-(int(curses.COLS/3)+1), h=curses.LINES)
#        win.Pointer.mvwin(0,0)
#        win.Pointer.mvderwin(0,0)
        KeyInput()

    Terminal.Name = 'xterm-256color'
    Curses.run(init=init, wait_time=5)
#    Curses.run()

