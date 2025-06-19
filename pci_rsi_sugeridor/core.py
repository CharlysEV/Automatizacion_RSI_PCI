#!/usr/bin/env python3
# core.py: Lógica de asignación PCI/RSI encapsulada

import os
import re
from datetime import datetime
from typing import Tuple

import openpyxl
import pandas as pd
import tabulate


class ClusterAllocator:
    """
    Encapsula el estado de asignaciones de PCI por cluster
    y los pools de PCI/RSI para cada vendor y banda.
    """

    def __init__(self):
        self._assigned_by_cluster = {}
        self._pool_pci = {
            "ERICSSON": {
                b: list(range(504))
                for b in [
                    "700",
                    "800",
                    "900",
                    "1800",
                    "2100",
                    "2600",
                    "1",
                    "3500",
                    "78",
                ]
            },
            "HUAWEI": {
                b: list(range(504))
                for b in [
                    "700",
                    "800",
                    "900",
                    "1800",
                    "2100",
                    "2600",
                    "1",
                    "3500",
                    "78",
                ]
            },
        }
        self._pool_rsi = {
            "ERICSSON": {
                b: list(range(838))
                for b in [
                    "700",
                    "800",
                    "900",
                    "1800",
                    "2100",
                    "2600",
                    "1",
                    "3500",
                    "78",
                ]
            },
            "HUAWEI": {
                b: list(range(838))
                for b in [
                    "700",
                    "800",
                    "900",
                    "1800",
                    "2100",
                    "2600",
                    "1",
                    "3500",
                    "78",
                ]
            },
        }

    def reset(self):
        """Resetea todas las asignaciones de clusters."""
        self._assigned_by_cluster.clear()

    def get_unused_pci(
        self, vendor: str, band: str, used_set: set, min_pci: int = 0
    ) -> list:
        """Devuelve pool – usado_maestro – usado_por_clusters, filtrado por min_pci."""
        pool = self._pool_pci.get(vendor.upper(), {}).get(band, [])
        assigned_global = (
            set().union(*self._assigned_by_cluster.values())
            if self._assigned_by_cluster
            else set()
        )
        forbidden = set(used_set) | assigned_global
        return [p for p in pool if p not in forbidden and p >= min_pci]

    def get_unused_rsi(
        self, vendor: str, band: str, used_set: set, min_rsi: int = 0
    ) -> list:
        """Devuelve lista de RSIs libres según el vendor/band y excluyendo used_set."""
        pool = self._pool_rsi.get(vendor.upper(), {}).get(band, [])
        return [r for r in pool if r not in used_set and r >= min_rsi]

    def register_assigned(self, cluster: set, pcis: list):
        """Registra los PCIs asignados para un cluster dado."""
        key = frozenset(cluster)
        self._assigned_by_cluster.setdefault(key, set()).update(
            [p for p in pcis if isinstance(p, int)]
        )

    def get_cluster_assigned(self, cluster: set) -> set:
        """Obtiene el set de PCIs ya asignados para un cluster."""
        return self._assigned_by_cluster.get(frozenset(cluster), set())


# FUNCIONES AUXILIARES


def ensure_csv(fname: str) -> str:
    f = fname.strip()
    basename = os.path.basename(f)
    dirname = os.path.dirname(f)
    if not basename.lower().endswith(".csv"):
        basename += ".csv"
    return os.path.join(dirname, basename) if dirname else basename


def detect_separator(fp: str, sample: int = 2048) -> str:
    try:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read(sample)
        return ";" if txt.count(";") > txt.count(",") else ","
    except FileNotFoundError:
        return ","


def map_column_names(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "SITE": ["SITE", "ENODEB_ID", "SITE_ID", "NODO OSP", "GNBID", "GNB_ID", "NEID"],
        "NODE": ["NODE", "NODE_ID", "NODO VDF"],
        "CELLNAME": ["CELLNAME", "CELL_NAME", "CELLID", "CELL_ID"],
        "BAND": ["BAND", "BANDA", "BANDWIDTH", "FREQUENCYBAND"],
        "TECH": ["TECH", "TECNOLOGIA", "TECNOLOGÍA"],
        "VENDOR": ["VENDOR", "FABRICANTE"],
        "BCCH/SC/PCI": ["BCCH/SC/PCI", "PCI", "BCCH", "SC", "BCCH_SC_PCI"],
        "RSQID": [
            "RSQID",
            "RSI",
            "RSRQID",
            "ROOTSEQUENCEINDEX",
            "LOGICALROOTSEQUENCEINDEX",
        ],
        "TAC": ["TAC"],
        "FECHA": ["FECHA", "DATE", "TIME", "TIMESTAMP"],
    }
    ren = {}
    for std, cands in mapping.items():
        for col in df.columns:
            if col.strip().upper() in [c.upper() for c in cands]:
                ren[col] = std
                break
    return df.rename(columns=ren)


