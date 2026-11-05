import random

from skiplist import SkipList


def test_insert_search_delete_against_dict():
    rng = random.Random(0)
    sl, ref = SkipList(seed=1), {}
    for _ in range(2000):
        k = rng.randint(0, 300)
        if rng.random() < 0.7:
            sl.insert(k, str(k))
            ref[k] = str(k)
        else:
            assert sl.delete(k) == (ref.pop(k, None) is not None)
        assert len(sl) == len(ref)
    assert list(sl) == sorted(ref.items())
    assert all(sl.get(k) == v for k, v in ref.items())


def test_overwrite_keeps_single_entry():
    sl = SkipList()
    sl.insert("a", 1)
    sl.insert("a", 2)
    assert len(sl) == 1 and sl.get("a") == 2


def test_range_and_intersection():
    a, b = SkipList(seed=2), SkipList(seed=3)
    for k in range(0, 50, 2):
        a.insert(k)
    for k in range(0, 50, 3):
        b.insert(k)
    assert [k for k, _ in a.range(10, 20)] == [10, 12, 14, 16, 18, 20]
    assert a.intersection(b) == list(range(0, 50, 6))


def test_levels_are_nested():
    sl = SkipList(seed=4)
    for k in range(200):
        sl.insert(k)
    levels = sl.levels()
    assert levels[0] == list(range(200))
    for lower, upper in zip(levels, levels[1:]):
        assert set(upper) <= set(lower) and len(upper) < len(lower)


def test_parses_nse_csv_export(tmp_path):
    from datetime import date

    from stocks import from_nse_csv

    csv = tmp_path / "TATAPOWER.csv"
    csv.write_text(
        "Date ,series ,OPEN ,HIGH ,LOW ,PREV. CLOSE ,ltp ,close ,vwap ,52W H ,52W L ,VOLUME ,VALUE ,No of trades \n"
        '17-Oct-2022,EQ,215.00,218.50,213.85,215.90,218.10,"1,217.95",216.50,298.05,190.00,"94,20,098",0,69021\n'
    )
    assert from_nse_csv(csv) == {date(2022, 10, 17): 1217.95}
