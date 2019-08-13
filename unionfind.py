from collections import defaultdict
import six

class UFNode(object):
    def __init__(self, data):
        self.data = data
        self.parent = None

    def find(self):
        if self.parent is None:
            return self
        else:
            self.parent = self.parent.find()
            return self.parent

    def union(self, other):
        c = self.find()
        o = other.find()
        if c != o:
            c.parent = o

    def hash(self):
        return self.data

class UnionFind(object):
    def __init__(self):
        self.objs = {}

    def union(self, item1, item2):
        if item1 not in self.objs:
            self.objs[item1] = UFNode(item1)
        if item2 not in self.objs:
            self.objs[item2] = UFNode(item2)
        self.objs[item1].union(self.objs[item2])

    def classes(self):
        classes = defaultdict(list)
        for obj, val in six.iteritems(self.objs):
            classes[val.find()].append(obj)

        return classes.values()