def map_peticion_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "SITE": ["SITE OSP", "SITE", "NODO OSP", "ENODEB_ID", "SITE_ID"],
        "NODE": ["NODE VDF", "NODE", "NODO VDF", "NODE_ID"],
        "TECH": ["TECH", "TECNOLOGIA", "TECNOLOGÍA"],
        "BAND": ["BAND", "BANDA"],
        "CELDAS": ["CELDAS", "SECTORES", "NUM_CELDAS"],
        "MIN_PCI": ["MIN_PCI", "MIN PCI", "PCI MIN"],
        "MIN_RSI": ["MIN_RSI", "MIN RSI", "RSI MIN"],
        "SUFIJO": ["SUFIJO", "SUFFIX", "CELL SUFFIX"],
    }
    ren = {}
    for std, cands in mapping.items():
        for col in df.columns:
            if col.strip().upper() in [c.upper() for c in cands]:
                ren[col] = std
                break
    df = df.rename(columns=ren)
    for opc in ["NODE", "CELDAS", "MIN_PCI", "MIN_RSI", "SUFIJO"]:
        if opc not in df.columns:
            df[opc] = ""
    return df


def normaliza_banda(b_raw: str, t_raw: str) -> str:
    b_str = str(b_raw).strip().upper()
    nums = re.findall(r"\d+", b_str)
    b = nums[0] if nums else b_str
    if b in ["78", "N78", "NR78", "3500"]:
        return "78"
    if b in ["700", "N28", "NR700", "B28", "28"]:
        return "700"
    if b in ["2100", "N1", "NR2100", "B1"]:
        return "2100"
    if b in ["1800", "B3", "N3", "NR1800"]:
        return "1800"
    if b in ["800", "B20", "N20", "NR800"]:
        return "800"
    if b in ["2600", "B7", "N7", "NR2600", "7"]:
        return "2600"
    return b


def agrupar_tech(x: str) -> str:
    xt = str(x).strip().upper()
    if xt.startswith("5G") or xt.startswith("NR"):
        return "5G"
    if xt.startswith("4G") or xt == "LTE":
        return "4G"
    if xt == "NBIOT":
        return "NBIOT"
    return xt


def detectar_numero_sectores(site: str, df_pci_master: pd.DataFrame) -> int:
    sc = site.strip().upper()
    df_site_local = df_pci_master[df_pci_master["SITE_CLEAN"] == sc]
    if df_site_local.empty:
        return 3
    sufijos = {
        int(m.group(1))
        for cel in df_site_local["CELLNAME"].dropna().astype(str)
        for m in [re.search(r"(\d+)[AB]$", cel.strip().upper())]
        if m
    }
    return len(sufijos) if sufijos else 3


def generar_nombre_celda(
    node: str, tech: str, band: str, idx: int, suffix: str = "A"
) -> str:
    base = str(node).strip().upper()
    t_clean = agrupar_tech(tech)
    b_clean = normaliza_banda(band, tech)
    letra_map = {
        "4G": {"700": "Y", "800": "M", "1800": "N", "2100": "T", "2600": "L"},
        "5G": {"700": "Q", "2100": "W", "3500": "P", "78": "P"},
    }
    letra = letra_map.get(t_clean, {}).get(b_clean, "X")
    suf = str(suffix).strip().upper()
    if suf not in ["A", "B"]:
        suf = "A"
    return f"{base}{letra}{idx}{suf}"


def serie_a_enteros_multi(s: pd.Series) -> set:
    res = set()
    for val in s.dropna().astype(str):
        for part in re.split(r"[;, \s]+", val):
            if part.isdigit():
                res.add(int(part))
    return res


def sugerir_consecutivos_mod3(pool: list, n: int, min_pci: int = 0) -> list:
    libres = [x for x in sorted(set(pool)) if x >= min_pci]
    for base in libres:
        if base % 3 == 0:
            seq = [base + i for i in range(n)]
            result = [x if x in libres else "" for x in seq]
            return result
    res = libres[:n]
    while len(res) < n:
        res.append("")
    return res


def sugerir_rsi_con_sep(libres: list, n: int, vendor: str, bc: str) -> list:
    libres_s = sorted(set(libres))
    if vendor.upper() == "ERICSSON":
        sep = 8 if bc == "3500" else 10
        first = libres_s[0] if libres_s else None
        if first is None:
            return [""] * n
        return [first + i * sep for i in range(n)]
    else:
        res = libres_s[:n]
        while len(res) < n:
            res.append("")
        return res


# ============================================================
#                    CARGA Y PREPROCESADO DE DATOS
# ============================================================


