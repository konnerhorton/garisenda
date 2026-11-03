"""A superposition is the exact sum of its sources (M2 (a), AC 2)."""

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

import garisenda as gs
from garisenda.sources._movement import VERDICTS

u = gs.units
ARRAYS = ("displacement", "gradient", "hessian", "third_derivative")


@st.composite
def superpositions(draw):
    """Two or three troughs: a tunnel, a parallel twin and maybe a crossing."""
    diameter = draw(st.floats(2.0, 12.0))
    first = gs.sources.IdealizedTunnel(
        reference_point=(draw(st.floats(-500, 500)), draw(st.floats(-500, 500))),
        azimuth=draw(st.floats(0.0, 360.0)) * u.degree,
        diameter=diameter,
        axis_depth=draw(st.floats(1.0, 40.0)) + diameter / 2,
        reference_station=draw(st.floats(-1e3, 1e3)),
    )
    twin = first.parallel(
        offset=draw(st.floats(1.0, 60.0)) * diameter * draw(st.sampled_from([-1, 1])),
        diameter=diameter,
        axis_depth=draw(st.floats(1.0, 40.0)) + diameter / 2,
    )
    tunnels = {"first": first, "twin": twin}
    if draw(st.booleans()):
        deepest = max(first.axis_depth, twin.axis_depth)
        tunnels["crossing"] = gs.sources.IdealizedTunnel(
            reference_point=(first.reference_x, first.reference_y),
            azimuth=(np.degrees(first.azimuth) + draw(st.floats(10.0, 170.0)))
            * u.degree,
            diameter=diameter,
            axis_depth=deepest + diameter + draw(st.floats(0.0, 20.0)),
        )
    sources = {
        name: gs.sources.transverse_surface_trough(
            tunnel,
            volume_loss=draw(st.floats(0.1, 5.0)) * u.percent,
            trough_width_parameter=draw(st.floats(0.2, 1.0)),
        )
        for name, tunnel in tunnels.items()
    }
    return sources, gs.superpose(**sources)


@st.composite
def points(draw, sources):
    first = sources["first"].tunnel
    crown = min(
        source.tunnel.axis_depth - source.tunnel.diameter / 2
        for source in sources.values()
    )
    count = draw(st.integers(1, 6))
    spread = st.floats(-150, 150)
    x = [first.reference_x + draw(spread) for _ in range(count)]
    y = [first.reference_y + draw(spread) for _ in range(count)]
    # At the surface, or below it (flagged), always above every crown.
    depth = [draw(st.sampled_from([0.0, crown / 2])) for _ in range(count)]
    return x, y, depth


@given(st.data())
def test_arrays_are_the_sums_and_the_verdict_the_worst(data):
    sources, combined = data.draw(superpositions())
    x, y, depth = data.draw(points(sources))
    movement = combined.evaluate(x=x, y=y, depth=depth)
    parts = [source.evaluate(x=x, y=y, depth=depth) for source in sources.values()]
    for name in ARRAYS:
        expected = sum(getattr(part, name) for part in parts)
        scale = max(float(np.max(np.abs(getattr(part, name)))) for part in parts)
        np.testing.assert_allclose(
            getattr(movement, name), expected, rtol=1e-12, atol=1e-12 * scale
        )
    worst = [
        VERDICTS[max(VERDICTS.index(part.verdict[n]) for part in parts)]
        for n in range(len(x))
    ]
    assert movement.verdict.tolist() == worst
    assert len(movement.flags) == sum(len(part.flags) for part in parts)
    assert {flag.source for flag in movement.flags} <= set(sources)
