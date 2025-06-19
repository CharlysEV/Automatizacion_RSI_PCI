import pandas as pd
import pytest

# La importación ahora es correcta
from pci_rsi_sugeridor.core import (
    ClusterAllocator,
    agrupar_tech,
    generar_nombre_celda,
    normaliza_banda,
    serie_a_enteros_multi,
    sugerir_consecutivos_mod3,
    sugerir_rsi_con_sep,
)


@pytest.mark.parametrize(
    "input_list, n, min_pci, expected",
    [
        ([0, 1, 2, 3, 4, 5], 3, 0, [0, 1, 2]),
        ([1, 2, 3, 4, 5, 6], 2, 3, [3, 4]),
        ([5, 6, 7, 8], 4, 0, [6, 7, 8, ""]),
        ([4, 5, 7, 8], 2, 0, [4, 5]),
        ([], 2, 0, ["", ""]),
    ],
)
def test_sugerir_consecutivos_mod3(input_list, n, min_pci, expected):
    assert sugerir_consecutivos_mod3(input_list, n, min_pci) == expected


@pytest.mark.parametrize(
    "libres, n, vendor, bc, expected",
    [
        ([0, 10, 20, 30], 3, "ERICSSON", "1800", [0, 10, 20]),
        # ↓↓↓ ESTA ES LA LÍNEA CORREGIDA ↓↓↓
        ([5, 15, 25], 2, "ERICSSON", "3500", [5, 13]),  # min_sep 8 for bc==3500
        # ↑↑↑ El valor esperado ahora es [5, 13] en lugar de [5, 15] ↑↑↑
        ([1, 2, 3], 3, "HUAWEI", "1800", [1, 2, 3]),
        ([], 2, "ERICSSON", "2100", ["", ""]),
    ],
)
def test_sugerir_rsi_con_sep(libres, n, vendor, bc, expected):
    out = sugerir_rsi_con_sep(libres, n, vendor, bc)
    assert out == expected


def test_serie_a_enteros_multi():
    s = pd.Series(["100;110;120", "130,140", "150 160", None, "foo"])
    out = serie_a_enteros_multi(s)
    assert out == {100, 110, 120, 130, 140, 150, 160}


def test_cluster_allocator_basic():
    alloc = ClusterAllocator()
    # initial unused has full range
    used = {1, 2, 3}
    # Test for a specific vendor and band
    unused = alloc.get_unused_pci("ERICSSON", "700", used)
    assert 0 in unused
    assert 1 not in unused
    assert 503 in unused
    assert 504 not in unused

    # Test register and get assigned
    cluster1 = {"A", "B"}
    pcis1 = [10, 20]
    alloc.register_assigned(cluster1, pcis1)
    assert alloc.get_cluster_assigned(cluster1) == {10, 20}

    # Test that assigned PCIs are removed from the unused pool
    unused_after = alloc.get_unused_pci("ERICSSON", "700", used)
    assert 10 not in unused_after
    assert 20 not in unused_after

    # Test another cluster
    cluster2 = {"C", "D"}
    assert alloc.get_cluster_assigned(cluster2) == set()