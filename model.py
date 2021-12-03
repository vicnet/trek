import random
from enum import IntEnum
from collections import namedtuple

import builder


class EventSource:
    def __init__(self):
        self.events = {}
        
    def triggerEvent(self, event):
        if event not in self.events:
            return
        for send in self.events[event]:
            send()

    def subscribe(self, when, send):
        if when not in self.events:
            self.events[when] = []
        self.events[when].append(send)


class Dice(EventSource):
    def __init__(self, max=6, min=1):
        super().__init__()
        self.min = min
        self.max = max
        self.value = None

    def throw(self):
        self.value = random.randint(self.min, self.max)
        self.triggerEvent('update')
        return self.value


class Pair(IntEnum):
    """Type of availabel dice pairs."""
    Min = 0
    Max = 1
    Neg = 2
    Add = 3
    Mul = 4

class Dices(EventSource):
    def __init__(self):
        super().__init__()
        self.red = Dice(6,1)
        self.yellow = Dice(5,0)
        self.red.subscribe('update', self.update)
        self.yellow.subscribe('update', self.update)

    def throw(self):
        self.red.throw()
        self.yellow.throw()

    def update(self):
        self.triggerEvent('update')

    def pairing(self):
        pairs = {}
        r = self.red.value
        y = self.yellow.value
        if r is None or y is None:
            return None
        pairs[Pair.Min] = min(r,y)
        pairs[Pair.Max] = max(r,y)
        pairs[Pair.Neg] = max(r,y)-min(r,y)
        pairs[Pair.Add] = r+y
        pairs[Pair.Mul] = r*y
        return pairs

    def value(self, pair):
        return self.pairing()[pair]

class Choices(EventSource):
    def __init__(self):
        super().__init__()
        self.choices = {}
        for pair in Pair:
            self.choices[pair] = 0
    
    def count(self, pair):
        return self.choices[pair]
    
    def max_count(self):
        return 4

    def check(self, pair):
        self.choices[pair] += 1
        self.triggerEvent('update')

debug = False

class Circle(EventSource):
    cpt = 0
    def __init__(self):
        global debug
        super().__init__()
        if debug:
            self.__value = Circle.cpt
            Circle.cpt += 1
        else:
            self.__value = None
        self.cnxs = []
        self.__mapped = False
    
    def add_cnx(self, i):
        self.cnxs.append(i)

    def getvalue(self):
        return self.__value

    def setvalue(self, value):
        self.__value = value
        self.triggerEvent('update')

    value=property(getvalue, setvalue)
    
    def getmapped(self):
        return self.__mapped
    
    def setmapped(self, mapped):
        self.__mapped = mapped
        self.triggerEvent('update')

    mapped=property(getmapped, setmapped)


class Circles:
    def __init__(self):
        super().__init__()
        circles = builder.get_circles('dunai.jpg')
        cnxs = builder.get_connections(circles)
        self.circles = [Circle() for _ in range(len(circles))]
        for i,j in cnxs:
             self.circles[i].add_cnx(j)

    def __getitem__(self, i):
        return self.circles[i]

class Path(EventSource):
    def __init__(self, path):
        super().__init__()
        self.path = path
        
    def exists(self, num):
        return num in self.path

    def add(self, new, num):
        self.path.append(new)
        self.triggerEvent('update')

class Paths(EventSource):
    def __init__(self):
        super().__init__()
        self.paths = []

    def add(self, new, num):
        """
        Add new-num path, new if the new added circle.
        num could be an existing or a new.
        """
        for path in self.paths:
            if path.exists(num):
                path.add(new, num)
                return
        path = Path([new, num])
        self.paths.append(path)
        self.triggerEvent('update')

class Game:
    def __init__(self):
        super().__init__()
        self.dices = Dices()
        self.choices = Choices()
        self.circles = Circles()
        self.paths = Paths()

        # current objects
        self.value = None
        self.circle = None

        self.turn()
    
    def turn(self):
        self.dices.throw()
        self.value = None
        self.circle = None

    def check(self, pair):
        self.choices.check(pair)
        self.value = self.dices.value(pair)
        self.update()

    def choose(self, num):
        if self.circle is None:
            NumCircle = namedtuple("NumCircle", ["num","circle"])
            self.circle = NumCircle(num, self.circles[num])
            self.update()
        else:
            current = self.circle
            self.paths.add(current.num, num)

    def update(self):
        if self.value is None: return
        if self.circle is None: return
        current = self.circle
        current.circle.value = self.value
        # check mapping if not already done
        if not current.circle.mapped:
            for num in current.circle.cnxs:
                circle = self.circles[num]
                if circle.value==self.value:
                    current.circle.mapped = True
                    circle.mapped = True

game = Game()
