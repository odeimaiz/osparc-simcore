import re
import sys
from pathlib import Path

from setuptools import find_packages, setup

here = Path(sys.argv[0] if __name__ == "__main__" else __file__).resolve().parent


def read_reqs(reqs_path: Path):
    return re.findall(
        r"(^[^#\n-][\w\[,\]]+[-~>=<.\w]*)", reqs_path.read_text(), re.MULTILINE
    )


install_requirements = read_reqs(
    here / "requirements" / "_base.in"
)  # WEAK requirements

test_requirements = read_reqs(
    here / "requirements" / "_test.txt"
)  # STRONG requirements

readme = Path(here / "README.md").read_text()

setup(
    name="simcore-models-library",
    version="0.1.0",
    author="Sylvain Anderegg (sanderegg)",
    description="Core service library for simcore pydantic models",
    python_requires="~=3.8",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.8",
    ],
    long_description=readme,
    license="MIT license",
    install_requires=install_requirements,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    test_suite="tests",
    tests_require=test_requirements,
    extras_require={"test": test_requirements},
    zip_safe=False,
)
