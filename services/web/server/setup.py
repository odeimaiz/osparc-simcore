import re
import sys
from pathlib import Path

from setuptools import find_packages, setup

current_dir = Path(sys.argv[0] if __name__ == "__main__" else __file__).resolve().parent


def read_reqs(reqs_path: Path):
    return re.findall(
        r"(^[^#\n-][\w\[,\]]+[-~>=<.\w]*)", reqs_path.read_text(), re.MULTILINE
    )


# -----------------------------------------------------------------
# Hard requirements on third-parties and latest for in-repo packages
install_requirements = read_reqs(current_dir / "requirements" / "_base.txt") + [
    "simcore-models-library",
    "simcore-postgres-database",
    "simcore-sdk",
    "simcore-service-library",
]
test_requirements = read_reqs(current_dir / "requirements" / "_test.txt")

setup(
    name="simcore-service-webserver",
    version="0.6.0",
    packages=find_packages(where="src"),
    package_dir={
        "": "src",
    },
    include_package_data=True,
    package_data={
        "": [
            "api/v0/openapi.yaml",
            "api/v0/schemas/*.json",
            "config/*.y*ml",
            "data/*.json",
            "templates/**/*.html",
        ]
    },
    entry_points={
        "console_scripts": [
            "simcore-service-webserver=simcore_service_webserver.__main__:main",
        ]
    },
    python_requires="~=3.8",
    install_requires=install_requirements,
    tests_require=test_requirements,
    setup_requires=["pytest-runner"],
)
