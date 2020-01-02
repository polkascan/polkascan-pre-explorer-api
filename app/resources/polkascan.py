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
from dogpile.cache.api import NO_VALUE
from sqlalchemy import func
from sqlalchemy import or_
from app.models.data import Block, Extrinsic, Event, RuntimeCall, RuntimeEvent, Runtime, RuntimeModule, \
    RuntimeCallParam, RuntimeEventAttribute, RuntimeType, RuntimeStorage, Account, Session, DemocracyProposal, Contract, \
    BlockTotal, SessionValidator, Log, DemocracyReferendum, AccountIndex, RuntimeConstant, SessionNominator, \
    DemocracyVote, CouncilMotion, CouncilVote, TechCommProposal, TechCommProposalVote, TreasuryProposal, Transfer, Did
from app.resources.base import JSONAPIResource, JSONAPIListResource, JSONAPIListResource2,JSONAPIDetailResource
from app.settings import SUBSTRATE_RPC_URL, SUBSTRATE_METADATA_VERSION, SUBSTRATE_ADDRESS_TYPE, TYPE_REGISTRY
from app.type_registry import load_type_registry
from app.utils.ss58 import ss58_decode, ss58_encode
from scalecodec.base import RuntimeConfiguration
from substrateinterface import SubstrateInterface
import json
import decimal
import datetime


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
        if 'transactions' in include_list:
            relationships['transactions'] = Extrinsic.query(self.session).filter_by(block_id=item.id, signed=1).order_by(
                'extrinsic_idx')
        if 'inherents' in include_list:
            relationships['inherents'] = Extrinsic.query(self.session).filter_by(block_id=item.id, signed=0).order_by(
                'extrinsic_idx')
        if 'events' in include_list:
            relationships['events'] = Event.query(self.session).filter_by(block_id=item.id, system=0).order_by(
                'event_idx')
        if 'logs' in include_list:
            relationships['logs'] = Log.query(self.session).filter_by(block_id=item.id).order_by(
                'log_idx')

        return relationships


class BlockListResource(JSONAPIListResource):

    def get_query(self):
        return Block.query(self.session).order_by(
            Block.id.desc()
        )


class BlockTotalDetailsResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        return BlockTotal.query(self.session).get(item_id)


class BlockTotalListResource(JSONAPIListResource):

    def get_query(self):
        return BlockTotal.query(self.session).order_by(
            BlockTotal.id.desc()
        )


class ExtrinsicListResource(JSONAPIListResource):

    def get_query(self):
        return Extrinsic.query(self.session).order_by(
            Extrinsic.block_id.desc()
        )

    def apply_filters(self, query, params):
        if params.get('filter[signed]'):

            query = query.filter_by(signed=params.get('filter[signed]'))

        if params.get('filter[module_id]'):

            query = query.filter_by(module_id=params.get('filter[module_id]'))

        if params.get('filter[call_id]'):

            query = query.filter_by(call_id=params.get('filter[call_id]'))

        if params.get('filter[address]'):

            if params.get('filter[address]')[0:2] == '0x':
                account_id = params.get('filter[address]')[2:]
            else:
                account_id = ss58_decode(params.get(
                    'filter[address]'), SUBSTRATE_ADDRESS_TYPE)

            query = query.filter_by(address=account_id)

        return query


class ExtrinsicDetailResource(JSONAPIDetailResource):

    def get_item_url_name(self):
        return 'extrinsic_id'

    def get_item(self, item_id):

        if item_id[0:2] == '0x':
            extrinsic = Extrinsic.query(self.session).filter_by(
                extrinsic_hash=item_id[2:]).first()
        else:
            extrinsic = Extrinsic.query(self.session).get(item_id.split('-'))

        return extrinsic

    def serialize_item(self, item):
        data = item.serialize()

        runtime_call = RuntimeCall.query(self.session).filter_by(
            module_id=item.module_id,
            call_id=item.call_id,
            spec_version=item.spec_version_id
        ).first()

        data['attributes']['documentation'] = runtime_call.documentation

        return data


