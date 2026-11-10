# Sweeps

`gs.sweep` runs one calculation over values of one to three inputs, and returns a table with one row per run: the inputs, the governing values and the verdict.

```python
--8<-- "sweep.py"
```

```text
--8<-- "sweep.txt"
```

## The function you write

`gs.sweep` takes a function that builds the whole calculation from the inputs being varied and returns its result. The inputs worth varying sit at different steps (volume loss on the trough, depth on the utility), and one change can reach more than one step, so a function with four lines of Python says it plainly.

**Name the function's arguments as the inputs they set**: `volume_loss`, not `vl`. After each run, `gs.sweep` checks that every varied value is among the result's recorded inputs, and raises if one isn't. A function that ignored an argument, or passed it to the wrong place, would otherwise give a table that varies nothing.

Likewise, **every input that isn't varied must stay the same** between runs, or `gs.sweep` raises: the table's fixed inputs would be wrong. Where two inputs share a name (the tunnel's `diameter` and the utility's), vary one through its own builder only.

## Grid or paired

With one input, there's one run per value. With two or three, `mode` is required, because the runs differ:

- `mode="grid"` runs every combination, the first input varying slowest: 3 × 3 = 9 runs above.
- `mode="paired"` runs the values element by element, so the sequences must be the same length.

The values can be a list, a numpy array or a pint array, and each element is passed to the function as it is.

## The table

- `run`, then each varied input **as used**: its magnitude in SI from the run's input record, so 1 % appears as 0.01.
- For each governing value, its value and `<name>_distance`, where along the utility it occurs.
- `validity`, the result's verdict, and `warnings`, how many flags it has. Above, the runs at depth 2 m are *outside*, because the trough is a surface method. For a buried utility, use `gs.sources.transverse_trough`, the trough at depth ([Below the surface](below-the-surface.md)).
- `error`: a run that raises is recorded in its row, with its values missing, and the sweep goes on. Above, the runs at depth 20 m put the sewer through the tunnel. If every run raises, the sweep raises the first error, since that is a mistake in the function.

`table.attrs` holds each column's unit (`units`), the function's name (`run`), the `mode`, the varied names (`vary`) and every input that wasn't varied (`fixed_inputs`), with its value, unit and source.

A sweep row is exactly the direct call: `crossing(volume_loss=1 * u.percent, depth=0 * u.m).governing()` gives the same values. See [`gs.sweep`](../reference/garisenda.md#garisenda.sweep).
