from setuptools import setup, find_packages

setup(
    name="perftest-result-confluence-writer",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'src': ['templates/*.html'],
    },
    install_requires=[
        "pandas",
        "requests",
        "jinja2",
        "tabulate",
    ],
    python_requires=">=3.9",
) 