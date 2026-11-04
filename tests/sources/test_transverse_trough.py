"""The transverse trough at depth against the M2 (b) spec's hand calculation."""

import math

import numpy as np
import pytest

import garisenda as gs

u = gs.units
REL = 1e-6  # hand calculation carried to 8 figures (spec, acceptance criteria)
ABS = 1e-15  # for the hand calculation's zeros


def tunnel(**changes):
    arguments = {
        "reference_point": (0, 0),
        "azimuth": 0 * u.degree,
        "diameter": 6.0,
        "axis_depth": 20.0,
    }
    arguments.update(changes)
    return gs.sources.IdealizedTunnel(**arguments)


def mair(tunnel_=None):
    return gs.sources.transverse_trough(
        tunnel_ or tunnel(),
        volume_loss=1 * u.percent,
        trough_width=gs.sources.mair_trough_width(),
    )


def linear(tunnel_=None, k=0.5):
    return gs.sources.transverse_trough(
        tunnel_ or tunnel(),
        volume_loss=1 * u.percent,
        trough_width=gs.sources.linear_trough_width(trough_width_parameter=k),
    )


def at(source, offset, depth, station=0.0):
    """Evaluate at a station and offset from the tunnel's reference point."""
    t = source.tunnel
    offset = np.atleast_1d(np.asarray(offset, dtype=float))
    x = t.reference_x + station * t.tangent[0] + offset * t.normal[0]
    y = t.reference_y + station * t.tangent[1] + offset * t.normal[1]
    return source.evaluate(x=x, y=y, depth=np.broadcast_to(depth, offset.shape))


def normal_part(source, movement):
    n = np.array([*source.tunnel.normal, 0.0])
    return movement.displacement @ n


# Case A, Mair's method: (z, o, S, u_n).
CASE_A = [
    (0, 0, 1.12798272e-2, 0.0),
    (0, 10, 6.84156105e-3, -2.22350734e-3),
    (10, 0, 1.67108552e-2, 0.0),
    (10, 6.75, 1.01356460e-2, -3.29408495e-3),
    (10, 10, 5.57707713e-3, -2.68525936e-3),
    (15, 5.125, 1.33493874e-2, -4.33855091e-3),
    (15, 10, 3.27999437e-3, -2.07999643e-3),
    (17, 4.475, 1.52884046e-2, -4.96873149e-3),
]
# Case B, linear method with k = 0.5, and M1's values at z = 0, o = 7.
CASE_B = [
    (0, 10, 6.84156105e-3, -3.42078053e-3),
    (10, 0, 2.25596545e-2, 0.0),
    (10, 5, 1.36831221e-2, -6.84156105e-3),
    (10, 10, 3.05311723e-3, -3.05311723e-3),
    (15, 2.5, 2.73662442e-2, -1.36831221e-2),
    (0, 7, 8.82877197e-3, -3.09007019e-3),
]
AZIMUTHS = [0.0, 30.0]


def check(source, depth, offset, settlement, horizontal):
    movement = at(source, offset, depth, station=12.5)
    assert movement.displacement[0, 2] == pytest.approx(settlement, rel=REL)
    assert normal_part(source, movement)[0] == pytest.approx(
        horizontal, rel=REL, abs=ABS
    )
    assert movement.verdict[0] == "within"
    assert movement.flags == ()


# AC 1: golden values through evaluate


@pytest.mark.parametrize("azimuth", AZIMUTHS)
@pytest.mark.parametrize(("depth", "offset", "settlement", "horizontal"), CASE_A)
def test_mair_against_case_a(azimuth, depth, offset, settlement, horizontal):
    source = mair(tunnel(azimuth=azimuth * u.degree))
    check(source, depth, offset, settlement, horizontal)


