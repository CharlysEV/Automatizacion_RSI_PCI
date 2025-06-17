import pytest
import pandas as pd
from core import (
    serie_a_enteros_multi,
    sugerir_consecutivos_mod3,
    sugerir_rsi_con_sep,
    ClusterAllocator
)

@ pytest.mark.parametrize("input_list, n, min_pci, expected", [
    ([0,1,2,3,4,5], 3, 0, [0,1,2]),
    ([1,2,3,4,5,6], 2, 3, [3,4]),
    ([5,6,7,8], 4, 0, [6,7,8, ""]),  # only block starting at 6
    ([4,5,7,8], 2, 0, [4,5]),
    ([], 2, 0, ["", ""]),
])
def test_sugerir_consecutivos_mod3(input_list, n, min_pci, expected):
    assert sugerir_consecutivos_mod3(input_list, n, min_pci) == expected

@ pytest.mark.parametrize("libres, n, vendor, bc, expected", [
    ([0,10,20,30], 3, 'ERICSSON', '1800', [0,10,20]),
    ([5,15,25], 2, 'ERICSSON', '3500', [5,13]),  # min_sep 8 for bc==3500
    ([1,2,3], 3, 'HUAWEI', '1800', [1,2,3]),
    ([], 2, 'ERICSSON', '2100', ["", ""])
])
def test_sugerir_rsi_con_sep(libres, n, vendor, bc, expected):
    out = sugerir_rsi_con_sep(libres, n, vendor, bc)
    assert out == expected


def test_serie_a_enteros_multi():
    s = pd.Series(["100;110;120", "130,140", "150 160", None, "foo"])
    out = serie_a_enteros_multi(s)
    assert out == {100,110,120,130,140,150,160}


def test_cluster_allocator_basic():
    alloc = ClusterAllocator()
    # initial unused has full range
    used = {1,2,3}
    free_pci = alloc.get_unused_pci('ERICSSON', '700', used, 0)
    assert 0 in free_pci and 1 not in free_pci
    # register assigned and then get cluster assigned
    cluster = {'A', 'B'}
    alloc.register_assigned(cluster, [10,20])
    assert alloc.get_cluster_assigned(cluster) == {10,20}
    # reset clears state
    alloc.reset()
    assert alloc.get_cluster_assigned(cluster) == set()


def test_cluster_allocator_reuse():
    alloc = ClusterAllocator()
    cluster = {'X'}
    # simulate reserve PCIs
    alloc.register_assigned(cluster, [0,1,2])
    free = alloc.get_unused_pci('ERICSSON', '700', set(), 0)
    # 0,1,2 should not appear
    assert not any(p in free for p in [0,1,2])
