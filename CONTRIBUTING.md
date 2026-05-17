# Getting started

This project uses [Poetry](https://python-poetry.org/) for dependency management. To start developing here, you need to install Poetry

* Follow the instructions on the [official docs](https://python-poetry.org/docs/master/#installing-with-the-official-installer)

Once you have Poetry installed on your system simply run:

```bash
poetry install --with test
```

This will create a virtual environment and install the required dependencies.

For more information on how to use Poetry, read the [official docs](https://python-poetry.org/docs/master/).

## Setting up your local environment

Simply run the following make command to create a virtual environment and start developing:

```bash
make init
```

This will clean up your current virtual env, install poetry, create a new virtual environment and install all dependencies for you.

You can use the following step to activate your newly created virtual environment.

```bash
source .venv/bin/activate
```

To add/remove dependencies just use Poetry cli! Like this:

```bash
poetry add requests
```

## Useful commands

* `make help`       To get a list of ready to use recipes
* `make test`       Run the unit test suite
* `make package-check` Build the wheel, validate `Requires-Dist` metadata, install it in a fresh virtual environment, and smoke import `brave`, `Brave`, and `AsyncBrave`
* `poetry list`     Lists all available Poetry commands
