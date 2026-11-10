"""Tests for gs.presets against the M3 (b) spec's AC 11 (decisions 13-16)."""

import pytest

import garisenda as gs
from garisenda._inputs import preset_caveats, record

u = gs.units

TABLE_2 = [
    (
        "lead_yarn_gas_main_with_history_of_leaks",
        "lead-yarn joint in gas main with history of leaks",
        0.0,
        0.0,
    ),
    ("lead_yarn_sound_gas_main", "lead-yarn joint in sound gas main", 1.0, 10.0),
    ("lead_yarn_water_main", "lead-yarn joint in water mains", 1.5, 15.0),
    ("rubber_gasket", "rubber gasket joint in gas or water mains", 2.5, 25.0),
]


@pytest.mark.parametrize(("joint", "description", "rotation", "pullout"), TABLE_2)
def test_cast_iron_joint_limits(joint, description, rotation, pullout):
    limits = gs.presets.cast_iron_joint_limits(joint=joint)
    assert isinstance(limits.rotation, gs.presets.Preset)
    assert isinstance(limits.rotation, gs.Sourced)
    assert limits.rotation.value == rotation * u.degree
    assert limits.pullout.value == pullout * u.mm
    for value in (limits.rotation, limits.pullout):
        assert value.source == (
            f"gs.presets.cast_iron_joint_limits(joint={joint!r}): Bracegirdle et "
            f"al. (1996), Table 2, p. 661, after Attewell et al. (1986), "
            f"{description!r}"
        )
        assert any("Attewell et al. hasn't been read" in c for c in value.caveats)
    assert any("calibrated with the shortcut" in c for c in limits.pullout.caveats)
    assert not any("calibrated" in c for c in limits.rotation.caveats)
    none_row = rotation == 0
    assert any("'none'" in c for c in limits.rotation.caveats) is none_row


def test_the_decision_12_example_source():
    limits = gs.presets.cast_iron_joint_limits(joint="lead_yarn_water_main")
    assert limits.rotation.source == (
        "gs.presets.cast_iron_joint_limits(joint='lead_yarn_water_main'): "
        "Bracegirdle et al. (1996), Table 2, p. 661, after Attewell et al. "
        "(1986), 'lead-yarn joint in water mains'"
    )


@pytest.mark.parametrize(
    ("material", "description", "tensile", "compressive"),
    [
        ("grey_iron", "pit cast and spun cast grey iron", 100, 1200),
        ("ductile_iron", "ductile iron", 500, 700),
    ],
)
def test_iron_strain_limits(material, description, tensile, compressive):
    limits = gs.presets.iron_strain_limits(material=material)
    assert limits.tensile.value.to("dimensionless").magnitude == pytest.approx(
        tensile * 1e-6
    )
    assert limits.compressive.value.to("dimensionless").magnitude == pytest.approx(
        compressive * 1e-6
    )
    for value in (limits.tensile, limits.compressive):
        assert value.source == (
            f"gs.presets.iron_strain_limits(material={material!r}): Bracegirdle "
            f"et al. (1996), Table 4, p. 662, {description!r}"
        )
        assert len(value.caveats) == 1
        assert "otherwise sound pipes" in value.caveats[0]


@pytest.mark.parametrize(
    ("diameter", "situation", "expected"),
    [
        ("over_300_mm", "general", 200),
        ("300_mm_or_less", "general", 150),
        ("over_300_mm", "particularly_adverse", 150),
        ("300_mm_or_less", "particularly_adverse", 100),
    ],
)
def test_grey_iron_tensile_strain_limit(diameter, situation, expected):
    limit = gs.presets.grey_iron_tensile_strain_limit(
        diameter=diameter, situation=situation
    )
    assert limit.value.to("dimensionless").magnitude == pytest.approx(expected * 1e-6)
    assert limit.source.startswith(
        f"gs.presets.grey_iron_tensile_strain_limit(diameter={diameter!r}, "
        f"situation={situation!r}): Bracegirdle et al. (1996), p. 662, after "
        "Herbert and Leach (1990), "
    )
    assert "tensile strain limits only" in limit.caveats[0]


@pytest.mark.parametrize(
    ("preset", "name"),
    [
        (gs.presets.cast_iron_joint_limits, "joint"),
        (gs.presets.iron_strain_limits, "material"),
    ],
)
def test_a_missing_row_raises(preset, name):
    with pytest.raises(TypeError, match=f"is missing {name}"):
        preset()


