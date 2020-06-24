# coding: utf-8

"""
    Data Modelling Storage Service API

    Data storage service for DMT  # noqa: E501

    The version of the OpenAPI document: 0.1.0
    Generated by: https://openapi-generator.tech
"""


import pprint
import re  # noqa: F401

import six

from dmss_api.configuration import Configuration


class InlineObject1(object):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    openapi_types = {
        'directory': 'str',
        'document': 'str',
        'files': 'list[file]'
    }

    attribute_map = {
        'directory': 'directory',
        'document': 'document',
        'files': 'files'
    }

    def __init__(self, directory=None, document=None, files=None, local_vars_configuration=None):  # noqa: E501
        """InlineObject1 - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration()
        self.local_vars_configuration = local_vars_configuration

        self._directory = None
        self._document = None
        self._files = None
        self.discriminator = None

        if directory is not None:
            self.directory = directory
        if document is not None:
            self.document = document
        if files is not None:
            self.files = files

    @property
    def directory(self):
        """Gets the directory of this InlineObject1.  # noqa: E501


        :return: The directory of this InlineObject1.  # noqa: E501
        :rtype: str
        """
        return self._directory

    @directory.setter
    def directory(self, directory):
        """Sets the directory of this InlineObject1.


        :param directory: The directory of this InlineObject1.  # noqa: E501
        :type directory: str
        """

        self._directory = directory

    @property
    def document(self):
        """Gets the document of this InlineObject1.  # noqa: E501


        :return: The document of this InlineObject1.  # noqa: E501
        :rtype: str
        """
        return self._document

    @document.setter
    def document(self, document):
        """Sets the document of this InlineObject1.


        :param document: The document of this InlineObject1.  # noqa: E501
        :type document: str
        """

        self._document = document

    @property
    def files(self):
        """Gets the files of this InlineObject1.  # noqa: E501


        :return: The files of this InlineObject1.  # noqa: E501
        :rtype: list[file]
        """
        return self._files

    @files.setter
    def files(self, files):
        """Sets the files of this InlineObject1.


        :param files: The files of this InlineObject1.  # noqa: E501
        :type files: list[file]
        """

        self._files = files

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, InlineObject1):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, InlineObject1):
            return True

        return self.to_dict() != other.to_dict()