@pytest.mark.parametrize("azimuth", AZIMUTHS)
@pytest.mark.parametrize(("depth", "offset", "settlement", "horizontal"), CASE_B)
def test_linear_against_case_b(azimuth, depth, offset, settlement, horizontal):
    source = linear(tunnel(azimuth=azimuth * u.degree))
    check(source, depth, offset, settlement, horizontal)


def test_normal_along_x_at_azimuth_zero():
    assert tunnel().normal == pytest.approx((1.0, 0.0), abs=1e-15)
    movement = mair().evaluate(x=10.0, y=3.0, depth=0.0)
    assert movement.displacement[0, 0] == pytest.approx(-2.22350734e-3, rel=REL)
    assert movement.displacement[0, 1] == pytest.approx(0.0, abs=1e-18)


def test_movement_is_toward_the_axis_on_both_sides():
    movement = at(mair(), [-10.0, 10.0], 10.0)
    horizontal = normal_part(mair(), movement)
    assert horizontal[0] == pytest.approx(2.68525936e-3, rel=REL)
    assert horizontal[1] == pytest.approx(-2.68525936e-3, rel=REL)
    assert movement.displacement[0, 2] == pytest.approx(5.57707713e-3, rel=REL)


# AC 2: case C, Mair's method at o = 5 m, z = 10 m: (a, b) -> (S, u_n).
CASE_C = {
    (0, 0): (1.27013730e-2, -3.05773794e-3),
    (1, 0): (-1.39384066e-3, -2.75993356e-4),
    (0, 1): (2.75993356e-4, -2.13667264e-4),
    (2, 0): (-1.25808937e-4, 1.64509029e-4),
    (1, 1): (-1.64509029e-4, 1.30268876e-5),
    (0, 2): (-1.30268876e-5, -1.74392636e-5),
    (3, 0): (7.49898710e-5, 1.19284936e-7),
    (2, 1): (-1.19284936e-7, 2.37911321e-5),
    (1, 2): (-2.37911321e-5, 7.60915632e-6),
    (0, 3): (-7.60915632e-6, -6.87170813e-7),
}


def read(movement, n, a, b):
    """Read the (a, b) derivative of S and u_n from the assembled tensors."""
    g = n
    e = np.array([0.0, 0.0, 1.0])
    tensors = {
        0: movement.displacement[0],
        1: movement.gradient[0],
        2: movement.hessian[0],
        3: movement.third_derivative[0],
    }
    tensor = tensors[a + b]
    for _ in range(a):
        tensor = tensor @ g
    for _ in range(b):
        tensor = tensor @ e
    return tensor[2], tensor @ n


@pytest.mark.parametrize("azimuth", AZIMUTHS)
@pytest.mark.parametrize(("order", "expected"), CASE_C.items())
def test_derivatives_against_case_c(azimuth, order, expected):
    source = mair(tunnel(azimuth=azimuth * u.degree))
    movement = at(source, 5.0, 10.0, station=-7.0)
    n = np.array([*source.tunnel.normal, 0.0])
    settlement, horizontal = read(movement, n, *order)
    assert settlement == pytest.approx(expected[0], rel=REL)
    assert horizontal == pytest.approx(expected[1], rel=REL)


def test_derivatives_against_a_central_difference_in_depth():
    step = 1e-3
    ahead = at(mair(), 5.0, 10.0 + step).displacement[0, 2]
    behind = at(mair(), 5.0, 10.0 - step).displacement[0, 2]
    assert (ahead - behind) / (2 * step) == pytest.approx(2.7599335e-4, rel=1e-7)


# AC 4: against M1, the fixed cases


def surface(k=0.5, tunnel_=None):
    return gs.sources.transverse_surface_trough(
        tunnel_ or tunnel(), volume_loss=1 * u.percent, trough_width_parameter=k
    )


OFFSETS = [-25.0, -10.0, -3.3, 0.0, 4.1, 7.0, 10.0, 17.32, 30.0]


