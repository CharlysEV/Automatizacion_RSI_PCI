from pci_rsi_sugeridor.core import (
    agrupar_tech,
    generar_nombre_celda,
    normaliza_banda,
)


def test_normaliza_banda():
    assert normaliza_banda("700", "4G") == "700"
    assert normaliza_banda("N78", "5G") == "78"


def test_agrupar_tech():
    assert agrupar_tech("5G SA") == "5G"
    assert agrupar_tech("NR") == "5G"
    assert agrupar_tech("4G") == "4G"
    assert agrupar_tech("LTE") == "4G"


def test_generar_nombre_celda():
    # Caso 4G
    assert generar_nombre_celda("M5161", "4G", "700", 1, "A") == "M5161Y1A"
    assert generar_nombre_celda("M5161", "4G", "2600", 2, "B") == "M5161L2B"

    # Caso 5G
    assert generar_nombre_celda("M5161", "5G", "N78", 3, "A") == "M5161P3A"

    # Caso con sufijo por defecto
    assert generar_nombre_celda("T1234", "4G", "800", 1) == "T1234M1A"

    # Caso con tecnología desconocida (debería usar 'X')
    assert generar_nombre_celda("E9876", "3G", "2100", 1) == "E9876X1A"