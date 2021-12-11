import random
from enum import IntEnum

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
    def __init__(self, num):
        global debug
        super().__init__()
        self.num = num
        if debug:
            self.__value = num
        else:
            self.__value = None
        self.cnxs = []
        self.__mapped = False

    def __repr__(self):
        return f'C{self.num}:{"/" if self.value is None else self.value}'

    def add_cnx(self, i):
        self.cnxs.append(i)
        
    def is_connected(self, i):
        return i in self.cnxs

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
        self.circles = [Circle(i) for i in range(len(circles))]
        for i,j in cnxs:
             self.circles[i].add_cnx(j)

    def __getitem__(self, i):
        return self.circles[i]


class Path(EventSource):
    def __init__(self, *path):
        super().__init__()
        self.path = [ *path ]
        self.sort()

    def sort(self):
        self.path.sort(key=lambda circle: circle.value)

    def exists(self, circle):
        return circle in self.path

    def add(self, new_circle, circle):
        self.path.append(new_circle)
        self.sort()
        self.triggerEvent('update')

    def merge(self, path):
        self.path += path.path
        self.sort()
        self.triggerEvent('update')


class Paths(EventSource):
    def __init__(self):
        super().__init__()
        self.paths = []

    def exists(self, circle):
        for path in self.paths:
            if path.exists(circle):
                return path
        return None

    def add(self, new_circle, circle):
        """
        Add path on 2 circles, new if the new added circle.
        'circle' could be an existing or a new.
        """
        existing = self.exists(new_circle)
        for path in self.paths:
            if path.exists(circle):
                if existing is None:
                    path.add(new_circle, circle)
                else:
                    existing.merge(path)
                    self.paths.remove(path)
                self.triggerEvent('update')
                return
        if existing is not None:
            path = Path(circle)
            existing.merge(path)
        else:
            path = Path(new_circle, circle)
            self.paths.append(path)
        self.triggerEvent('update')


class Score(EventSource):
    bonus_points = [1,3,6]
    
    def __init__(self):
        super().__init__()

    def bonus_for(self, size):
        if size<3:
            return 0
        if size<6:
            return Score.bonus_points[size-3]
        return 5*(size-4)

    def update(self):
        self.triggerEvent('update')


class ScorePath(Score):
    def __init__(self, paths):
        super().__init__()
        self.paths = paths
        self.paths.subscribe('update', self.update)

    def score_for(self, path):
        path = path.path
        if path[-1].value is None:
            return None
        return path[-1].value+len(path)-1, len(path)

    def score(self):
        points_sizes = [ self.score_for(path) for path in self.paths.paths ]
        points,sizes = list(zip(*points_sizes))
        max_size = max(sizes)
        bonus = self.bonus_for(max_size)
        return points, bonus, sum(points)+bonus


class ScoreMap(Score):
    def __init__(self, circles):
        super().__init__()
        self.circles = circles

    def score(self):
        maps = []
        # check all circles
        for circle in self.circles:
            # check only circle with value
            if circle.value is None:
                continue
            # check if a circle is linked to a map
            first_map = None
            for amap in maps:
                if circle.value == amap['value']:
                    # the circle could be in this map
                    # check if connected to an other circle
                    for other in amap['list']:
                        if other.is_connected(circle.num):
                            # it is connected, add or merge
                            if first_map is None:
                                # add to map if not in first one
                                amap['list'].append(circle)
                                first_map = amap
                            else:
                                # circle is in first and map => merge
                                first_map['list'] += amap['list']
                                maps.remove(amap)
                            break
            # check if circle should add
            if first_map is None:
                # not added yet, so create a new map
                maps.append({ 'value': circle.value, 'list':[ circle ] })
        points = []
        max_size = 0
        for amap in maps:
            size = len(amap['list'])
            if size<=1:
                # keep only with min 2 circles
                continue
            points.append(amap['value']+size-1)
            max_size = max(max_size, size)
        bonus = self.bonus_for(max_size)
        return points, bonus, sum(points)+bonus


class Game:
    def __init__(self):
        super().__init__()
        self.dices = Dices()
        self.choices = Choices()
        self.circles = Circles()
        self.paths = Paths()
        self.score_path = ScorePath(self.paths)
        self.score_maps = ScoreMap(self.circles)
        
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
            self.circle = self.circles[num]
            self.update()
        else:
            current = self.circle
            self.paths.add(current, self.circles[num])

    def update(self):
        if self.value is None: return
        if self.circle is None: return
        current = self.circle
        current.value = self.value
        # check mapping if not already done
        if not current.mapped:
            for num in current.cnxs:
                circle = self.circles[num]
                if circle.value==self.value:
                    current.mapped = True
                    circle.mapped = True
                    self.score_maps.update()

game = Game()
game.circles[15].value = 5
game.circles[16].value = 5
game.circles[0].value = 5
game.circles[8].value = 5
#game.circle = game.circles[0]
#game.paths.add(game.circles[15],game.circles[16])
game.score_maps.score()
