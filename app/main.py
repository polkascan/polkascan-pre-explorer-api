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
#  main.py

from app.settings import DB_CONNECTION, DEBUG

import falcon

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.middleware.context import ContextMiddleware
from app.middleware.sessionmanager import SQLAlchemySessionManager

from app.resources import polkascan

# Database connection
engine = create_engine(DB_CONNECTION, echo=DEBUG, isolation_level="READ_UNCOMMITTED")
session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Define application
app = falcon.API(middleware=[ContextMiddleware(), SQLAlchemySessionManager(session_factory)])

# Application routes
app.add_route('/system/block', polkascan.PolkascanBlockListResource())
app.add_route('/system/block/{block_id}', polkascan.PolkascanBlockDetailsResource())
app.add_route('/system/extrinsic/{extrinsic_id}', polkascan.PolkascanExtrinsicDetailResource())
app.add_route('/system/event/{event_id}', polkascan.PolkascanEventDetailResource())
app.add_route('/system/networkstats/{network_id}', polkascan.PolkascanNetworkStatisticsResource())
app.add_route('/balance/transfers', polkascan.PolkascanBalanceTransferResource())