def test_a_missing_diameter_or_situation_raises():
    with pytest.raises(TypeError, match="is missing situation"):
        gs.presets.grey_iron_tensile_strain_limit(diameter="over_300_mm")
    with pytest.raises(TypeError, match="is missing diameter"):
        gs.presets.grey_iron_tensile_strain_limit(situation="general")


def test_an_unknown_row_lists_the_rows():
    with pytest.raises(ValueError, match="'rubber_gasket'") as error:
        gs.presets.cast_iron_joint_limits(joint="lead_yarn")
    assert "'lead_yarn_water_main'" in str(error.value)
    with pytest.raises(ValueError, match="'ductile_iron'"):
        gs.presets.iron_strain_limits(material="cast_iron")
    with pytest.raises(ValueError, match="'over_300_mm'"):
        gs.presets.grey_iron_tensile_strain_limit(diameter="300", situation="general")
    with pytest.raises(ValueError, match="'particularly_adverse'"):
        gs.presets.grey_iron_tensile_strain_limit(
            diameter="over_300_mm", situation="adverse"
        )


def test_record_takes_a_preset_as_a_sourced():
    limit = gs.presets.iron_strain_limits(material="grey_iron").tensile
    magnitude, entry = record(
        "tensile_strain_limit",
        limit,
        kind="design judgment",
        unit="dimensionless",
        plain_number="refuse",
    )
    assert magnitude == pytest.approx(100e-6)
    assert entry.source == limit.source


def test_preset_caveats_are_each_listed_once_in_order():
    joints = gs.presets.cast_iron_joint_limits(joint="rubber_gasket")
    strains = gs.presets.iron_strain_limits(material="grey_iron")
    caveats = preset_caveats(
        joints.rotation, joints.pullout, strains.tensile, strains.compressive, 1.0
    )
    assert caveats == (
        *joints.pullout.caveats,
        *strains.tensile.caveats,
    )
    assert preset_caveats(1.0, gs.Sourced(2.0, source="x"), None) == ()


# M4 (a): building presets (spec decision 4)


@pytest.mark.parametrize(
    ("structure", "ratio", "where"),
    [
        ("masonry", 2.6, "p. 716, 'often taken as 2.6' for masonry"),
        ("framed", 12.5, "§4.5, p. 717, reinforced concrete framed buildings"),
    ],
)
def test_youngs_to_shear_modulus_ratio(structure, ratio, where):
    value = gs.presets.youngs_to_shear_modulus_ratio(structure=structure)
    assert isinstance(value, gs.presets.Preset)
    assert value.value.to("dimensionless").magnitude == ratio
    assert value.source.startswith(
        f"gs.presets.youngs_to_shear_modulus_ratio(structure={structure!r}): "
        f"Mair, Taylor & Burland (1996), {where}"
    )
    assert "Burland & Wroth (1974)" in value.caveats[0]
    assert "hasn't been read" in value.caveats[0]
    framed = structure == "framed"
    assert any("Poisson's ratio as 0.3" in c for c in value.caveats) is framed


def test_damage_categories_preset():
    value = gs.presets.damage_categories()
    assert isinstance(value.value, gs.buildings.DamageCategories)
    assert value.source == (
        "gs.presets.damage_categories(): Mair, Taylor & Burland (1996), Table 2, "
        "p. 715, after Boscardin & Cording (1989)"
    )
    (caveat,) = value.caveats
    assert "Boscardin & Cording (1989), which hasn't been read" in caveat
    assert "'Moderate to Severe'" in caveat


def test_preliminary_assessment_limits():
    limits = gs.presets.preliminary_assessment_limits()
    assert limits.settlement.value == 10 * u.mm
    assert limits.slope.value.to("dimensionless").magnitude == pytest.approx(1 / 500)
    for value in (limits.settlement, limits.slope):
        assert value.source == (
            "gs.presets.preliminary_assessment_limits(): Mair, Taylor & Burland "
            "(1996), §5.2, p. 717"
        )
        (caveat,) = value.caveats
        assert "Rankin (1988), which hasn't been read" in caveat
        assert "foundation level" in caveat
    _, entry = record(
        "slope_limit",
        limits.slope,
        kind="design judgment",
        unit="dimensionless",
        plain_number="refuse",
    )
    assert entry.value.magnitude == pytest.approx(0.002)


def test_building_preset_missing_or_unknown_row():
    with pytest.raises(TypeError, match="is missing structure"):
        gs.presets.youngs_to_shear_modulus_ratio()
    with pytest.raises(ValueError, match="'masonry', 'framed'"):
        gs.presets.youngs_to_shear_modulus_ratio(structure="steel")
