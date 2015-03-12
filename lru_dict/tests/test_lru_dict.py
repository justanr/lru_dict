from lru_dict import lru_dict

def make_existing_iterable(size):
    return [(i,i) for i in range(size)]

def test_lru_from_existing_dict():
    existing = {i:i for i in range(10)}
    l = lru_dict(size=10, existing=existing)
    assert existing == l._data

def test_lru_from_existing_list():
    existing = make_existing_iterable(5)
    l = lru_dict(size=10, existing=existing)
    assert all(i in l for i in range(5))

def test__make_key_newest():
    existing = make_existing_iterable(5)
    l = lru_dict(size=5, existing=existing)
    l._make_key_newest(0)
    assert l.mru == 0

def test_peek_doesnt_affect_lru():
    existing = make_existing_iterable(5)
    l = lru_dict(size=5, existing=existing)
    l.peek(0)
    assert l.lru == 0

def test_delitem():
    existing = make_existing_iterable(5)
    l = lru_dict(size=5, existing=existing)
    del l[0]
    assert all(0 not in v for v in [l._stack, l._data])
    assert l.lru == 1

def test_getitem_affects_lru():
    existing = make_existing_iterable(5)
    l = lru_dict(size=5, existing=existing)
    l[0]
    assert l.mru == 0

def test_setitem_affects_lru():
    existing = make_existing_iterable(5)
    l = lru_dict(size=5, existing=existing)
    l[0] = 0
    assert l.mru == 0

def test_setitem_handles_overflow():
    existing = make_existing_iterable(5)
    l = lru_dict(size=5, existing=existing)
    l[6] = 6
    assert 0 not in l

def test_resize_truncates_if_smaller():
    existing = make_existing_iterable(10)
    l = lru_dict(size=10, existing=existing)
    l.resize(8)

    assert all(i not in l for i in [0,1])

def test_values_doesnt_affect_lru():
    existing = make_existing_iterable(10)
    l = lru_dict(size=10, existing=existing)
    prev_mru = l.mru
    vi = iter(l.values())
    next(vi)

    assert prev_mru == l.mru

def test_items_doesnt_affect_lru():
    existing = make_existing_iterable(10)
    l = lru_dict(size=10, existing=existing)
    prev_mru = l.mru
    vi = iter(l.items())
    next(vi)

    assert prev_mru == l.mru


def test_equality():
    existing = make_existing_iterable(5)
    l = lru_dict(size=5, existing=existing)
    o = lru_dict(size=5, existing=existing)

    assert l == o

def test_not_equality():
    existing = make_existing_iterable(5)
    l = lru_dict(size=5, existing=existing)
    o = lru_dict(size=5, existing=existing)
    l[5] = 5
    
    assert l != o
