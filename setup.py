# setup.py

from setuptools import setup
from Cython.Build import cythonize

setup(
    name="my_cython_core",
    # We tell Cython to compile everything under core/*.pyx
    # package_dir= ["core"],
    ext_modules=cythonize(
        [
            "gym_trading_env2/core/asset.pyx",
            "gym_trading_env2/core/pair.pyx",
            "gym_trading_env2/core/value.pyx",
            "gym_trading_env2/core/quotation.pyx",
            "gym_trading_env2/core/portfolio.pyx",
        ],
        language_level=3
    ),
    zip_safe=False,
)