def cargar_y_preprocesar_pci(csv_pci_path: str) -> pd.DataFrame:
    sep = detect_separator(csv_pci_path)
    df = pd.read_csv(
        csv_pci_path, dtype=str, sep=sep, encoding="utf-8", error_bad_lines=False
    )
    df = map_column_names(df)
    if "SITE" not in df.columns:
        raise ValueError("La columna 'SITE' es obligatoria en el maestro PCI/RSI.")
    df["SITE_CLEAN"] = df["SITE"].astype(str).str.strip().str.upper()
    df["BAND_CLEAN"] = df.apply(
        lambda r: normaliza_banda(r.get("BAND", ""), r.get("TECH", "")), axis=1
    )
    df["TECH_GROUP"] = df.get("TECH", "").apply(agrupar_tech)
    df["VENDOR_CLEAN"] = df.get("VENDOR", "").astype(str).str.strip().str.upper()
    return df


def cargar_y_preprocesar_rsi_5g(
    csv_rsi_path: str, df_pci_master: pd.DataFrame
) -> pd.DataFrame:
    sep = detect_separator(csv_rsi_path)
    try:
        df = pd.read_csv(
            csv_rsi_path, dtype=str, sep=sep, encoding="utf-8", error_bad_lines=False
        )
    except FileNotFoundError:
        return pd.DataFrame()
    df = map_column_names(df)
    if "SITE" not in df.columns or "FECHA" not in df.columns:
        return pd.DataFrame()
    df["SITE_CLEAN"] = df["SITE"].astype(str).str.strip().str.upper()
    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
    df = df.sort_values("FECHA", ascending=False).drop_duplicates("SITE_CLEAN")
    df["TAC"] = df["SITE_CLEAN"].map(df_pci_master.set_index("SITE_CLEAN")["TAC"])
    return df


def preprocesar_TACAreas(xlsx_path: str = "TACAreas.xlsx") -> dict:
    try:
        wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    except FileNotFoundError:
        return {}
    ws = wb.active
    tac_a_vecinos: dict[str, set] = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        tac = str(row[1]).strip() if row[1] else None
        vec = str(row[2]).strip() if row[2] else None
        if tac:
            tac_a_vecinos.setdefault(tac, set())
            if vec and vec != tac:
                tac_a_vecinos[tac].add(vec)
    return {k: sorted(v) for k, v in tac_a_vecinos.items()}


# ============================================================
#                       SUGERIDOR PCI/RSI (CORE)
# ============================================================


def sugerir_pci_rsi(
    site: str,
    nodo_vdf: str,
    tech: str,
    band: str,
    n_celdas: int,
    df_pci_master: pd.DataFrame,
    df_rsi_5g_master: pd.DataFrame,
    tac_a_vecinos: dict,
    min_pci: int,
    min_rsi: int,
    modo_r: bool,
    allocator=None,
    coord_pcis=None,
) -> Tuple[list, list]:
    if allocator is None:
        allocator = ClusterAllocator()

    sc_upper = site.strip().upper()
    tc = agrupar_tech(tech)
    bc = normaliza_banda(band, tech)

    df_site = df_pci_master[df_pci_master["SITE_CLEAN"] == sc_upper]
    if df_site.empty:
        raise ValueError(f"SITE {site} no encontrado en maestro.")

    df_site_tc = df_site[df_site["TECH_GROUP"] == tc]
    tacs = df_site_tc["TAC"].dropna().unique().tolist()
    tacs = [
        t
        for t in tacs
        if df_site[(df_site["TAC"] == t) & (df_site["TECH_GROUP"] == "NBIOT")].empty
    ]

    resumen_list, detalle_list = [], []
    for tac_item in tacs:
        vecinos = tac_a_vecinos.get(str(tac_item), [])
        cluster = set(vecinos) | {str(tac_item)}

        usados_pci = set()
        mask_pci = (
            df_pci_master["TAC"].isin(cluster)
            & (df_pci_master["BAND_CLEAN"] == bc)
            & (df_pci_master["TECH_GROUP"] == tc)
        )
        usados_pci |= serie_a_enteros_multi(df_pci_master[mask_pci]["BCCH/SC/PCI"])
        usados_pci |= allocator.get_cluster_assigned(cluster)
        libres_pci = allocator.get_unused_pci(
            df_site["VENDOR_CLEAN"].iloc[0], bc, usados_pci, min_pci
        )

        usados_rsi = (
            serie_a_enteros_multi(df_pci_master[mask_pci]["RSQID"])
            if tc != "5G"
            else set()
        )
        libres_rsi = allocator.get_unused_rsi(
            df_site["VENDOR_CLEAN"].iloc[0], bc, usados_rsi, min_rsi
        )

        if coord_pcis:
            ap_list = []
            for res_4g in coord_pcis:
                cand = next((p for p in libres_pci if p % 3 == res_4g), None)
                ap_list.append(cand if cand is not None else "")
        else:
            ap_list = sugerir_consecutivos_mod3(libres_pci, n_celdas, min_pci)
        ar_list = sugerir_rsi_con_sep(
            libres_rsi, n_celdas, df_site["VENDOR_CLEAN"].iloc[0], bc
        )

        allocator.register_assigned(cluster, [p for p in ap_list if isinstance(p, int)])

        resumen_list.append(
            {
                "Elemento": sc_upper,
                "NODO VDF": nodo_vdf,
                "Tecnología": f"{tech}_{bc}",
                "pci's": ";".join(str(x) for x in ap_list if x != ""),
                "rsi's": ";".join(str(x) for x in ar_list if x != ""),
                "TAC": tac_item,
                "TAC_VECINOS": ",".join(vecinos),
            }
        )
        for idx_det, cell_name in enumerate(
            [generar_nombre_celda(nodo_vdf, tech, band, i + 1) for i in range(n_celdas)]
        ):
            detalle_list.append(
                {
                    "NODO VDF": nodo_vdf,
                    "Celda": cell_name,
                    "PCI sugerido": ap_list[idx_det] if idx_det < len(ap_list) else "",
                    "RSI sugerido": ar_list[idx_det] if idx_det < len(ar_list) else "",
                    "TAC": tac_item,
                    "TAC_VECINOS": ",".join(vecinos),
                }
            )
    return resumen_list, detalle_list