class EventsListResource(JSONAPIListResource):

    def apply_filters(self, query, params):

        if params.get('filter[module_id]'):

            query = query.filter_by(module_id=params.get('filter[module_id]'))

        if params.get('filter[event_id]'):

            query = query.filter_by(event_id=params.get('filter[event_id]'))

        return query

    def get_query(self):
        return Event.query(self.session).filter(Event.system == False).order_by(
            Event.block_id.desc()
        )


class EventDetailResource(JSONAPIDetailResource):

    def get_item_url_name(self):
        return 'event_id'

    def get_item(self, item_id):
        return Event.query(self.session).get(item_id.split('-'))

    def serialize_item(self, item):
        data = item.serialize()

        runtime_event = RuntimeEvent.query(self.session).filter_by(
            module_id=item.module_id,
            event_id=item.event_id,
            spec_version=item.spec_version_id
        ).first()

        data['attributes']['documentation'] = runtime_event.documentation

        return data


class LogListResource(JSONAPIListResource):

    def get_query(self):
        return Log.query(self.session).order_by(
            Log.block_id.desc()
        )


class LogDetailResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        return Log.query(self.session).get(item_id.split('-'))


class NetworkStatisticsResource(JSONAPIResource):

    cache_expiration_time = 6

    def on_get(self, req, resp, network_id=None):
        resp.status = falcon.HTTP_200

        # TODO make caching more generic for custom resources

        cache_key = '{}-{}'.format(req.method, req.url)

        response = self.cache_region.get(cache_key, self.cache_expiration_time)

        if response is NO_VALUE:

            best_block = BlockTotal.query(self.session).filter_by(
                id=self.session.query(func.max(BlockTotal.id)).one()[0]).first()
            if best_block:
                response = self.get_jsonapi_response(
                    data={
                        'type': 'networkstats',
                        'id': network_id,
                        'attributes': {
                            'best_block': best_block.id,
                            'total_signed_extrinsics': int(best_block.total_extrinsics_signed),
                            'total_events': int(best_block.total_events),
                            'total_events_module': int(best_block.total_events_module),
                            'total_blocks': 'N/A',
                            'total_accounts': int(best_block.total_accounts),
                            'total_runtimes': Runtime.query(self.session).count()
                        }
                    },
                )
            else:
                response = self.get_jsonapi_response(
                    data={
                        'type': 'networkstats',
                        'id': network_id,
                        'attributes': {
                            'best_block': 0,
                            'total_signed_extrinsics': 0,
                            'total_events': 0,
                            'total_events_module': 0,
                            'total_blocks': 'N/A',
                            'total_accounts': 0,
                            'total_runtimes': 0
                        }
                    },
                )
            self.cache_region.set(cache_key, response)
            resp.set_header('X-Cache', 'MISS')
        else:
            resp.set_header('X-Cache', 'HIT')

        resp.media = response


class BalanceTransferListResource(JSONAPIListResource):

    def get_query(self):
        return Event.query(self.session).filter(
            Event.module_id == 'balances', Event.event_id == 'Transfer'
        ).order_by(Event.block_id.desc())

    def serialize_item(self, item):
        return {
            'type': 'balancetransfer',
            'id': '{}-{}'.format(item.block_id, item.event_idx),
            'attributes': {
                'block_id': item.block_id,
                'event_idx': '{}-{}'.format(item.block_id, item.event_idx),
                'sender': ss58_encode(item.attributes[0]['value'].replace('0x', ''), SUBSTRATE_ADDRESS_TYPE),
                'sender_id': item.attributes[0]['value'].replace('0x', ''),
                'destination': ss58_encode(item.attributes[1]['value'].replace('0x', ''), SUBSTRATE_ADDRESS_TYPE),
                'destination_id': item.attributes[1]['value'].replace('0x', ''),
                'value': item.attributes[2]['value'],
                'fee': item.attributes[3]['value']
            }
        }


class BalanceTransferDetailResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        return Event.query(self.session).get(item_id.split('-'))

    def serialize_item(self, item):
        return {
            'type': 'balancetransfer',
            'id': '{}-{}'.format(item.block_id, item.event_idx),
            'attributes': {
                'block_id': item.block_id,
                'event_idx': '{}-{}'.format(item.block_id, item.event_idx),
                'sender': ss58_encode(item.attributes[0]['value'].replace('0x', ''), SUBSTRATE_ADDRESS_TYPE),
                'sender_id': item.attributes[0]['value'].replace('0x', ''),
                'destination': ss58_encode(item.attributes[1]['value'].replace('0x', ''), SUBSTRATE_ADDRESS_TYPE),
                'destination_id': item.attributes[1]['value'].replace('0x', ''),
                'value': item.attributes[2]['value'],
                'fee': item.attributes[3]['value']
            }
        }


class TransferListResource(JSONAPIListResource2):
    
    def get_item_url_name(self):
        return 'did'

    def get_query(self,did):
        return Transfer.query(self.session).filter(or_(Transfer.from_did == did,Transfer.to_did == did)).order_by(Transfer.block_id.desc())

    def serialize_item(self, item):
        return {
            'type': 'transfer',
            'id': '{}-{}'.format(item.block_id, item.event_idx),
            'attributes': {
                'block_id': item.block_id,
                'event_idx': item.event_idx,
                'extrinsic_idx': item.extrinsic_idx,
                'from_account_id': item.from_account_id,
                'from_address': ss58_encode(item.from_account_id, SUBSTRATE_ADDRESS_TYPE),
                'to_account_id': item.to_account_id,
                'to_address': ss58_encode(item.to_account_id, SUBSTRATE_ADDRESS_TYPE),
                'balance': float(item.balance),
                'from_did': item.from_did,
                'to_did': item.to_did,
                'fee': float(item.fee),
                'datetime': item.datetime.isoformat()
            }
        }
    
