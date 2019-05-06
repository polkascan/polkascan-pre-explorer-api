#  Polkascan PRE Explorer API
#
#  Copyright 2018-2019 openAware BV (NL).
#  This file is part of Polkascan.
#
#  Polkascan is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Polkascan is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Polkascan. If not, see <http://www.gnu.org/licenses/>.
#
#  settings.py
import os

DB_NAME = os.environ.get("DB_NAME", "polkascan")
DB_HOST = os.environ.get("DB_HOST", "mysql")
DB_PORT = os.environ.get("DB_PORT", 3306)
DB_USERNAME = os.environ.get("DB_USERNAME", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "root")

DB_CONNECTION = os.environ.get("DB_CONNECTION", "mysql+mysqlconnector://{}:{}@{}:{}/{}".format(
    DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
))

DEBUG = False

MAX_RESOURCE_PAGE_SIZE = 100

try:
    from app.local_settings import *
except ImportError:
    pass
