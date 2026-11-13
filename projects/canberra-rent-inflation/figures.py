"""Portfolio figures from the reviewed ABS panels."""

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import PercentFormatter

from analysis import CASE_CITIES, CITIES, growth_table, rebase, rent_yoy

TEAL, BLUE, OCHRE, INK = "#086d69", "#315988", "#9d572b", "#20353d"


def axes(title, ylabel, size):
    fig, ax = plt.subplots(figsize=size, layout="constrained")
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=INK, pad=11)
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#879b9f")
    ax.grid(axis="y", color="#dce5e6", linewidth=0.7)
    ax.set_axisbelow(True)
    return fig, ax


def date_axis(ax, dates):
    ticks = [dates[0], *[date for date in dates[1:-1] if date.month == 1], dates[-1]]
    ax.set_xticks(ticks, [date.strftime("%b %Y") for date in ticks])
    ax.margins(x=0.025)


def city_lines(ax, data):
    for metric, label, colour, style in (
        ("Rents", "Rents", TEAL, "-"),
        ("All groups CPI", "All groups CPI", BLUE, "--"),
    ):
        ax.plot(data.index, data[metric], label=label, color=colour, linestyle=style, linewidth=2.2)
        ax.scatter(data.index[-1], data[metric].iloc[-1], color=colour, s=24, zorder=3)
    ax.set_ylim(99, 110.2)
    ax.set_yticks([100, 105, 110])


def plot_city(monthly, city):
    data = rebase(monthly[city])
    fig, ax = axes(f"{city} rent and overall prices", "Index (Apr 2024 = 100)", (7.5, 3.4))
    city_lines(ax, data)
    date_axis(ax, data.index)
    ax.legend(frameon=False, loc="upper left", ncols=2)
    return fig


def plot_canberra(monthly):
    return plot_city(monthly, "Canberra")


def plot_city_panels(monthly):
    fig, panels = plt.subplots(1, 3, figsize=(8.5, 2.22), sharey=True, layout="constrained")
    for ax, city in zip(panels, CASE_CITIES):
        data = rebase(monthly[city])
        city_lines(ax, data)
        ax.set_title(city, loc="left", fontsize=11, fontweight="bold", color=INK)
        ax.set_xticks([data.index[0], data.index[-1]], ["Apr 2024", "Sep 2026"])
        ax.tick_params(labelsize=8, length=0)
        ax.spines[["top", "left", "right", "bottom"]].set_visible(False)
        ax.grid(axis="y", color="#dce5e6", linewidth=.7)
        ax.set_axisbelow(True)
    return fig


def plot_rent_yoy(monthly):
    data = rent_yoy(monthly)
    fig, ax = axes("Annual rent inflation across cities", "Change from a year earlier", (7.5, 3.4))
    for city, colour, style in zip(CITIES, (TEAL, BLUE, OCHRE), ("-", "--", "-.")):
        ax.plot(data.index, data[city], label=city, color=colour, linestyle=style, linewidth=2)
    date_axis(ax, data.index)
    ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.legend(frameon=False, loc="upper right", ncols=3)
    return fig


def plot_historical(quarterly):
    windows = {
        "Dec 2019 to Sep 2025": "2019-12-01",
        "Sep 2022 to Sep 2025": "2022-09-01",
    }
    gaps = pd.DataFrame({label: growth_table(quarterly, start, "2025-09-01")["Rent minus CPI (pp)"]
                         for label, start in windows.items()})
    fig, ax = axes("Rent growth relative to local CPI", "Cumulative growth gap (percentage points)", (7.5, 3.6))
    ax.bar([i - .17 for i in range(3)], gaps.iloc[:, 0], width=.33, color=TEAL, label=gaps.columns[0])
    ax.bar([i + .17 for i in range(3)], gaps.iloc[:, 1], width=.33, facecolor="white",
           edgecolor=OCHRE, hatch="//", label=gaps.columns[1])
    ax.axhline(0, color=INK, linewidth=.8)
    ax.set_xticks(range(3), gaps.index)
    ax.set_ylim(-10, 13)
    ax.legend(frameon=False, loc="upper left", ncols=2)
    return fig
