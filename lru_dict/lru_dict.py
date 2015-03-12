from collections import MutableMapping, Mapping, KeysView, ItemsView, ValuesView

class ProxiedPeek(Mapping):
    """Helper class for iteration over lru_dicts

    The various ValuesView and ItemsView invoke `__getitem__` on
    the passed mapping, which alters the state of the LRU cache.

    By proxying through a mapping that'll invoke the `peek` method,
    the LRU order is preserved at some cost in preformance.
    """
    def __init__(self, proxied):
        self.__proxied = proxied
        super(ProxiedPeek, self).__init__()

    def __getitem__(self, key):
        return self.__proxied.peek(key)

    def __iter__(self):
        return iter(self.__proxied)

    def __contains__(self, value):
        return value in self.__proxied

    def __len__(self):
        return len(self.__proxied)

    def __repr__(self):
        return "<Proxied {!r}>".format(self.__proxied)

class lru_dict(MutableMapping):
    """A dict/stack implementation of LRU.

    This is a sized mapping that maintains the order of keys based on
    last access of the key, rather than insertion as collections.OrderedDict
    does. Access order is maintained internally by a Python list.

    Setting and getting an item from the cache bumps the item to the
    most recently accessed location, however if a simple value check is
    needed, there is `lru_dict.peek` which will not affect access order.

    When items are added beyond the size of the cache, the least recently
    accessed item is bumped off the stack and out of the interal dict storage.

    >>> cache = lru_dict(size=5)
    >>> cache.update({i:i for i in range(6)})
    >>> list(cache.keys())
    ... [1, 2, 3, 4, 5]

    Iteration is based on the internal stack, rather than internal 
    dict storage.

    `lru_dict` also allows preloading from an initial dictionary or key-value
    pairs. If a dictionary is passed but the order of these keys is
    important, consider passing an instance of collections.OrderedDict.

    The only required argument to instantiate is `size`, which must be a
    numeric value greater than or equal to one.

    `lru_dict` will allow dynamic resizing of the cache as well via the
    `lru_dict.resize` method, which will possibly truncate the oldest values.
    """
    def __init__(self, size, existing=None, *args, **kwargs):
        if size < 1:
            raise ValueError("cache size must be =< 1")

        self.__size = size
        self._stack = []
        self._data = {}

        if existing is not None:
            self.update(existing)

        super(lru_dict, self).__init__(*args, **kwargs)

    @property
    def size(self):
        "Current size of cache."
        return self.__size

    @size.setter
    def size(self, *args):
        raise AttributeError("Use lru_dict.resize to resize cache.")

    @property
    def lru(self):
        "Least recently used item"
        return self._stack[0]

    @property
    def mru(self):
        "Most recently used item"
        return self._stack[-1]

    @property
    def filled(self):
        "Number of cache slots currently filled"
        return len(self)

    def __repr__(self):
        return '<{} size={} filled={}>'.format(self.__class__.__name__,
                                               self.size,
                                               self.filled
                                               )
    def peek(self, key):
        "Return a value from the cache without affecting access order."
        return self._data[key]

    def _make_key_newest(self, key):
        "Bumps an existing key to the most recently accessed location."
        try:
            index = self._stack.index(key)
        except ValueError as e:
            raise KeyError(e)
        else:
            self._stack.append(self._stack.pop(index))

    def resize(self, new_size):
        "Dynamically resize cache and potentially truncate old items."
        if new_size < 1:
            raise ValueError("cache size must be =< 1")

        self.__size = new_size

        if len(self) > self.size:
            # partition at the new size and remove all LRU items
            # rather than continually popping from the stack
            for key in self._stack[:-self.size]:
                del self._data[key]
            self._stack = self._stack[-self.size:]

    # is this needed?
    def __eq__(self, other):
        "Check if this and another LRU are equal in size and LRU order."
        if isinstance(other, lru_dict):
            return self.size == other.size and \
                   self.filled == other.filled and \
                   all(s == o for s,o in zip(self.items(), other.items()))
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, lru_dict):
            return not self.__eq__(other)
        return NotImplemented

    def __setitem__(self, key, value):
        "Sets item in cache and makes key the most recently accessed item."
        if key in self:
            self._make_key_newest(key)
        else:
            self._stack.append(key)
        self._data[key] = value

        if len(self._stack) > self.size:
            del self[self._stack[0]]

    def __getitem__(self, key):
        """Makes key the most recently accessed item and 
        returns value from cache.
        """
        self._make_key_newest(key)
        return self._data[key]

    def __delitem__(self, key):
        "Removes an arbitrary item from the cache and stack."
        del self._data[key]
        self._stack.pop(self._stack.index(key))

    # checking in the dict is faster than stack
    def __contains__(self, value):
        return value in self._data

    def __len__(self):
        return len(self._stack)

    def __iter__(self):
        return iter(self._stack)

    # pass a ProxiedPeek instance to ValuesView and ItemsView
    # to not mess up LRU order since they both invoke __getitem__
    # returning a view over the mapping is consistent with
    # the behavior in other mappings rather returning a custom iterator
    # pass ProxiedPeek to KeysView to maintain consistency
    def keys(self):
        return KeysView(ProxiedPeek(self))

    def values(self):
        return ValuesView(ProxiedPeek(self))

    def items(self):
        return ItemsView(ProxiedPeek(self))

    # maintain consistency with Python 2
    iteritems = items
    itervalues = values
    iterkeys = keys
