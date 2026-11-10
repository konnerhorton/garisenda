# Presets

Named, cited presets of published limits and parameters. A preset is never applied unless you pass it: call one with its row, and pass its values as the check's limits. Each value is a `Preset`, a `Sourced` whose source names the call, the paper and its table, and whom the paper quotes; its caveats join the result's assumptions.

```python
import garisenda as gs

joints = gs.presets.cast_iron_joint_limits(joint="lead_yarn_water_main")
strains = gs.presets.iron_strain_limits(material="grey_iron")
ratio = gs.presets.youngs_to_shear_modulus_ratio(structure="masonry")
```

There is no pipe length preset yet: no citable source for nominal laying lengths has been found.

::: garisenda.presets.cast_iron_joint_limits

::: garisenda.presets.iron_strain_limits

::: garisenda.presets.grey_iron_tensile_strain_limit

::: garisenda.presets.youngs_to_shear_modulus_ratio

::: garisenda.presets.damage_categories

::: garisenda.presets.preliminary_assessment_limits

::: garisenda.presets.Preset

::: garisenda.presets.JointLimits

::: garisenda.presets.StrainLimits

::: garisenda.presets.PreliminaryLimits
