# D-FAST Morphological Impact [![GitHub license](https://img.shields.io/github/license/Deltares/D-FAST_Morphological_Impact)](https://github.com/Deltares/D-FAST_Morphological_Impact/blob/master/LICENSE.md)

This is one of the [Deltares](https://www.deltares.nl) Fluvial Assessment Tools.
The purpose of this tool is to provide a first estimate the morphological impact of engineering measures in rivers without doing a morphological simulation.
The user should carry out six steady state hydrodynamic simulations using [D-Flow FM](https://www.deltares.nl/en/software/module/d-flow-flexible-mesh/).
The results of these simulations will be combined with some basic morphological characteristics to arrive at the estimated impact.
For more details see the documentation section.

## Documentation

The documentation consists of
* a LaTeX user manual including scientific description, and developer starter guide (also in this readme)
* a [Technical Reference Manual](docs/techref.md) in Markdown
the sources of both documents can be found in the `docs` folder.

## Developer user starter guide
1. install python 3
2. Make sure pip is installed 
3. Install poetry with the following command: 
	`pip install poetry`
4. Use the following command to install the virtual environment with the correct dependencies: (problems with PyQt5 can occur here)
	`poetry install`
5. After this command has run correctly, you should have a folder called **"venv."**, this is your virtual environment. To activate this environment, run the following command: (problems with admin rights can occur here)
	`Poetry shell` 
6. You should get something similar as this:
	`(d-fast-morphological-impact-py3.11) PS C:\checkouts\D-Fast\MI\D-FAST_Morphological_Impact>`
7. Use the following command to run the GUI:
	`poetry run python -m dfastmi`
8. Use the following command to run the tests:
	`poetry run pytest tests/`

## License

This software is distributed under the terms of the GNU Lesser General Public License Version 2.1.
See the [license file](LICENSE.md) for details.
