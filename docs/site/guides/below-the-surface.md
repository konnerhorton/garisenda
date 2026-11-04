# Below the surface

A buried utility moves with the ground at its own depth, where the trough is narrower and deeper than at the surface. `gs.sources.transverse_trough` gives the transverse trough at any depth above the tunnel's crown. How its width changes with depth is a method you name: there's no default.

```python
--8<-- "below-the-surface.py"
```

```text
--8<-- "below-the-surface.txt"
```

![The cross-section at the gas main's station, 8 m deep](../img/generated/below-the-surface-cross-section.png)

![The profile along the gas main](../img/generated/below-the-surface-profile.png)

## The width at depth

The trough at depth z is Gaussian, as at the surface, with the same volume V_L A per unit length of tunnel at every depth, so a narrower trough is deeper. Its width is i(z) = c₀ z₀ + c₁ (z₀ − z), by one of two methods:

- **`gs.sources.mair_trough_width()`**, Mair et al. (1993)'s fit for tunnels in clay, i(z) = 0.175 z₀ + 0.325 (z₀ − z), as Mair & Taylor (1997) give it. It takes no arguments: its coefficients are the method, and can't be swept or overridden. At the surface it gives i = 0.5 z₀.
- **`gs.sources.linear_trough_width(trough_width_parameter=k)`**, i = k (z₀ − z) with your k. No source gives this width at depth: it's your choice, and the result records it as such. At the surface it is the surface trough's i = k z₀, and its movements there are `transverse_surface_trough`'s exactly. It is what's offered for granular ground until a method for it is added.

The result records the method by name in `trough_width` (`"Mair et al. (1993), clay"` or `"linear"`), and the linear method's k as `trough_width_parameter`.

## Horizontal movement

The ground's horizontal movement is set by keeping its volume constant, as for undrained clay: the only field that does, with the trough above, is u = −c₁ (o/i) S, toward the axis.

- With the **linear method** the vectors point at the tunnel axis, as for the surface trough.
- With **Mair's method** they point at a point 0.175 z₀/0.325 below the axis (Taylor 1995), which gives 65 % of the horizontal movement at the surface that vectors toward the axis would (Mair & Taylor 1997). So at the surface, Mair's method has the surface trough's settlement with k = 0.5 but 0.65 of its horizontal movement.

In sands, vectors toward the axis may underestimate horizontal movement near the edge of the trough (Mair & Taylor 1997); the linear method's assumptions say so.

## Below the crown

The method applies only above the tunnel's crown, at depth z₀ − D/2 (Bracegirdle et al. 1996). A point deeper than that, beside the bore or below it, is flagged *outside*, not raised, and given the trough at the crown's depth, with its derivatives with respect to depth zero. The sewer above, beside the bore at 18.5 m, is flagged at every station. Movements there need another method or a numerical analysis. For the linear method, which has no source for a limit, the same limit is garisenda's choice, and the flag says so.

A point inside the bore raises, as does a point above the ground surface.

![The cross-section at the sewer, beside the bore below its crown](../img/generated/below-the-surface-crown.png)

Mair et al. (1993)'s data reach about 0.9 z₀ deep, so close to the crown of a tunnel with z₀ under about 5 D the fit is extrapolated. That isn't flagged, since no source states it as a limit.

## The figures

The cross-section draws the trough at the utility's depth, and its panels say which ("Settlement at depth 8 m"). The ±i marks are at i at that depth. Where the section passes through a bore, the trough's line breaks. The profile figure is unchanged: it draws the result's values.

## Sweeping k

`trough_width_parameter` is swept as for the surface trough, by the same name, so a sweep written for one works with the other. The method itself can't be swept: switching it between runs raises, as for any input that isn't varied. To compare Mair's method with the linear one, run each. See [Sweeps](sweep.md) and [`gs.sources.transverse_trough`](../reference/sources.md#garisenda.sources.transverse_trough).