def planificar_lnr700(
    site: str,
    n_celdas: int,
    df_pci_master: pd.DataFrame,
    df_rsi_5g_master: pd.DataFrame,
    tac_a_vecinos: dict,
    min_pci: int,
    min_rsi: int,
    modo_r: bool,
    manual_cache: dict,
) -> Tuple[list, list, list, list]:
    allocator = ClusterAllocator()
    res4, det4 = sugerir_pci_rsi(
        site,
        site,
        "4G",
        "700",
        n_celdas,
        df_pci_master,
        df_rsi_5g_master,
        tac_a_vecinos,
        min_pci,
        min_rsi,
        modo_r,
        allocator,
    )
    coord = [
        d.get("PCI sugerido") % 3 if isinstance(d.get("PCI sugerido"), int) else None
        for d in det4
    ]
    res5, det5 = sugerir_pci_rsi(
        site,
        site,
        "5G",
        "700",
        n_celdas,
        df_pci_master,
        df_rsi_5g_master,
        tac_a_vecinos,
        min_pci,
        min_rsi,
        modo_r,
        allocator,
        coord,
    )
    return res4, det4, res5, det5


def masivo_OSP_VDF(
    entrada_osp: str,
    correspondencia_zr: str,
    salida_resumen: str,
    salida_detalle: str,
    modo_r: bool,
    df_pci_master: pd.DataFrame,
    df_rsi_5g_master: pd.DataFrame,
    tac_a_vecinos: dict,
) -> None:
    df_req = pd.read_csv(
        ensure_csv(entrada_osp),
        dtype=str,
        sep=detect_separator(entrada_osp),
        encoding="utf-8",
        error_bad_lines=False,
    )
    df_req = map_peticion_columns(df_req)
    df_req["BAND_CLEAN"] = df_req.apply(
        lambda r: normaliza_banda(r.get("BAND", ""), r.get("TECH", "")), axis=1
    )
    resumen_all, detalle_all = [], []
    for (site, band), group in df_req.groupby(["SITE", "BAND_CLEAN"]):
        n_celdas = detectar_numero_sectores(site, df_pci_master)
        if band == "700":
            r4, d4, r5, d5 = planificar_lnr700(
                site,
                n_celdas,
                df_pci_master,
                df_rsi_5g_master,
                tac_a_vecinos,
                0,
                0,
                modo_r,
                {},
            )
            resumen_all.extend(r4 + r5)
            detalle_all.extend(d4 + d5)
        else:
            tech = group["TECH"].iloc[0]
            r, d = sugerir_pci_rsi(
                site,
                site,
                tech,
                band,
                n_celdas,
                df_pci_master,
                df_rsi_5g_master,
                tac_a_vecinos,
                0,
                0,
                modo_r,
            )
            resumen_all.extend(r)
            detalle_all.extend(d)
    pd.DataFrame(resumen_all).to_csv(
        salida_resumen, index=False, sep=";", encoding="utf-8-sig"
    )
    pd.DataFrame(detalle_all).to_csv(
        salida_detalle, index=False, sep=";", encoding="utf-8-sig"
    )
    print("Resumen masivo generado:")
    print(
        tabulate.tabulate(
            pd.DataFrame(resumen_all),
            headers="keys",
            tablefmt="github",
            showindex=False,
        )
    )
    print("\nDetalle masivo generado:")
    print(
        tabulate.tabulate(
            pd.DataFrame(detalle_all),
            headers="keys",
            tablefmt="github",
            showindex=False,
        )
    )
