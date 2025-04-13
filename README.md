# uulm-utils
Collection of helpers for Ulm University students.
## Installation
Requires:
- [python](https://www.python.org/)
- [playwright](https://playwright.dev/python/)

Assuming you have a recent version of python installed, run

```
pip install git+https://github.com/eneller/uulm-utils
```
Or, even better, use [uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io/stable/installation/) to install.
This will provide the `uulm` command.

## Usage
```
Usage: uulm [OPTIONS] COMMAND [ARGS]...

Options:
  -u, --username TEXT
  -p, --password TEXT
  --headful            Show the browser window
  --help               Show this message and exit.

Commands:
  campusonline  Interact with the module tree in Campusonline
  coronang      Automatically register for courses on CoronaNG
```