def decimal_default_proc(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

class DidListResource(JSONAPIListResource):
    def get_query(self):
        return Did.query(self.session)
    
class DidDetailResource(JSONAPIDetailResource):
    def get_item(self, item_id):
        print(item_id)
        return Did.query(self.session).get(item_id).first()
        

class AccountResource(JSONAPIListResource):

    def get_query(self):
        return Account.query(self.session).order_by(
            Account.updated_at_block.desc()
        )


class AccountDetailResource(JSONAPIDetailResource):

    cache_expiration_time = 6

    def __init__(self):
        RuntimeConfiguration().update_type_registry(load_type_registry('default'))
        if TYPE_REGISTRY != 'default':
            RuntimeConfiguration().update_type_registry(load_type_registry(TYPE_REGISTRY))
        super(AccountDetailResource, self).__init__()

    def get_item(self, item_id):
        if item_id[0:2] == '0x':
            return Account.query(self.session).filter_by(id=item_id[2:]).first()
        else:
            return Account.query(self.session).filter_by(address=item_id).first()

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'recent_extrinsics' in include_list:
            relationships['recent_extrinsics'] = Extrinsic.query(self.session).filter_by(
                address=item.id).order_by(Extrinsic.block_id.desc())[:10]

        if 'indices' in include_list:
            relationships['indices'] = AccountIndex.query(self.session).filter_by(
                account_id=item.id).order_by(AccountIndex.updated_at_block.desc())

        return relationships

    def serialize_item(self, item):
        substrate = SubstrateInterface(
            SUBSTRATE_RPC_URL, metadata_version=SUBSTRATE_METADATA_VERSION)
        data = item.serialize()

        storage_call = RuntimeStorage.query(self.session).filter_by(
            module_id='balances',
            name='FreeBalance',
        ).order_by(RuntimeStorage.spec_version.desc()).first()

        data['attributes']['free_balance'] = substrate.get_storage(
            block_hash=None,
            module='Balances',
            function='FreeBalance',
            params=item.id,
            return_scale_type=storage_call.type_value,
            hasher=storage_call.type_hasher,
            metadata_version=SUBSTRATE_METADATA_VERSION
        )

        storage_call = RuntimeStorage.query(self.session).filter_by(
            module_id='balances',
            name='ReservedBalance',
        ).order_by(RuntimeStorage.spec_version.desc()).first()

        data['attributes']['reserved_balance'] = substrate.get_storage(
            block_hash=None,
            module='Balances',
            function='ReservedBalance',
            params=item.id,
            return_scale_type=storage_call.type_value,
            hasher=storage_call.type_hasher,
            metadata_version=SUBSTRATE_METADATA_VERSION
        )

        storage_call = RuntimeStorage.query(self.session).filter_by(
            module_id='system',
            name='AccountNonce',
        ).order_by(RuntimeStorage.spec_version.desc()).first()

        data['attributes']['nonce'] = substrate.get_storage(
            block_hash=None,
            module='System',
            function='AccountNonce',
            params=item.id,
            return_scale_type=storage_call.type_value,
            hasher=storage_call.type_hasher,
            metadata_version=SUBSTRATE_METADATA_VERSION
        )

        return data


class AccountIndexListResource(JSONAPIListResource):

    def get_query(self):
        return AccountIndex.query(self.session).order_by(
            AccountIndex.updated_at_block.desc()
        )


class AccountIndexDetailResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        return AccountIndex.query(self.session).filter_by(short_address=item_id).first()

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'recent_extrinsics' in include_list:
            relationships['recent_extrinsics'] = Extrinsic.query(self.session).filter_by(
                address=item.account_id).order_by(Extrinsic.block_id.desc())[:10]

        return relationships


class SessionListResource(JSONAPIListResource):

    cache_expiration_time = 60

    def get_query(self):
        return Session.query(self.session).order_by(
            Session.id.desc()
        )


class SessionDetailResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        return Session.query(self.session).get(item_id)

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'blocks' in include_list:
            relationships['blocks'] = Block.query(self.session).filter_by(
                session_id=item.id
            ).order_by(Block.id.desc())

        if 'validators' in include_list:
            relationships['validators'] = SessionValidator.query(self.session).filter_by(
                session_id=item.id
            ).order_by(SessionValidator.rank_validator)

        return relationships


class SessionValidatorListResource(JSONAPIListResource):

    cache_expiration_time = 60

    def get_query(self):
        return SessionValidator.query(self.session).order_by(
            SessionValidator.session_id, SessionValidator.rank_validator
        )

    def apply_filters(self, query, params):

        if params.get('filter[latestSession]'):

            session = Session.query(self.session).order_by(
                Session.id.desc()).first()

            query = query.filter_by(session_id=session.id)

        return query


class SessionValidatorDetailResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        session_id, rank_validator = item_id.split('-')
        return SessionValidator.query(self.session).filter_by(
            session_id=session_id,
            rank_validator=rank_validator
        ).first()

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'nominators' in include_list:
            relationships['nominators'] = SessionNominator.query(self.session).filter_by(
                session_id=item.session_id, rank_validator=item.rank_validator
            ).order_by(SessionNominator.rank_nominator)

        return relationships


class SessionNominatorListResource(JSONAPIListResource):

    cache_expiration_time = 60

    def get_query(self):
        return SessionNominator.query(self.session).order_by(
            SessionNominator.session_id, SessionNominator.rank_validator, SessionNominator.rank_nominator
        )

    def apply_filters(self, query, params):

        if params.get('filter[latestSession]'):

            session = Session.query(self.session).order_by(
                Session.id.desc()).first()

            query = query.filter_by(session_id=session.id)

        return query


class DemocracyProposalListResource(JSONAPIListResource):

    def get_query(self):
        return DemocracyProposal.query(self.session).order_by(
            DemocracyProposal.id.desc()
        )


class DemocracyProposalDetailResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        return DemocracyProposal.query(self.session).get(item_id)


class DemocracyReferendumListResource(JSONAPIListResource):

    def get_query(self):
        return DemocracyReferendum.query(self.session).order_by(
            DemocracyReferendum.id.desc()
        )

    def serialize_item(self, item):
        # Exclude large proposals from list view
        return item.serialize(exclude=['proposal'])


class DemocracyReferendumDetailResource(JSONAPIDetailResource):

    cache_expiration_time = 60

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'votes' in include_list:
            relationships['votes'] = DemocracyVote.query(self.session).filter_by(
                democracy_referendum_id=item.id
            ).order_by(DemocracyVote.updated_at_block.desc())

        return relationships

    def get_item(self, item_id):
        return DemocracyReferendum.query(self.session).get(item_id)


class CouncilMotionListResource(JSONAPIListResource):

    def get_query(self):
        return CouncilMotion.query(self.session).order_by(
            CouncilMotion.proposal_id.desc()
        )

    def serialize_item(self, item):
        # Exclude large proposals from list view
        return item.serialize(exclude=['proposal'])


class CouncilMotionDetailResource(JSONAPIDetailResource):

    cache_expiration_time = 60

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'votes' in include_list:
            relationships['votes'] = CouncilVote.query(self.session).filter_by(
                proposal_id=item.proposal_id
            ).order_by(CouncilVote.id.desc())

        return relationships

    def get_item(self, item_id):
        return CouncilMotion.query(self.session).get(item_id)


class TechCommProposalListResource(JSONAPIListResource):

    def get_query(self):
        return TechCommProposal.query(self.session).order_by(
            TechCommProposal.proposal_id.desc()
        )

    def serialize_item(self, item):
        # Exclude large proposals from list view
        return item.serialize(exclude=['proposal'])


class TechCommProposalDetailResource(JSONAPIDetailResource):

    cache_expiration_time = 60

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'votes' in include_list:
            relationships['votes'] = TechCommProposalVote.query(self.session).filter_by(
                proposal_id=item.proposal_id
            ).order_by(TechCommProposalVote.id.desc())

        return relationships

    def get_item(self, item_id):
        return TechCommProposal.query(self.session).get(item_id)


class TreasuryProposalListResource(JSONAPIListResource):

    def get_query(self):
        return TreasuryProposal.query(self.session).order_by(
            TreasuryProposal.proposal_id.desc()
        )


class TreasuryProposalDetailResource(JSONAPIDetailResource):

    cache_expiration_time = 60

    def get_item(self, item_id):
        return TreasuryProposal.query(self.session).get(item_id)


class ContractListResource(JSONAPIListResource):

    def get_query(self):
        return Contract.query(self.session).order_by(
            Contract.created_at_block.desc()
        )


class ContractDetailResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        return Contract.query(self.session).get(item_id)


class RuntimeListResource(JSONAPIListResource):

    cache_expiration_time = 60

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

    cache_expiration_time = 3600

    def apply_filters(self, query, params):

        if params.get('filter[latestRuntime]'):

            latest_runtime = Runtime.query(self.session).order_by(
                Runtime.spec_version.desc()).first()

            query = query.filter_by(spec_version=latest_runtime.spec_version)

        if params.get('filter[module_id]'):

            query = query.filter_by(module_id=params.get('filter[module_id]'))

        return query

    def get_query(self):
        return RuntimeCall.query(self.session).order_by(
            RuntimeCall.spec_version.asc(), RuntimeCall.module_id.asc(), RuntimeCall.call_id.asc()
        )


class RuntimeCallDetailResource(JSONAPIDetailResource):

    def get_item_url_name(self):
        return 'runtime_call_id'

    def get_item(self, item_id):
        spec_version, module_id, call_id = item_id.split('-')
        return RuntimeCall.query(self.session).filter_by(
            spec_version=spec_version,
            module_id=module_id,
            call_id=call_id
        ).first()

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

    cache_expiration_time = 3600

    def apply_filters(self, query, params):

        if params.get('filter[latestRuntime]'):

            latest_runtime = Runtime.query(self.session).order_by(
                Runtime.spec_version.desc()).first()

            query = query.filter_by(spec_version=latest_runtime.spec_version)

        if params.get('filter[module_id]'):

            query = query.filter_by(module_id=params.get('filter[module_id]'))

        return query

    def get_query(self):
        return RuntimeEvent.query(self.session).order_by(
            RuntimeEvent.spec_version.asc(), RuntimeEvent.module_id.asc(), RuntimeEvent.event_id.asc()
        )


class RuntimeEventDetailResource(JSONAPIDetailResource):

    def get_item_url_name(self):
        return 'runtime_event_id'

    def get_item(self, item_id):
        spec_version, module_id, event_id = item_id.split('-')
        return RuntimeEvent.query(self.session).filter_by(
            spec_version=spec_version,
            module_id=module_id,
            event_id=event_id
        ).first()

    def get_relationships(self, include_list, item):
        relationships = {}

        if 'attributes' in include_list:
            relationships['attributes'] = RuntimeEventAttribute.query(self.session).filter_by(
                runtime_event_id=item.id).order_by('id')

        if 'recent_events' in include_list:
            relationships['recent_events'] = Event.query(self.session).filter_by(
                event_id=item.event_id, module_id=item.module_id).order_by(Event.block_id.desc())[:10]

        return relationships


class RuntimeTypeListResource(JSONAPIListResource):

    cache_expiration_time = 3600

    def get_query(self):
        return RuntimeType.query(self.session).order_by(
            'spec_version', 'type_string'
        )

    def apply_filters(self, query, params):

        if params.get('filter[latestRuntime]'):

            latest_runtime = Runtime.query(self.session).order_by(
                Runtime.spec_version.desc()).first()

            query = query.filter_by(spec_version=latest_runtime.spec_version)

        return query


class RuntimeModuleListResource(JSONAPIListResource):

    cache_expiration_time = 3600

    def get_query(self):
        return RuntimeModule.query(self.session).order_by(
            'spec_version', 'name'
        )

    def apply_filters(self, query, params):

        if params.get('filter[latestRuntime]'):

            latest_runtime = Runtime.query(self.session).order_by(
                Runtime.spec_version.desc()).first()

            query = query.filter_by(spec_version=latest_runtime.spec_version)

        return query


class RuntimeModuleDetailResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        spec_version, module_id = item_id.split('-')
        return RuntimeModule.query(self.session).filter_by(spec_version=spec_version, module_id=module_id).first()

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

        if 'storage' in include_list:
            relationships['storage'] = RuntimeStorage.query(self.session).filter_by(
                spec_version=item.spec_version, module_id=item.module_id).order_by(
                'name')

        if 'constants' in include_list:
            relationships['constants'] = RuntimeConstant.query(self.session).filter_by(
                spec_version=item.spec_version, module_id=item.module_id).order_by(
                'name')

        return relationships


class RuntimeStorageDetailResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        spec_version, module_id, name = item_id.split('-')
        return RuntimeStorage.query(self.session).filter_by(
            spec_version=spec_version,
            module_id=module_id,
            name=name
        ).first()


class RuntimeConstantListResource(JSONAPIListResource):

    cache_expiration_time = 3600

    def get_query(self):
        return RuntimeConstant.query(self.session).order_by(
            RuntimeConstant.spec_version.desc(
            ), RuntimeConstant.module_id.asc(), RuntimeConstant.name.asc()
        )


class RuntimeConstantDetailResource(JSONAPIDetailResource):

    def get_item(self, item_id):
        spec_version, module_id, name = item_id.split('-')
        return RuntimeConstant.query(self.session).filter_by(
            spec_version=spec_version,
            module_id=module_id,
            name=name
        ).first()