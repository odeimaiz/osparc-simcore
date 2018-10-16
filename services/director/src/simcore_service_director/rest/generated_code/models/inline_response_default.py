# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from .base_model_ import Model
from .inline_response_default_data import InlineResponseDefaultData  # noqa: F401,E501
from .. import util


class InlineResponseDefault(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, data: InlineResponseDefaultData=None, status: int=None):  # noqa: E501
        """InlineResponseDefault - a model defined in OpenAPI

        :param data: The data of this InlineResponseDefault.  # noqa: E501
        :type data: InlineResponseDefaultData
        :param status: The status of this InlineResponseDefault.  # noqa: E501
        :type status: int
        """
        self.openapi_types = {
            'data': InlineResponseDefaultData,
            'status': int
        }

        self.attribute_map = {
            'data': 'data',
            'status': 'status'
        }

        self._data = data
        self._status = status

    @classmethod
    def from_dict(cls, dikt) -> 'InlineResponseDefault':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The inline_response_default of this InlineResponseDefault.  # noqa: E501
        :rtype: InlineResponseDefault
        """
        return util.deserialize_model(dikt, cls)

    @property
    def data(self) -> InlineResponseDefaultData:
        """Gets the data of this InlineResponseDefault.


        :return: The data of this InlineResponseDefault.
        :rtype: InlineResponseDefaultData
        """
        return self._data

    @data.setter
    def data(self, data: InlineResponseDefaultData):
        """Sets the data of this InlineResponseDefault.


        :param data: The data of this InlineResponseDefault.
        :type data: InlineResponseDefaultData
        """

        self._data = data

    @property
    def status(self) -> int:
        """Gets the status of this InlineResponseDefault.


        :return: The status of this InlineResponseDefault.
        :rtype: int
        """
        return self._status

    @status.setter
    def status(self, status: int):
        """Sets the status of this InlineResponseDefault.


        :param status: The status of this InlineResponseDefault.
        :type status: int
        """

        self._status = status
