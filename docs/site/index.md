# garisenda

Ground movements from tunneling and their effect on utilities and structures: greenfield closed-form and empirical methods, made traceable. Every result records its inputs, its method, its source and the limits it was checked against, comes with a figure, and says when it falls outside a method's range, which is where a numerical model is needed.

```python
--8<-- "home.py"
```

```text
--8<-- "home.txt"
```

![The cross-section at the water main's station: settlement and horizontal movement at the surface, and the tunnel and water main to scale](img/generated/home.png)

The water main is 1.5 m deep, and the trough is a surface method, so every station is flagged *outside*: the values are the surface's, and the figure says so. Nothing outside a method's range is hidden or dropped.

!!! warning "In development"
    garisenda is pre-alpha. The transverse trough's sources aren't verified yet, so its results are for trying the library, not for design.

The name is the Garisenda, the leaning tower in Bologna whose lean comes from settlement of its foundations.
