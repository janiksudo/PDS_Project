import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='PDS_Project',
    version='1.0.0',
    description="Semester Project - Programming Data Science",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Diana Gowalow, Max Kaiser, Tim Ockenga, Tom Celig, Janik Muires",
    author_email="dgowalow@smail.uni-koeln.de, mkaiser2@smail.uni-koeln.de, tockenga@smail.uni-koeln.de, tcelig@smail.uni-koeln.de, jmuires@smail.uni-koeln.de",
    url="https://github.com/janiksudo/PDS_Project",
    packages=setuptools.find_packages(),
    install_requires=['pandas', 'scikit-learn', 'click', 'tqdm'],
    entry_points={
        'console_scripts': ['nextbike=nextbike.cli:cli']
    }
)
