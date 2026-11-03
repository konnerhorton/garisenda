# Install

garisenda needs Python 3.12 or later and runs on Windows, macOS and Linux.

=== "Latest (recommended)"

    The latest version from GitHub. It has every feature on this site.

    ```bash
    pip install git+https://github.com/konnerhorton/garisenda
    ```

    Or, in a [uv](https://docs.astral.sh/uv/) project:

    ```bash
    uv add git+https://github.com/konnerhorton/garisenda
    ```

=== "Released"

    The last release on PyPI. It can be behind this site, which follows the latest version.

    ```bash
    pip install garisenda
    ```

    Or, in a uv project:

    ```bash
    uv add garisenda
    ```

To check which version you have:

```python
import garisenda as gs

print(gs.__version__)
```
