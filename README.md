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

  Passing username and password is supported through multiple ways as entering
  your password visibly into your shell history is discouraged for security
  reasons.

  - using environment variables `UULM_USERNAME`, `UULM_PASSWORD`
  - using a `.env` file in the current working directory with the same variables
  - interactive mode, if none of the above was specified

Options:
  -u, --username TEXT
  -p, --password TEXT
  --headful            Show the browser window
  -d, --debug          Set the log level to DEBUG
  --help               Show this message and exit.

Commands:
  campusonline  Interact with the module tree in Campusonline.
  coronang      Automatically register for courses on CoronaNG by...
  grades        Calculate your weighted grade using the best n credits.
  sport         Automatically register for courses on the AktivKonzepte...
```
