"""The statistics every analysis uses: per-unit means, paired contrasts, bootstrap intervals."""

import random
import statistics as st

import pytest

from outcome_bias.stats import (
    boot,
    change,
    cond_mean,
    contrast,
    direction,
    excludes_zero,
    fmt,
    fmt_full,
    fmt_short,
    unit_means,
)


def rows(cells):
    """cells: {(unit, cond): [answers]} -> answer rows."""
    return [dict(unit=u, cond=c, answer=a) for (u, c), answers in cells.items() for a in answers]


def test_boot_is_deterministic_and_brackets_the_mean():
    values = [1.0, 4.0, 2.0, 8.0, 5.0, 7.0]
    m, lo, hi = boot(values)
    assert m == st.mean(values)
    assert lo < m < hi
    assert boot(values) == (m, lo, hi)


def test_boot_keeps_its_random_stream():
    """Pinned before the resampling mean was sped up: the same seed must give the same interval, or every
    published interval would shift."""
    values = [-5.722, 12.654, 2.197, 16.235, 17.543, -16.068, -19.21, 30.248, -4.439, -5.94, 39.739, 8.216, 30.188,
              8.581, 18.344, -10.963, 18.092, 32.083, 11.391, 24.475, 20.285]
    assert boot(values) == (10.853761904761905, 3.8891904761904756, 17.80557142857143)


def reference_boot(values, n=5000, seed=0):
    """boot as first written, with statistics.mean (exact, slow)."""
    rng = random.Random(seed)
    means = sorted(st.mean(rng.choices(values, k=len(values))) for _ in range(n))
    return st.mean(values), means[int(0.025 * n)], means[int(0.975 * n) - 1]


@pytest.mark.parametrize("seed", range(6))
def test_boot_matches_statistics_mean_exactly(seed):
    """Bit for bit, including values on rounding boundaries (unit means of 0-100 answers are often multiples
    of 0.2, and their resample means land exactly on x.x5)."""
    r = random.Random(seed)
    k = r.choice([3, 12, 21])
    values = [r.choice([round(r.uniform(-60, 60), 1), r.randint(-50, 50) / 5, r.random() * 1e-3]) for _ in range(k)]
    assert boot(values, n=400) == reference_boot(values, n=400)


def test_boot_of_a_constant_has_no_width():
    assert boot([3.0] * 5) == (3.0, 3.0, 3.0)


def test_unit_means_pool_answers_within_a_cell():
    um = unit_means(rows({("a", "harm"): [10, 20], ("a", "payoff"): [5]}))
    assert um == {("a", "harm"): 15, ("a", "payoff"): 5}


def test_contrast_pairs_within_units_and_skips_unpaired_ones():
    um = {("a", "harm"): 30, ("a", "payoff"): 10, ("b", "harm"): 25, ("b", "payoff"): 20,
          ("c", "harm"): 90}  # c has no payoff answer: left out
    m, lo, hi, up, down, n = contrast(um, "harm", "payoff")
    assert m == pytest.approx(12.5)
    assert (up, down, n) == (2, 0, 2)
    assert lo <= m <= hi


def test_contrast_counts_units_that_moved_by_more_than_two_percent_of_the_observed_range():
    # range of unit means = 100 - 0, so the tolerance is 2 points
    um = {("a", "x"): 100, ("a", "y"): 0, ("b", "x"): 51, ("b", "y"): 50, ("c", "x"): 40, ("c", "y"): 45}
    _, _, _, up, down, _ = contrast(um, "x", "y")
    assert (up, down) == (1, 1), "b moved by 1 point, under the tolerance"


def test_contrast_needs_two_units():
    assert contrast({("a", "x"): 1, ("a", "y"): 0}, "x", "y") is None


def test_change_compares_the_same_contrast_across_two_runs():
    old = {("a", "x"): 10, ("a", "y"): 0, ("b", "x"): 20, ("b", "y"): 0}
    new = {("a", "x"): 5, ("a", "y"): 0, ("b", "x"): 10, ("b", "y"): 0}
    assert change(new, old, "x", "y")[0] == pytest.approx(-7.5)
    assert change(new, {("a", "x"): 1, ("a", "y"): 0}, "x", "y") is None


def test_cond_mean_averages_units():
    assert cond_mean({("a", "x"): 10, ("b", "x"): 20, ("a", "y"): 99}, "x") == 15


def test_direction_and_excludes_zero():
    assert direction((5, 1, 9)) == +1
    assert direction((-5, -9, -1)) == -1
    assert direction((1, -1, 3)) == 0
    assert direction(None) == 0
    assert excludes_zero((5, 1, 9)) and not excludes_zero((1, -1, 3)) and not excludes_zero(None)


def test_formats():
    c = (23.24, 15.31, 31.29, 18, 0, 21)
    assert fmt(c) == "+23.2 [+15.3, +31.3] *"
    assert fmt(c, counts=True) == "+23.2 [+15.3, +31.3] 18up/0dn *"
    assert fmt((1.0, -1.0, 3.0)) == "+1.0 [-1.0, +3.0]  "
    assert fmt(None) == "n/a"
    assert fmt_short(c, 1) == "+23.2*"
    assert fmt_short((1.0, -1.0, 3.0), 2) == "+1.00"
    assert fmt_full(c, 1) == "+23.2 [+15.3, +31.3]"
    assert fmt_full(c, 1, star=True) == "+23.2 [+15.3, +31.3]*"
    assert fmt_short(None, 1) == fmt_full(None, 1) == "—"
