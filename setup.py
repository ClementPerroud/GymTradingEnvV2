# setup.py

from setuptools import setup
from Cython.Build import cythonize

setup(
    name="my_cython_core",
    # We tell Cython to compile everything under core/*.pyx
    # package_dir= ["core"],
    ext_modules=cythonize(
        [
            "core/asset.pyx",
            "core/pair.pyx",
            "core/value.pyx",
            "core/quotation.pyx",
            "core/portfolio.pyx",
        ],
        language_level=3
    ),
    zip_safe=False,
)
