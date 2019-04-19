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
#  polkascan.py

import falcon
from sqlalchemy import func

from app.models.data import Block, Extrinsic, Event
from app.models.data import Metadata
from app.resources.base import BaseResource
from app.settings import MAX_RESOURCE_PAGE_SIZE
from app.utils.ss58 import ss58_decode, ss58_encode


class PolkascanHeadResource(BaseResource):
    def on_get(self, req, resp):
        head_obj = Block.get_head(self.session)

        resp.status = falcon.HTTP_200
        resp.media = {
            "head": head_obj
        }


class PolkascanBlockDetailsResource(BaseResource):

    def on_get(self, req, resp, block_id=None):
        if block_id:
            if block_id.isnumeric():
                block = Block.query(self.session).filter_by(id=block_id).first()
            else:
                block = Block.query(self.session).filter_by(hash=block_id).first()
        else:
            block = None

        if not block:
            resp.status = falcon.HTTP_404
        else:

            # Attach extrinsics and events
            relationships = None
            #TODO make generic
            if req.params.get('include'):
                include_relationships = req.params.get('include')
                relationships = {}
                if 'extrinsics' in include_relationships:
                    relationships['extrinsics'] = Extrinsic.query(self.session).filter_by(block_id=block.id).order_by('extrinsic_idx')
                if 'events' in include_relationships:
                    relationships['events'] = Event.query(self.session).filter_by(block_id=block.id, system=0).order_by('event_idx')

            resp.status = falcon.HTTP_200
            resp.media = self.get_jsonapi_response(
                data=block.serialize(),
                relationships=relationships
            )


class PolkascanBlockListResource(BaseResource):

    def on_get(self, req, resp):

        # TODO make generic
        page = int(req.params.get('page[number]', 0))
        page_size = min(int(req.params.get('page[size]', 25)), MAX_RESOURCE_PAGE_SIZE)

        blocks = Block.query(self.session).order_by(
            Block.id.desc()
        )[page * page_size: page * page_size + page_size]

        resp.status = falcon.HTTP_200
        resp.media = self.get_jsonapi_response(
            data=[block.serialize() for block in blocks],
            meta={
                'best_block': self.session.query(func.max(Block.id)).one()[0]
            }
        )


class PolkascanExtrinsicListResource(BaseResource):

    def on_get(self, req, resp):

        # TODO make generic
        page = int(req.params.get('page[number]', 0))
        page_size = min(int(req.params.get('page[size]', 25)), MAX_RESOURCE_PAGE_SIZE)

        extrinsics = Extrinsic.query(self.session).order_by(
            Extrinsic.block_id.desc(), Extrinsic.extrinsic_idx.asc()
        )[page * page_size: (page * page_size) + page_size]

        resp.status = falcon.HTTP_200
        resp.media = self.get_jsonapi_response(
            data=[extrinsic.serialize() for extrinsic in extrinsics]
        )


class PolkascanEventsListResource(BaseResource):

    def on_get(self, req, resp):

        # TODO make generic
        page = int(req.params.get('page[number]', 0))
        page_size = min(int(req.params.get('page[size]', 25)), MAX_RESOURCE_PAGE_SIZE)

        events = Event.query(self.session).filter(Event.system == False).order_by(
            Event.block_id.desc(), Event.event_idx.asc()
        )[page * page_size: (page * page_size) + page_size]

        resp.status = falcon.HTTP_200
        resp.media = self.get_jsonapi_response(
            data=[event.serialize() for event in events]
        )


class PolkascanNetworkStatisticsResource(BaseResource):

    def on_get(self, req, resp, network_id=None):
        resp.status = falcon.HTTP_200

        resp.media = self.get_jsonapi_response(
            data={
                'type': 'networkstats',
                'id': network_id,
                'attributes': {
                    'best_block': self.session.query(func.max(Block.id)).one()[0],
                    'total_signed_extrinsics': Extrinsic.query(self.session).filter_by(signed=1).count(),
                    'total_events': Event.query(self.session).count(),
                    'total_blocks': Block.query(self.session).count(),
                    'total_runtimes': Metadata.query(self.session).count()
                }
            },
        )


class PolkascanBalanceTransferResource(BaseResource):

    def on_get(self, req, resp):
        page = int(req.params.get('page[number]', 0))
        page_size = int(req.params.get('page[size]', 25))

        balance_transfers = Extrinsic.query(self.session).filter(
            Extrinsic.module_id == 'balances' and Extrinsic.call_id == 'transfer'
        ).order_by(Extrinsic.block_id.desc())

        # Apply filters
        # TODO make generic
        if req.params.get('filter[address]'):

            if len(req.params.get('filter[address]')) == 64:
                account_id = req.params.get('filter[address]')
            else:
                account_id = ss58_decode(req.params.get('filter[address]'))

            balance_transfers = balance_transfers.filter_by(address=account_id)

        # Apply paging
        # TODO make generic
        balance_transfers = balance_transfers[page * page_size: page * page_size + page_size]

        resp.status = falcon.HTTP_200
        resp.media = self.get_jsonapi_response(
            data=[{
                'type': 'balancetransfer',
                'id': '{}-{}'.format(transfer.block_id, transfer.extrinsic_idx),
                'attributes': {
                    'block_id': transfer.block_id,
                    'sender': ss58_encode(transfer.address),
                    'destination': ss58_encode(transfer.params[0]['value']),
                    'value': transfer.params[1]['value']
                }
            } for transfer in balance_transfers],
        )


class PolkascanExtrinsicDetailResource(BaseResource):

    def on_get(self, req, resp, extrinsic_id=None):

        rich_extrinsic = None

        if extrinsic_id:
            rich_extrinsic = Extrinsic.query(self.session).get(extrinsic_id.split('-'))

        if not rich_extrinsic:
            resp.status = falcon.HTTP_404
        else:
            resp.status = falcon.HTTP_200
            resp.media = self.get_jsonapi_response(data=rich_extrinsic.serialize())


class PolkascanEventDetailResource(BaseResource):

    def on_get(self, req, resp, event_id=None):

        if event_id:
            event = Event.query(self.session).get(event_id.split('-'))
            resp.status = falcon.HTTP_200
            resp.media = self.get_jsonapi_response(data=event.serialize())
        else:
            resp.status = falcon.HTTP_404

