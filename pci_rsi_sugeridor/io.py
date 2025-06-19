#!/usr/bin/env python3
# io.py: Módulo de I/O y CLI

import argparse
import logging
import os
import sys
from datetime import datetime

import pandas as pd
from core import (
    agrupar_tech,
    cargar_y_preprocesar_pci,
    cargar_y_preprocesar_rsi_5g,
    detectar_numero_sectores,
    ensure_csv,
    masivo_OSP_VDF,
    normaliza_banda,
    planificar_lnr700,
    preprocesar_TACAreas,
    sugerir_pci_rsi,
)

VERSION = "3.9"


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=level)
    # Reducir verbosidad de librerías externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sugeridor PCI/RSI ZN-ZR con pool virtual"
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["ZN", "ZR"],
        required=True,
        help="Modo de operación: ZN (N) o ZR (R)",
    )
    parser.add_argument(
        "-M",
        "--masivo",
        action="store_true",
        help="Ejecutar en modo masivo (CSV entrada)",
    )
    parser.add_argument(
        "-i", "--entrada", help="CSV de entrada (modo masivo) o SITE (modo individual)"
    )
    parser.add_argument(
        "-z", "--zr-corr", default="", help="CSV de correspondencias ZR (opcional)"
    )
    parser.add_argument(
        "-t",
        "--tech",
        choices=["4G", "5G", "2600R", "LTE", "NR"],
        help="Tecnología (solo en modo individual y banda ≠ 700)",
    )
    parser.add_argument(
        "-b", "--band", required=True, help="Banda (700,800,1800,2100,2600,3500,78,1)"
    )
    parser.add_argument("--min-pci", type=int, default=0, help="Valor mínimo de PCI")
    parser.add_argument("--min-rsi", type=int, default=0, help="Valor mínimo de RSI")
    parser.add_argument(
        "-o", "--output-dir", default="salida", help="Directorio de salida para CSVs"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Habilitar salida verbose (debug logs)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    logger.info(f"Iniciando Sugeridor PCI/RSI v{VERSION}")
    os.makedirs(args.output_dir, exist_ok=True)

    # Carga de datos maestros
    logger.debug("Cargando archivo maestro de PCI/RSI...")
    df_pci_master = cargar_y_preprocesar_pci("am_cellinfo_etldb.csv")
    if df_pci_master.empty:
        logger.error("No se pudo cargar el fichero maestro PCI/RSI. Abortando.")
        sys.exit(1)
    logger.info("Maestro PCI/RSI cargado correctamente.")

    logger.debug("Cargando fichero RSI 5G...")
    df_rsi_5g = cargar_y_preprocesar_rsi_5g(
        "gnodebfunctionmodule_nrducell.csv", df_pci_master
    )
    logger.info("RSI 5G cargado.")

    logger.debug("Cargando información de TAC vecinos...")
    tac_vecinos = preprocesar_TACAreas("TACAreas.xlsx")
    logger.info(f"{len(tac_vecinos)} entradas de TAC vecinos cargadas.")

    if args.masivo:
        if not args.entrada:
            logger.error("En modo masivo, --entrada <archivo.csv> es obligatorio.")
            sys.exit(1)
        resumen_csv = os.path.join(
            args.output_dir, f"resumen_masivo_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        detalle_csv = os.path.join(
            args.output_dir, f"detalle_masivo_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        logger.info("Ejecutando en modo masivo.")
        masivo_OSP_VDF(
            ensure_csv(args.entrada),
            ensure_csv(args.zr_corr) if args.zr_corr else "",
            resumen_csv,
            detalle_csv,
            args.mode == "ZR",
            df_pci_master,
            df_rsi_5g,
            tac_vecinos,
        )
    else:
        if not args.entrada:
            logger.error("En modo individual, --entrada <SITE> es obligatorio.")
            sys.exit(1)
        site = args.entrada.strip()
        band_norm = normaliza_banda(args.band, args.tech or "")
        n_sectores = detectar_numero_sectores(site, df_pci_master)
        logger.info(f"Procesando SITE={site}, banda={band_norm}, sectores={n_sectores}")

        if band_norm == "700":
            logger.info("Banda 700 detectada: aplicando planificar_lnr700.")
            resumen4, detalle4, resumen5, detalle5 = planificar_lnr700(
                site,
                n_sectores,
                df_pci_master,
                df_rsi_5g,
                tac_vecinos,
                args.min_pci,
                args.min_rsi,
                args.mode == "ZR",
                {},
            )
            resumen = resumen4 + resumen5
            detalle = detalle4 + detalle5
        else:
            if not args.tech:
                logger.error("Debe indicar --tech cuando la banda no es 700.")
                sys.exit(1)
            resumen, detalle = sugerir_pci_rsi(
                site,
                site,
                args.tech,
                args.band,
                n_sectores,
                df_pci_master,
                df_rsi_5g,
                tac_vecinos,
                args.min_pci,
                args.min_rsi,
                args.mode == "ZR",
            )

        if resumen:
            df_res = pd.DataFrame(resumen)
            print(df_res.to_markdown(index=False))
        else:
            logger.warning("No se generó resumen para los criterios dados.")

        if detalle:
            df_det = pd.DataFrame(detalle)
            print(df_det.to_markdown(index=False))
        else:
            logger.warning("No se generó detalle para los criterios dados.")


if __name__ == "__main__":
    main()
