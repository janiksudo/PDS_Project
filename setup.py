import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='PDS_Project',
    version='0.0.1dev1',
    description="Semester Project - Programming Data Science",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="",
    author_email="student@uni-koeln.de",
    url="https://github.com/janiksudo/PDS_Project",
    packages=setuptools.find_packages(),
    install_requires=['pandas', 'scikit-learn', 'click'],
    entry_points={
        'console_scripts': ['nextbike=nextbike.cli:main']
    }
)
