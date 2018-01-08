import argparse
import re
import xmlrpc.client
import functools
import sys
from abc import *
from urllib.parse import urlparse

VIDEO_CONNECTOR_TYPES = {
    'VGA',
    'HDMI',
    'DP',
}

class ChameleonEdid:
    """ An edid object on the chamelium """
    __slots__ = [
        '__id',
        '__chameleon'
    ]

    def __init__(self, chameleon, blob):
        """
        Arguments:
            chameleon - The chameleon this EDID lives on
            blob - A binary object containing the EDID data
        """
        self.__id = chameleon.CreateEdid(blob)
        self.__chameleon = chameleon

    def __del__(self):
        self.__chameleon.DestroyEdid(self.id)

    @property
    def id(self):
        """ The ID of this edid on the chameleon """
        return self.__id

class CHAMELEON_DEFAULT_EDID:
    """ The default edid used by the chamelium """
    id = 0
