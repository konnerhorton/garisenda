# Plot

Every figure takes a result and returns an ordinary matplotlib figure with its axes. A figure with several panels returns `(fig, axs)`, as `plt.subplots` does, and takes `axs=` to draw into panels you already have. Figures draw the result's values and never recalculate them.

::: garisenda.plot.profile

::: garisenda.plot.cross_section
