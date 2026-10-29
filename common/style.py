"""Estilo gráfico compartido (paleta Okabe–Ito, apta para daltonismo)."""
from __future__ import annotations

import matplotlib.pyplot as plt

REGIONES_ES = {
    "East Asia & Pacific": "Asia Oriental y Pacífico",
    "Europe & Central Asia": "Europa y Asia Central",
    "Latin America & Caribbean": "América Latina y Caribe",
    "Middle East & North Africa": "Medio Oriente y Norte de África",
    "North America": "Norteamérica",
    "South Asia": "Asia Meridional",
    "Sub-Saharan Africa": "África Subsahariana",
}
COLORES = {
    "East Asia & Pacific": "#0072B2",
    "Europe & Central Asia": "#56B4E9",
    "Latin America & Caribbean": "#009E73",
    "Middle East & North Africa": "#E69F00",
    "North America": "#000000",
    "South Asia": "#CC79A7",
    "Sub-Saharan Africa": "#D55E00",
}
FUENTE = "Fuente: Banco Mundial (WDI), OMS (GHED), PNUD vía Our World in Data. Elaboración propia."


def aplicar_estilo() -> None:
    """Configura matplotlib con un estilo limpio y legible."""
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 160, "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "axes.titleweight": "bold",
        "axes.titlesize": 12, "legend.frameon": False,
    })


def pie_fuente(fig, texto: str = FUENTE) -> None:
    """Agrega la fuente al pie de la figura."""
    fig.text(0.01, 0.005, texto, fontsize=7, color="#555555", ha="left", va="bottom")
