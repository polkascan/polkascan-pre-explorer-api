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
from app.settings import DB_CONNECTION, DEBUG, DOGPILE_CACHE_SETTINGS

import falcon

from dogpile.cache import make_region

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.middleware.context import ContextMiddleware
from app.middleware.sessionmanager import SQLAlchemySessionManager
from app.middleware.cache import CacheMiddleware

from app.resources import polkascan

# Database connection
engine = create_engine(DB_CONNECTION, echo=DEBUG, isolation_level="READ_UNCOMMITTED")
session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Define cache region
cache_region = make_region().configure(
            'dogpile.cache.redis',
            arguments={
                'host': DOGPILE_CACHE_SETTINGS['host'],
                'port': DOGPILE_CACHE_SETTINGS['port'],
                'db': DOGPILE_CACHE_SETTINGS['db'],
                'redis_expiration_time': 60*60*2,   # 2 hours
                'distributed_lock': True
            }
)

# Define application
app = falcon.API(middleware=[
    ContextMiddleware(),
    SQLAlchemySessionManager(session_factory),
    CacheMiddleware(cache_region)
])

# Application routes
app.add_route('/system/block', polkascan.BlockListResource())
app.add_route('/system/block/{block_id}', polkascan.BlockDetailsResource())
app.add_route('/system/extrinsic', polkascan.ExtrinsicListResource())
app.add_route('/system/extrinsic/{extrinsic_id}', polkascan.ExtrinsicDetailResource())
app.add_route('/system/event', polkascan.EventsListResource())
app.add_route('/system/event/{event_id}', polkascan.EventDetailResource())
app.add_route('/system/runtime', polkascan.RuntimeListResource())
app.add_route('/system/runtime/{item_id}', polkascan.RuntimeDetailResource())
app.add_route('/system/runtime-call', polkascan.RuntimeCallListResource())
app.add_route('/system/runtime-call/{runtime_call_id}', polkascan.RuntimeCallDetailResource())
app.add_route('/system/runtime-event', polkascan.RuntimeEventListResource())
app.add_route('/system/runtime-event/{runtime_event_id}', polkascan.RuntimeEventDetailResource())
app.add_route('/system/runtime-module/{item_id}', polkascan.RuntimeModuleDetailResource())
app.add_route('/system/runtime-storage/{item_id}', polkascan.RuntimeStorageDetailResource())
app.add_route('/system/networkstats/{network_id}', polkascan.NetworkStatisticsResource())
app.add_route('/balance/transfers', polkascan.BalanceTransferResource())
app.add_route('/balances/account', polkascan.AccountResource())
app.add_route('/balances/account/{item_id}', polkascan.AccountDetailResource())
app.add_route('/session/session', polkascan.SessionListResource())
app.add_route('/session/session/{item_id}', polkascan.SessionDetailResource())
app.add_route('/democracy/proposal', polkascan.DemocracyProposalListResource())
app.add_route('/democracy/proposal/{item_id}', polkascan.DemocracyProposalDetailResource())
app.add_route('/contract/contract', polkascan.ContractListResource())
app.add_route('/contract/contract/{item_id}', polkascan.ContractDetailResource())
