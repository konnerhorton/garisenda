# Sources

The bibliography (SPEC §2.2): one entry per source garisenda cites, with its short key, what is cited from it, and the date it was verified against the source itself. 🔬 marks what hasn't been read.

## `bracegirdle1996`
Bracegirdle, A., Mair, R. J., Nyren, R. J. & Taylor, R. N. (1996). A methodology for evaluating potential damage to cast iron pipes induced by tunnelling. In *Geotechnical Aspects of Underground Construction in Soft Ground*, eds R. J. Mair & R. N. Taylor, pp. 659–664. Balkema, Rotterdam.
- Cited for: Eq. 1, settlement with the volume and width at the pipe's depth, and Eq. 2, the width at depth in clay, with the limit "only ... above the level of the crown of the tunnel" (p. 660).
- Eq. 3 (horizontal movement) has a smudge in its denominator; read as y/(z₀ − z_p), not cited (`docs/work/m2b-subsurface.md`).
- Cited for (M3 (a)): the approach, ground strains "obtained directly by differentiating the displacements" (p. 660) and pipes that follow the ground (p. 663); Eqs. 7–9, curvature at the trough's center and peak hogging curvature and horizontal strain at √3 i (p. 662); combined tensile strain as bending plus axial strain (pp. 662–663).
- Cited for (M3 (b)): Table 2, allowable joint rotation and pull-out, after Attewell et al. (1986), and the text on individual joints and the conservative pull-out (p. 661); Table 4, allowable increase in strain, and Herbert & Leach (1990)'s grey iron tensile values as quoted (p. 662); joints taken as rigid for bending strain (p. 663).
- Eqs. 5–6 (p. 661), conservative joint rotation for one trough, are read but not used: Eq. 5's derivation can't be checked without Attewell et al. (1986), and it exceeds the joint geometry only for some pipe lengths (TODO #4).
- Verified 2026-11-04 (M2 (b)); Eqs. 7–9 and pp. 660, 662–663 verified 2026-11-06 (M3 (a)), Eqs. 7–9 against the page image; Tables 2 and 4, Eqs. 5–6 and pp. 661–663 verified 2026-11-06 (M3 (b)) against the page images.

## `attewell1986`
Attewell, P. B., Yeates, J. & Selby, A. R. (1986). *Soil Movements Induced by Tunnelling and their Effects on Pipelines and Structures*. Blackie and Son Ltd., London. As listed in Bracegirdle et al. (1996)'s references (read from the text layer, 2026-11-06).
- 🔬 Not read: cited only as quoted in Bracegirdle et al. (1996), Table 2 (SPEC §2.1), and named so in `gs.presets.cast_iron_joint_limits`. TODO #4.

## `herbert_leach1990`
Herbert, R. & Leach, G. (1990). Damage control procedures for distribution mains. *Gas '90*, Institution of Gas Engineers, Communication 1437. As listed in Bracegirdle et al. (1996)'s references (read from the text layer, 2026-11-06).
- 🔬 Not read: cited only as quoted in Bracegirdle et al. (1996), p. 662 (SPEC §2.1), and named so in `gs.presets.grey_iron_tensile_strain_limit`.

## `mair1993`
Mair, R. J., Taylor, R. N. & Bracegirdle, A. (1993). Subsurface settlement profiles above tunnels in clays. *Géotechnique* 43(2), 315–320.
- 🔬 Not read: the reference as given in Taylor (1995) and Mair & Taylor (1997). Its method is cited from them (SPEC §2.1). TODO #3.

## `mair_taylor1997`
Mair, R. J. & Taylor, R. N. (1997). Theme lecture: Bored tunnelling in the urban environment. *Proc. 14th Int. Conf. on Soil Mechanics and Foundation Engineering*, Hamburg, pp. 2353–2385. Balkema.
- Cited for: Eq. 7, i = K (z₀ − z), p. 2361; Eq. 8, K = (0.175 + 0.325 (1 − z/z₀))/(1 − z/z₀), after Mair et al. (1993), p. 2362; vectors toward a point 0.175 z₀/0.325 below the axis, giving 65 % of the horizontal movement toward the axis, p. 2362; horizontal movement in sands, p. 2362.
- 🔬 The proceedings' volume number isn't on the pages read.
- Verified 2026-11-04 (M2 (b)).

## `mair1996`
Mair, R. J., Taylor, R. N. & Burland, J. B. (1996). Prediction of ground movements and assessment of risk of building damage due to bored tunnelling. In *Geotechnical Aspects of Underground Construction in Soft Ground*, eds R. J. Mair & R. N. Taylor, pp. 713–718. Balkema, Rotterdam.
- Cited for (M4 (a)): Table 1, damage categories, and Table 2, limiting tensile strain per category, after Boscardin & Cording (1989) (p. 715); Eqs. 7–9, the deep beam's bending and diagonal strains and the combined bending strain, after Burland & Wroth (1974), with the section's t and I, H from foundation to eaves, the zones split at the inflection points and E/G = 2.6 for masonry (§§4.1–4.3, p. 716); Eq. 10, the combined diagonal strain with Poisson's ratio 0.3, E/G = 12.5 for framed buildings (§4.5), and the preliminary assessment's 10 mm and 1/500 (§§5.1–5.3, p. 717).
- Burland & Wroth (1974), Burland et al. (1977) and Boscardin & Cording (1989) are cited "after" it, 🔬 (TODO #7). The beam with any shear coefficient and Eq. 10's general form are garisenda's own derivation (`docs/work/m4a-building-damage.md`, Mechanics).
- The text layer is OCR; read the page images. Verified 2026-11-10 (M4 (a)) against the page images.

## `jones2022`
Jones, B. (2022). *Soft Ground Tunnel Design*. First edition. CRC Press, Boca Raton.
- A check, not cited for an equation (SPEC §2.1): Eqs. 13.12 and 13.23 (pp. 476, 479), the corrected beam after Netzel (2009), check the Timoshenko form; Examples 13.1–13.2 (pp. 470–490) are case J's golden values. Its Example 13.2 calls the sagging zone category 1 where its own Table 13.1 gives 0.
- Cited as the report of Harris & Franzius (2006)'s z_f/z₀ < 0.2 (§13.2.1, p. 490) and of Rankin (1988) for Stage 1 (p. 469), both 🔬 (TODO #7).
- Book pages are PDF pages less 23. Verified 2026-11-10 (M4 (a)) against the page images for Eqs. 13.12 and 13.23 and Tables 13.2–13.3.

## `taylor1995`
Taylor, R. N. (1995). Tunnelling in soft ground in the UK. In *Underground Construction in Soft Ground*, eds K. Fujita & O. Kusakabe, pp. 123–126. Balkema, Rotterdam.
- Cited for: Eq. 5, K = 0.325 + 0.175/(1 − z/z₀), after Mair et al. (1993), and the constant-volume direction of movement, toward a point 0.175 z₀/0.325 below the axis, p. 125. Eqs. 1–4 and 6 (p. 124–125) restate the surface trough (TODO #2).
- Verified 2026-11-04 (M2 (b)).
