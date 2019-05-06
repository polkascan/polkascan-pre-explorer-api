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

from app.models.data import Block, Extrinsic, Event, RuntimeCall, RuntimeEvent, Runtime, RuntimeModule, \
    RuntimeCallParam, RuntimeEventAttribute, RuntimeType
from app.models.data import Metadata
from app.resources.base import BaseResource, JSONAPIResource, JSONAPIListResource, JSONAPIDetailResource
from app.utils.ss58 import ss58_decode, ss58_encode


class BlockDetailsResource(JSONAPIDetailResource):

    def get_item_url_name(self):
        return 'block_id'

    def get_item(self, item_id):
        if item_id.isnumeric():
            return Block.query(self.session).filter_by(id=item_id).first()
        else:
            return Block.query(self.session).filter_by(hash=item_id).first()

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'extrinsics' in include_list:
            relationships['extrinsics'] = Extrinsic.query(self.session).filter_by(block_id=item.id).order_by(
                'extrinsic_idx')
        if 'events' in include_list:
            relationships['events'] = Event.query(self.session).filter_by(block_id=item.id, system=0).order_by(
                'event_idx')

        return relationships


class BlockListResource(JSONAPIListResource):

    def get_query(self):
        return Block.query(self.session).order_by(
            Block.id.desc()
        )

    def get_meta(self):
        return {
            'best_block': self.session.query(func.max(Block.id)).one()[0]
        }


class ExtrinsicListResource(JSONAPIListResource):

    def get_query(self):
        return Extrinsic.query(self.session).order_by(
            Extrinsic.block_id.desc(), Extrinsic.extrinsic_idx.asc()
        )

    def apply_filters(self, query, params):
        if params.get('filter[signed]'):

            query = query.filter_by(signed=params.get('filter[signed]'))

        if params.get('filter[module_id]'):

            query = query.filter_by(module_id=params.get('filter[module_id]'))

        if params.get('filter[call_id]'):

            query = query.filter_by(call_id=params.get('filter[call_id]'))

        return query


class ExtrinsicDetailResource(JSONAPIDetailResource):

    def get_item_url_name(self):
        return 'extrinsic_id'

    def get_item(self, item_id):
        extrinsic = Extrinsic.query(self.session).get(item_id.split('-'))

        if extrinsic and extrinsic.address:
            extrinsic.address = ss58_encode(extrinsic.address)

        return extrinsic


class EventsListResource(JSONAPIListResource):

    def get_query(self):
        return Event.query(self.session).filter(Event.system == False).order_by(
            Event.block_id.desc(), Event.event_idx.asc()
        )


class EventDetailResource(JSONAPIDetailResource):

    def get_item_url_name(self):
        return 'event_id'

    def get_item(self, item_id):
        return Event.query(self.session).get(item_id.split('-'))


class PolkascanNetworkStatisticsResource(JSONAPIResource):

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


class BalanceTransferResource(JSONAPIListResource):

    def get_query(self):
        return Extrinsic.query(self.session).filter(
            Extrinsic.module_id == 'balances' and Extrinsic.call_id == 'transfer'
        ).order_by(Extrinsic.block_id.desc())

    def apply_filters(self, query, params):
        if params.get('filter[address]'):

            if len(params.get('filter[address]')) == 64:
                account_id = params.get('filter[address]')
            else:
                account_id = ss58_decode(params.get('filter[address]'))

            return query.filter_by(address=account_id)

        return query

    def serialize_item(self, item):
        return {
                'type': 'balancetransfer',
                'id': '{}-{}'.format(item.block_id, item.extrinsic_idx),
                'attributes': {
                    'block_id': item.block_id,
                    'sender': ss58_encode(item.address),
                    'destination': ss58_encode(item.params[0]['value']),
                    'value': item.params[1]['value']
                }
        }


class RuntimeListResource(JSONAPIListResource):

    def get_query(self):
        return Runtime.query(self.session).order_by(
            Runtime.id.desc()
        )


class RuntimeDetailResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        return Runtime.query(self.session).get(item_id)

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'modules' in include_list:
            relationships['modules'] = RuntimeModule.query(self.session).filter_by(
                spec_version=item.spec_version
            ).order_by('lookup', 'id')

        if 'types' in include_list:
            relationships['types'] = RuntimeType.query(self.session).filter_by(
                spec_version=item.spec_version
            ).order_by('type_string')

        return relationships


class RuntimeCallListResource(JSONAPIListResource):

    def get_query(self):
        return RuntimeCall.query(self.session).order_by(
            RuntimeCall.spec_version.asc(), RuntimeCall.module_id.asc(), RuntimeCall.call_id.asc()
        )


class RuntimeCallDetailResource(JSONAPIDetailResource):

    def get_item_url_name(self):
        return 'runtime_call_id'

    def get_item(self, item_id):
        return RuntimeCall.query(self.session).get(item_id)

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'params' in include_list:
            relationships['params'] = RuntimeCallParam.query(self.session).filter_by(
                runtime_call_id=item.id).order_by('id')

        if 'recent_extrinsics' in include_list:
            relationships['recent_extrinsics'] = Extrinsic.query(self.session).filter_by(
                call_id=item.call_id, module_id=item.module_id).order_by(Extrinsic.block_id.desc())[:10]

        return relationships


class RuntimeEventListResource(JSONAPIListResource):

    def get_query(self):
        return RuntimeEvent.query(self.session).order_by(
            RuntimeEvent.spec_version.asc(), RuntimeEvent.module_id.asc(), RuntimeEvent.event_id.asc()
        )


class RuntimeEventDetailResource(JSONAPIDetailResource):

    def get_item_url_name(self):
        return 'runtime_event_id'

    def get_item(self, item_id):
        return RuntimeEvent.query(self.session).get(item_id)

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'attributes' in include_list:
            relationships['attributes'] = RuntimeEventAttribute.query(self.session).filter_by(
                runtime_event_id=item.id).order_by('id')

        if 'recent_events' in include_list:
            relationships['recent_events'] = Event.query(self.session).filter_by(
                event_id=item.event_id, module_id=item.module_id).order_by(Event.block_id.desc())[:10]


        return relationships


class RuntimeModuleDetailResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        return RuntimeModule.query(self.session).get(item_id)

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'calls' in include_list:
            relationships['calls'] = RuntimeCall.query(self.session).filter_by(
                spec_version=item.spec_version, module_id=item.module_id).order_by(
                'lookup', 'id')

        if 'events' in include_list:
            relationships['events'] = RuntimeEvent.query(self.session).filter_by(
                spec_version=item.spec_version, module_id=item.module_id).order_by(
                'lookup', 'id')

        return relationships
