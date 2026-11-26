"""The statistics used everywhere: means per unit, paired differences between endings, bootstrap intervals.

The unit is the scenario (or vignette, target, action), never the single answer: repeated answers on
one prompt are nearly identical. Wordings of an ending are pooled within a unit.
"""

import random
import statistics as st
from collections import defaultdict


def boot(values, n=5000, seed=0):
    """Mean and bootstrap 95% interval (resampling the values, fixed seed).

    Each resample mean is exact and then rounded once, as statistics.mean computes it, so published intervals
    reproduce to the last digit (a float sum rounds twice and moves some printed endpoints by 0.1). It is done
    in integers, about ten times faster than statistics.mean: every float is an integer over a power of two,
    so over a common denominator a resample's sum is an integer sum. Resampling the integers draws the same
    positions as resampling the values (same seed, same length)."""
    rng = random.Random(seed)
    k = len(values)
    ratios = [float(v).as_integer_ratio() for v in values]
    denominator = max(d for _, d in ratios)
    numerators = [num * (denominator // d) for num, d in ratios]
    means = sorted(sum(rng.choices(numerators, k=k)) / (k * denominator) for _ in range(n))  # int / int rounds once
    return st.mean(values), means[int(0.025 * n)], means[int(0.975 * n) - 1]


def unit_means(rows, value="answer"):
    """{(unit, cond): mean of `value`} over the given answer rows."""
    cells = defaultdict(list)
    for r in rows:
        cells[(r["unit"], r["cond"])].append(float(r[value]))
    return {k: st.mean(v) for k, v in cells.items()}


def contrast(um, a, b):
    """Ending a minus ending b, paired within units: (mean, lo, hi, units up, units down, n units).
    Units with only one of the two endings are left out. "Up" and "down" count units that moved by more than
    2% of the range the unit means span (over every ending in `um`, so about 2 points on a 0-100 question).
    None if fewer than 2 units."""
    units = sorted({u for u, c in um if c == a} & {u for u, c in um if c == b})
    diffs = [um[(u, a)] - um[(u, b)] for u in units]
    if len(diffs) < 2:
        return None
    m, lo, hi = boot(diffs)
    tol = 0.02 * (max(um.values()) - min(um.values()) or 1)
    return m, lo, hi, sum(d > tol for d in diffs), sum(d < -tol for d in diffs), len(diffs)


def change(um_new, um_old, a, b):
    """How much (a minus b) changed from one set of answers to another, paired by unit."""
    d_new = {u: um_new[(u, a)] - um_new[(u, b)] for u, c in um_new if c == a and (u, b) in um_new}
    d_old = {u: um_old[(u, a)] - um_old[(u, b)] for u, c in um_old if c == a and (u, b) in um_old}
    units = sorted(set(d_new) & set(d_old))
    return boot([d_new[u] - d_old[u] for u in units]) if len(units) > 1 else None


def cond_mean(um, cond):
    """Mean over units of one ending's unit means."""
    return st.mean(v for (_, c), v in um.items() if c == cond)


def direction(c):
    """+1 or -1 if the interval of an estimate (mean, lo, hi, ...) excludes zero on that side, else 0."""
    return 0 if c is None else (+1 if c[1] > 0 else -1 if c[2] < 0 else 0)


def excludes_zero(c):
    return direction(c) != 0


def fmt(c, digits=1, counts=False):
    """'+23.2 [+15.3, +31.3] *' (the star marks an interval that excludes zero)."""
    if not c:
        return "n/a"
    m, lo, hi = c[:3]
    s = f"{m:+.{digits}f} [{lo:+.{digits}f}, {hi:+.{digits}f}]"
    if counts and len(c) > 3:
        s += f" {c[3]}up/{c[4]}dn"
    return s + (" *" if excludes_zero(c) else "  ")


def fmt_short(c, digits):
    """'+23.2*' for tables: the estimate, starred if its interval excludes zero."""
    return "—" if c is None else f"{c[0]:+.{digits}f}{'*' if direction(c) else ''}"


def fmt_full(c, digits, star=False):
    """'+23.2 [+15.3, +31.3]' for tables, starred on request."""
    if c is None:
        return "—"
    return f"{c[0]:+.{digits}f} [{c[1]:+.{digits}f}, {c[2]:+.{digits}f}]" + ("*" if star and direction(c) else "")


def digits_for(question):
    return 2 if question in ("sanction", "action", "performance") else 1
