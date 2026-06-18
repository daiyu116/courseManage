# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2024-2026 courseManage Contributors
from setuptools import setup, Extension
from Cython.Build import cythonize
import os

CRITICAL_MODULES = [
    "utils/license.py",
    "routers/license.py",
    "optimizer.py",
    "utils/smart_command.py",
    "utils/wechat_notifier.py",
    "utils/remainder.py",
]

extensions = [
    Extension(
        module.replace("/", ".").replace(".py", ""),
        [module],
    )
    for module in CRITICAL_MODULES
]

setup(
    name="courseManage-protected",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        },
        force=True,
    ),
)