@pytest.mark.parametrize("azimuth", AZIMUTHS)
def test_linear_at_the_surface_is_m1(azimuth):
    t = tunnel(azimuth=azimuth * u.degree)
    mine, theirs = at(linear(t), OFFSETS, 0.0), at(surface(tunnel_=t), OFFSETS, 0.0)
    np.testing.assert_allclose(
        mine.displacement, theirs.displacement, rtol=1e-12, atol=1e-18
    )
    np.testing.assert_allclose(
        mine.gradient[:, :, :2], theirs.gradient[:, :, :2], rtol=1e-12, atol=1e-18
    )


def test_mair_at_the_surface_is_m1_settlement_and_065_of_its_horizontal():
    mine, theirs = at(mair(), OFFSETS, 0.0), at(surface(), OFFSETS, 0.0)
    np.testing.assert_allclose(
        mine.displacement[:, 2], theirs.displacement[:, 2], rtol=1e-12
    )
    np.testing.assert_allclose(
        mine.displacement[:, :2],
        0.65 * theirs.displacement[:, :2],
        rtol=1e-12,
        atol=1e-18,
    )
    assert at(surface(), 10.0, 0.0).displacement[0, 0] == pytest.approx(
        -3.42078053e-3, rel=REL
    )


# AC 5: validity below the crown

CROWN_REASON = "Below the tunnel crown: the subsurface trough applies only above"


@pytest.mark.parametrize(
    ("make", "width", "settlement", "horizontal"),
    [
        (mair, 4.475, 1.35027643e-2, -4.90323843e-3),
        (linear, 1.5, 2.90712742e-4, -4.84521236e-4),
    ],
)
def test_case_d_below_the_crown(make, width, settlement, horizontal):
    source = make()
    movement = at(source, [5.0, 5.0, 5.0], [10.0, 19.0, 17.0005])
    assert list(movement.verdict) == ["within", "outside", "within"]
    assert movement.displacement[1, 2] == pytest.approx(settlement, rel=REL)
    assert normal_part(source, movement)[1] == pytest.approx(horizontal, rel=REL)
    crown = at(source, 5.0, 17.0)
    np.testing.assert_array_equal(movement.displacement[1], crown.displacement[0])
    assert source.width_at(19.0) == pytest.approx(width, rel=1e-12)
    (flag,) = movement.flags
    assert flag.verdict == "outside"
    assert flag.reason.startswith(CROWN_REASON)
    assert "(Bracegirdle et al. 1996, p. 660" in flag.reason
    assert "another method or numerical analysis" in flag.reason
    assert flag.limit == "depth at most z0 - D/2 = 17 m (the crown)"
    assert flag.points == (1,)


def test_only_the_linear_flag_says_the_limit_is_garisendas():
    mine = at(linear(), 5.0, 19.0).flags[0].reason
    theirs = at(mair(), 5.0, 19.0).flags[0].reason
    assert "applied to the linear method by garisenda" in mine
    assert "garisenda" not in theirs


@pytest.mark.parametrize("make", [mair, linear])
def test_depth_derivatives_below_the_crown_are_exactly_zero(make):
    movement = at(
        make(tunnel(azimuth=30 * u.degree)), [5.0, -4.0, 12.0], [19.0, 21.0, 30.0]
    )
    assert set(movement.verdict) == {"outside"}
    assert np.all(movement.gradient[:, :, 2] == 0)
    assert np.all(movement.hessian[:, :, 2, :] == 0)
    assert np.all(movement.hessian[:, :, :, 2] == 0)
    for axis in (2, 3, 4):
        assert np.all(np.take(movement.third_derivative, 2, axis=axis) == 0)
    assert np.all(movement.hessian[:, 2, 0, 0] != 0)


@pytest.mark.parametrize("make", [mair, linear])
def test_inside_the_bore_and_above_the_surface_raise(make):
    with pytest.raises(ValueError, match=r"inside the bore can't be evaluated: \[1\]"):
        at(make(), [5.0, 0.0], [19.0, 18.0])
    with pytest.raises(ValueError, match=r"above the ground surface.*\[0\]"):
        at(make(), [5.0, 5.0], [-0.01, 1.0])


