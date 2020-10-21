import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="D-FAST Morphological Impact",
    version="0.1.0",
    author="Bert Jagers",
    author_email="bert.jagers@deltares.nl",
    description="Rapid Assessment Tool for Morphological Impact of River Training Measures",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Deltares/D-FAST_Morphological_Impact",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)",
        "Development Status :: 3 - Alpha",
        "Environment :: X11 Applications :: Qt",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)