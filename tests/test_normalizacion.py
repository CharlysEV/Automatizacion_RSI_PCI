from pci_rsi_sugeridor.core import normaliza_banda

def test_normaliza_banda():
    # Casos estándar
    assert normaliza_banda("700", "4G") == "700"
    assert normaliza_banda("800", "4G") == "800"
    assert normaliza_banda("1800", "4G") == "1800"
    assert normaliza_banda("2100", "4G") == "2100"
    assert normaliza_banda("2600", "4G") == "2600"
    assert normaliza_banda("3500", "5G") == "78"

    # Casos con prefijos/sufijos y espacios
    assert normaliza_banda("  NR700 ", "5G") == "700"
    assert normaliza_banda("B28", "4G") == "700"
    assert normaliza_banda("N78", "5G") == "78"
    assert normaliza_banda("N3", "5G") == "1800"
    assert normaliza_banda("7", "4G") == "2600"

    # Casos que extraen solo el número
    assert normaliza_banda("L900", "4G") == "900"
    assert normaliza_banda("U900", "3G") == "900"

    # Caso con solo un número que podría ser ambiguo
    assert normaliza_banda("7", "4G") == "2600"