def test_a_point_just_above_the_surface_is_within():
    assert at(mair(), 5.0, -0.0005).verdict[0] == "within"


# AC 8: the trough's inputs and records


def test_trough_width_missing_raises_the_judgment_error():
    with pytest.raises(TypeError, match="trough_width is a required design judgment"):
        gs.sources.transverse_trough(tunnel(), volume_loss=1 * u.percent)


@pytest.mark.parametrize("value", [0.5, "mair", 0.5 * u.dimensionless])
def test_trough_width_not_a_method_raises_naming_both(value):
    with pytest.raises(
        TypeError, match=r"mair_trough_width\(\).*linear_trough_width\("
    ):
        gs.sources.transverse_trough(
            tunnel(), volume_loss=1 * u.percent, trough_width=value
        )


def test_volume_loss_is_checked_as_m1():
    with pytest.raises(TypeError, match="volume_loss needs a pint quantity"):
        gs.sources.transverse_trough(
            tunnel(), volume_loss=0.01, trough_width=gs.sources.mair_trough_width()
        )
    with pytest.raises(ValueError, match="volume_loss must be more than 0"):
        gs.sources.transverse_trough(
            tunnel(),
            volume_loss=0 * u.percent,
            trough_width=gs.sources.mair_trough_width(),
        )


TUNNEL_RECORDS = [entry.name for entry in tunnel().inputs]
CONSTANTS = [
    "depth_tolerance",
    "critical_distance_sampling",
    "critical_distance_tolerance",
]


def test_mair_records():
    source = mair()
    names = [entry.name for entry in source.inputs]
    assert names == [*TUNNEL_RECORDS, "volume_loss", "trough_width", *CONSTANTS]
    records = {entry.name: entry for entry in source.inputs}
    assert records["trough_width"].value == "Mair et al. (1993), clay"
    assert records["trough_width"].kind == "design judgment"
    assert records["trough_width"].given_as == "method"
    assert records["depth_tolerance"].value == 1e-3 * u.m
    assert records["critical_distance_sampling"].value.m == pytest.approx(1 / 8)
    assert records["critical_distance_tolerance"].value == 1e-9 * u.m
    for name in CONSTANTS:
        assert records[name].kind == "constant or setting"
    (method,) = source.method
    assert method.name == "Transverse Gaussian trough at depth"
    assert "i(z) = c0 z0 + c1 (z0 - z)" in method.equations
    assert "u_n(o, z) = -c1 r S" in method.equations
    assert "Bracegirdle et al. (1996), Eq. 1, p. 660" in method.source
    assert "Mair & Taylor (1997)" in method.source
    assert any("clays" in text for text in source.assumptions)
    assert any("Constant volume" in text for text in source.assumptions)


def test_linear_records():
    source = linear(k=gs.Sourced(0.4, source="Basis of design"))
    names = [entry.name for entry in source.inputs]
    assert names == [
        *TUNNEL_RECORDS,
        "volume_loss",
        "trough_width",
        "trough_width_parameter",
        *CONSTANTS,
    ]
    records = {entry.name: entry for entry in source.inputs}
    assert records["trough_width"].value == "linear"
    assert records["trough_width_parameter"].value.m == 0.4
    assert records["trough_width_parameter"].source == "Basis of design"
    assert any("their choice" in text for text in source.assumptions)


def test_trough_width_keeps_its_source():
    source = gs.sources.transverse_trough(
        tunnel(),
        volume_loss=1 * u.percent,
        trough_width=gs.Sourced(gs.sources.mair_trough_width(), source="GI report"),
    )
    records = {entry.name: entry for entry in source.inputs}
    assert records["trough_width"].source == "GI report"
    assert math.isclose(source.width_at(0.0), 10.0)
