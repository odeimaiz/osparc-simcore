# coding: utf-8

"""
    simcore-service-webserver API

    simcore-service-webserver rest API definition  # noqa: E501

    OpenAPI spec version: 1.0.0-oas3
    Contact: support@simcore.io
    Generated by: https://openapi-generator.tech
"""


from setuptools import setup, find_packages  # noqa: H301

NAME = "simcore-webserver-sdk"
VERSION = "1.0.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["urllib3 >= 1.15", "six >= 1.10", "certifi", "python-dateutil"]
REQUIRES.append("aiohttp")

setup(
    name=NAME,
    version=VERSION,
    description="simcore-service-webserver API",
    author_email="support@simcore.io",
    url="https://github.com/ITISFoundation/osparc-simcore/tree/master/packages/webserver-sdk/python",
    keywords=["OpenAPI", "OpenAPI-Generator", "simcore-service-webserver API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    include_package_data=True,
    long_description="""\
    simcore-service-webserver rest API definition  # noqa: E501
    """
)
