"""A skip list: a sorted map with expected O(log n) search, insert, and delete.

Each node is promoted to the next level with probability p, so level i holds
about n * p^i nodes. A search starts on the sparsest level and drops down,
skipping over long runs of keys, much like binary search over a linked list.
"""

import random


class _Node:
    __slots__ = ("key", "value", "forward")

    def __init__(self, key, value, level):
        self.key, self.value = key, value
        self.forward = [None] * (level + 1)


class SkipList:
    def __init__(self, max_level=16, p=0.5, seed=None):
        self.max_level, self.p = max_level, p
        self.head = _Node(None, None, max_level)
        self.level = 0
        self._len = 0
        self._rng = random.Random(seed)

    def __len__(self):
        return self._len

    def __iter__(self):
        node = self.head.forward[0]
        while node:
            yield node.key, node.value
            node = node.forward[0]

    def __contains__(self, key):
        return self._find(key) is not None

    def get(self, key, default=None):
        node = self._find(key)
        return node.value if node else default

    def insert(self, key, value=None):
        update = self._predecessors(key)
        node = update[0].forward[0]
        if node and node.key == key:  # existing key: overwrite value
            node.value = value
            return
        lvl = self._random_level()
        if lvl > self.level:
            for i in range(self.level + 1, lvl + 1):
                update[i] = self.head
            self.level = lvl
        new = _Node(key, value, lvl)
        for i in range(lvl + 1):
            new.forward[i] = update[i].forward[i]
            update[i].forward[i] = new
        self._len += 1

    def delete(self, key):
        update = self._predecessors(key)
        node = update[0].forward[0]
        if not node or node.key != key:
            return False
        for i in range(len(node.forward)):
            update[i].forward[i] = node.forward[i]
        while self.level > 0 and self.head.forward[self.level] is None:
            self.level -= 1
        self._len -= 1
        return True

    def range(self, lo, hi):
        """Yield (key, value) with lo <= key <= hi in O(log n + k)."""
        node = self._predecessors(lo)[0].forward[0]
        while node and node.key <= hi:
            yield node.key, node.value
            node = node.forward[0]

    def intersection(self, other):
        """Keys present in both lists, via a linear merge of level 0: O(n + m)."""
        a, b = self.head.forward[0], other.head.forward[0]
        out = []
        while a and b:
            if a.key == b.key:
                out.append(a.key)
                a, b = a.forward[0], b.forward[0]
            elif a.key < b.key:
                a = a.forward[0]
            else:
                b = b.forward[0]
        return out

    def levels(self):
        """Keys on each level, from the bottom up (for visualizing the structure)."""
        out = []
        for i in range(self.level + 1):
            keys, node = [], self.head.forward[i]
            while node:
                keys.append(node.key)
                node = node.forward[i]
            out.append(keys)
        return out

    # -- internals -------------------------------------------------------------

    def _predecessors(self, key):
        """For each level, the last node whose key is < key."""
        update = [self.head] * (self.max_level + 1)
        node = self.head
        for i in range(self.level, -1, -1):
            while node.forward[i] and node.forward[i].key < key:
                node = node.forward[i]
            update[i] = node
        return update

    def _find(self, key):
        node = self._predecessors(key)[0].forward[0]
        return node if node and node.key == key else None

    def _random_level(self):
        lvl = 0
        while self._rng.random() < self.p and lvl < self.max_level:
            lvl += 1
        return lvl
