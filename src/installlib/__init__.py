"""
********************************************************************************
installlib
********************************************************************************

.. currentmodule:: installlib


.. toctree::
    :maxdepth: 1


"""

from __future__ import print_function

import os


__author__ = ["Chen Kasirer"]
__copyright__ = "Gramazio Kohler Research, ETH Zurich"
__license__ = "MIT License"
__email__ = "kasirer@arch.ethz.ch"
__version__ = "0.2.2"


HERE = os.path.dirname(__file__)

HOME = os.path.abspath(os.path.join(HERE, "../../"))
DOCS = os.path.abspath(os.path.join(HOME, "docs"))


__all__ = ["HOME", "DOCS"]
