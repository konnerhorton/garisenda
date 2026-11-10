"""Figures drawn from results.

Every figure takes a result and returns ``(fig, ax)`` for one axes or
``(fig, axs)`` for several panels, as `matplotlib.pyplot.subplots` does. It
draws from the result's values and never recalculates them.
"""

from garisenda.plot._cross_section import cross_section
from garisenda.plot._profile import profile

__all__ = ["cross_section", "profile"]
