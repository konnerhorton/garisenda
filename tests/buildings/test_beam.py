"""The beam's strains (docs/work/m4a-building-damage.md, AC 6 and 15)."""

import math

import numpy as np
import pytest

import garisenda as gs
from garisenda.buildings._beam import (
    POISSON_RATIO,
    bending_strain,
    diagonal_strain,
    section,
    total_bending_strain,
    total_diagonal_strain,
)

BURLAND_WROTH = gs.buildings.burland_wroth_beam()
TIMOSHENKO = gs.buildings.timoshenko_beam()

# Jones (2022), Example 13.2 (p. 490): masonry, H = 5.6 m, E/G = 2.6, with his
# own Delta/L and eps_h (sampled at 1 m), and his printed strains.
JONES = {
    "hogging": {
        "length": 16.0,
        "deflection_ratio": 3.04653e-4,
        "horizontal": 5.448e-4,
        "printed": (0.0005060, 0.0002302, 0.0010508, 0.0006130),
    },
    "sagging": {
        "length": 15.5,
        "deflection_ratio": 6.52738e-4,
        "horizontal": -1.1829e-3,
        "printed": (0.0010055, 0.0002361, -0.0001774, 0.0003903),
    },
}


def strains(mode, beam, *, deflection_ratio, length, horizontal, height=5.6):
    common = {
        "length": length,
        "height": height,
        "mode": mode,
        "youngs_to_shear_modulus_ratio": 2.6,
        "beam": beam,
    }
    eb = bending_strain(deflection_ratio, **common)
    ed = diagonal_strain(deflection_ratio, **common)
    return (
        eb,
        ed,
        total_bending_strain(eb, horizontal),
        total_diagonal_strain(ed, horizontal),
    )


@pytest.mark.parametrize("mode", ["hogging", "sagging"])
def test_jones_printed_strains_with_the_timoshenko_beam(mode):
    case = JONES[mode]
    eb, ed, _, _ = strains(
        mode,
        TIMOSHENKO,
        deflection_ratio=case["deflection_ratio"],
        length=case["length"],
        horizontal=case["horizontal"],
    )
    printed_eb, printed_ed, printed_ebt, printed_edt = case["printed"]
    # To half a unit in Jones's last printed digit (1e-7). He chains his
    # rounded eps_b and eps_d into Eqs. 9 and 10, so the totals are checked
    # from those: from the unrounded eps_d, hogging eps_dt is 0.00061306.
    assert abs(eb - printed_eb) <= 0.5e-7
    assert abs(ed - printed_ed) <= 0.5e-7
    horizontal = case["horizontal"]
    assert abs(total_bending_strain(printed_eb, horizontal) - printed_ebt) <= 0.5e-7
    assert abs(total_diagonal_strain(printed_ed, horizontal) - printed_edt) <= 0.5e-7


def test_burland_wroth_hogging_bending_strain():
    case = JONES["hogging"]
    eb, *_ = strains(
        "hogging",
        BURLAND_WROTH,
        deflection_ratio=case["deflection_ratio"],
        length=case["length"],
        horizontal=case["horizontal"],
    )
    assert abs(eb - 0.0004396) <= 0.5e-7


def test_the_named_methods():
    assert BURLAND_WROTH.shear_deflection_coefficient == 1.5
    assert TIMOSHENKO.shear_deflection_coefficient == 1.2
    assert BURLAND_WROTH.name != TIMOSHENKO.name


def test_sections():
    assert section("hogging", 6.0) == (6.0, 72.0)
    assert section("sagging", 6.0) == (3.0, 18.0)
    with pytest.raises(ValueError, match="'hogging' or 'sagging'"):
        section("level", 6.0)


@pytest.mark.parametrize("mode", ["hogging", "sagging"])
@pytest.mark.parametrize("length", [2.0, 18.0, 60.0])
@pytest.mark.parametrize("ratio", [2.6, 12.5])
def test_eqs_7_and_8_as_printed(mode, length, ratio):
    # Mair, Taylor & Burland (1996), p. 716, written out here on their own:
    # Eq. 7: Delta/L = (L/(12t) + 3IE/(2tLHG)) eps_b
    # Eq. 8: Delta/L = (1 + HL^2 G/(18IE)) eps_d
    height, deflection_ratio = 8.0, 2e-4
    t, inertia = (
        (height, height**3 / 3)
        if mode == "hogging"
        else (
            height / 2,
            height**3 / 12,
        )
    )
    eq7 = deflection_ratio / (
        length / (12 * t) + 3 * inertia * ratio / (2 * t * length * height)
    )
    eq8 = deflection_ratio / (1 + height * length**2 / (18 * inertia * ratio))
    common = {
        "length": length,
        "height": height,
        "mode": mode,
        "youngs_to_shear_modulus_ratio": ratio,
        "beam": BURLAND_WROTH,
    }
    assert bending_strain(deflection_ratio, **common) == pytest.approx(eq7, rel=1e-14)
    assert diagonal_strain(deflection_ratio, **common) == pytest.approx(eq8, rel=1e-14)


@pytest.mark.parametrize("mode", ["hogging", "sagging"])
@pytest.mark.parametrize("length", [2.0, 18.0, 60.0])
def test_the_timoshenko_beam_gives_the_larger_strains(mode, length):
    common = {
        "length": length,
        "height": 8.0,
        "mode": mode,
        "youngs_to_shear_modulus_ratio": 2.6,
    }
    for function in (bending_strain, diagonal_strain):
        assert function(2e-4, beam=TIMOSHENKO, **common) > function(
            2e-4, beam=BURLAND_WROTH, **common
        )


def test_eq_10_as_printed_and_never_negative():
    for eh in np.linspace(-5e-3, 5e-3, 41):
        for ed in (0.0, 1e-4, 2e-3):
            eq10 = 0.35 * eh + math.sqrt((0.65 * eh) ** 2 + ed**2)
            found = total_diagonal_strain(ed, eh)
            assert found == pytest.approx(eq10, rel=1e-12, abs=1e-18)
            assert found >= -1e-18
    assert POISSON_RATIO == 0.3


def test_eq_9_adds_the_horizontal_strain_with_its_sign():
    assert total_bending_strain(4e-4, -1e-4) == pytest.approx(3e-4)
