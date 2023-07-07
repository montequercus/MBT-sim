# Introduction
The goal of these examples is to show how model-based testing (MBT) can be applied to a simulation model. This document describes the required software to run the examples, how to install them, and what potential problems there are.

The open-source testing framework [AltWalker](https://altom.gitlab.io/altwalker/altwalker/) is used for model-based testing. It can run tests that are written in Python using the [unittest](https://docs.python.org/3/library/unittest.html) package. AltWalker uses GraphWalker to generate test paths. [GraphWalker](http://graphwalker.github.io/) is an open-source software package written in Java.

Two Python packages are used for making and executing simulation models. The open-source package [salabim](https://www.salabim.org/) is used to make discrete event simulation models. The open-source package [mesa](https://github.com/projectmesa/mesa) is used to make agent-based simulation models.

# Requirements
The following versions of the mentioned Python packages are used:
- altwalker 0.3.2
- salabim 23.1.4
- mesa 0.8.8.1
- numpy 1.21.5

The `unittest` and `warnings` packages will be installed when `altwalker` is installed.

The following version of other software is used:
- Python 3.7.13
- Java 11
- GraphWalker 4.3.2

# Installation
## GraphWalker
The GraphWalker CLI can downloaded from its [repository](https://graphwalker.github.io/). With the given instructions, it is then installed using Java. However, this gave the error `Missing a command` on my system.

An alternative is to use the installation instruction from [AltWalker's site](https://altwalker.github.io/altwalker/installation.html#graphwalker). The GraphWalker repository is cloned using git, and installed using a Python script:

```
> git clone https://github.com/altwalker/graphwalker-installer.git
> cd graphwalker-installer
> python install-graphwalker.py
```

This Python script has to be edited to installed the correct version of Graphwalker. The edited version is included in this repository. Alternatively, the edits to the file can be made manually: In line 170 of 'install-graphwalker.py', `version = "latest"` can be replaced by `version = "4.3.2"`, to ensure that no snapshot version is installed. Line 148 can be commented out or deleted for Windows machines, to ensure that the `PATH` environment variable is not overwritten. 

Before running the Python script (again), ensure that the installation folder does not exist yet. On Windows, it is placed in the Home folder. Its path would be 'C:/Users/<user>/graphwalker'. 

After installation, the file 'gw.bat' must be added to the `PATH` variable, in order for AltWalker to function. This can be done manually. This file will be located in the aforementioned 'graphwalker' folder.

### GraphWalker Studio
GraphWalker Studio can be optionally installed to visualize the abstract models (.json files) that AltWalker uses. The Java .jar file can be downloaded from the [GraphWalker site](https://graphwalker.github.io/).

Studio can be used by running the command
```
java -jar graphwalker-studio-4.3.2.jar
```
And then by opening the URL `http://localhost:9090/studio.html`

## AltWalker
AltWalker can be installed using the [AltWalker installation instructions](<`version = "4.3.2"`>). Three prerequisites are listed:
- Python3, with pip3
- Java 11
- GraphWalker CLI

Installation is done through pip:
```
pip install altwalker
```

## Salabim and mesa
Salabim and mesa can be installed through pip as well.
```
pip install salabim
pip install mesa
```


# Running tests with AltWalker
Tests can be run from within Python by using the AltWalker API and `Walker` functionality. This can be done as a separate "test execution script".

Alternatively, tests are run from the CLI. This is done in the *M/M/1 example*

## File structure
It is important to note the required file structure of a test project. Taken from  [AltWalker's documentation](https://altom.gitlab.io/altwalker/altwalker/cli.html):
```
test-project/
├── .git/
├── models/
│   └── default.json
└── tests/
    ├── __init__.py
    └── test.py
```

Thus, there must be a file `__init__.py` in the 'tests' folder. This can be an empty file. The 'test script' file in the 'tests' folder must be called `test.py`. 

To avoid confusion, we can list 4 types of files that typically need to be made, to have a functioning AltWalker test:

| Type of file                             | Name or extension| Language                  |
| -------------------------------- | ---------------- | ------------------------- |
| Abstract model, or graph         | .json            | JSON                      |
| Test script                      | test.py          | Python, using `unittest`  |
| Test execution script (optional) | .py              | Python, using `altwalker` |
| System under test                | (variable)       | (variable)                          |

In short, the abstract model gives a finite state machine (FSM), with vertices connected by edges. In model-based testing (MBT), this is used as a simplified representation of the system under test (SUT). The SUT in this case is some simulation model.
AltWalker/GraphWalker can generate (randomized) test paths through this abstract model. Each vertex and edge on this path, when encountered, will execute a (unit) test on the SUT. 

The (unit) tests associated with each vertex and edge of an abstract model, are given in the test script. This file must be called 'test.py'. 
Note that when multiple abstract models (.json files) are used, there is still only one test script. A `unittest.TestCase` class is then defined for each abstract model. The name of this class in the test script must be the same as its `"name"` given in the abstract model JSON file.
Note also that it makes no sense to run the test script on its own. It will only work when executed by AltWalker, with an abstract model specified.

Lastly, the test execution script is a made-up name for a separate Python script, from which a model-based test can be run. This is where the `altwalker` package is used.
Alternatively, model-based tests can be run from the CLI. This is done in this example.

## Run from CLI
The instructions for running tests from the CLI are found in [AltWalker's documentation](https://altom.gitlab.io/altwalker/altwalker/cli.html). 
The commands that are used in the examples are: `check`, `verify`, and `online`.

AltWalker can be added to the `PATH` environment variable, or the commands can be run while using a Python environment with `altwalker`



