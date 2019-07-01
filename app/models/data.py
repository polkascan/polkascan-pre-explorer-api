#  Polkascan PRE Harvester
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
#  data.py

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.dialects.mysql import LONGTEXT

from app.models.base import BaseModel
from app.utils.ss58 import ss58_encode


data_block = sa.Table('data_block', BaseModel.metadata,
    sa.Column('id', sa.Integer(), primary_key=True, autoincrement=False),
    sa.Column('parent_id', sa.Integer(), nullable=False),
    sa.Column('hash', sa.String(66), unique=True, index=True, nullable=False),
    sa.Column('parent_hash', sa.String(66), index=True, nullable=False),
    sa.Column('state_root', sa.String(66), nullable=False),
    sa.Column('extrinsics_root', sa.String(66), nullable=False),
    sa.Column('count_extrinsics', sa.Integer(), nullable=False),
    sa.Column('count_extrinsics_unsigned', sa.Integer(), nullable=False),
    sa.Column('count_extrinsics_signed', sa.Integer(), nullable=False),
    sa.Column('count_extrinsics_error', sa.Integer(), nullable=False),
    sa.Column('count_extrinsics_success', sa.Integer(), nullable=False),
    sa.Column('count_extrinsics_signedby_address', sa.Integer(), nullable=False),
    sa.Column('count_extrinsics_signedby_index', sa.Integer(), nullable=False),
    sa.Column('count_events', sa.Integer(), nullable=False),
    sa.Column('count_events_system', sa.Integer(), nullable=False),
    sa.Column('count_events_module', sa.Integer(), nullable=False),
    sa.Column('count_events_extrinsic', sa.Integer(), nullable=False),
    sa.Column('count_events_finalization', sa.Integer(), nullable=False),
    sa.Column('count_accounts', sa.Integer(), nullable=False),
    sa.Column('count_accounts_new', sa.Integer(), nullable=False),
    sa.Column('count_accounts_reaped', sa.Integer(), nullable=False),
    sa.Column('count_sessions_new', sa.Integer(), nullable=False),
    sa.Column('count_contracts_new', sa.Integer(), nullable=False),
    sa.Column('count_log', sa.Integer(), nullable=False),
    sa.Column('range10000', sa.Integer(), nullable=False),
    sa.Column('range100000', sa.Integer(), nullable=False),
    sa.Column('range1000000', sa.Integer(), nullable=False),
    sa.Column('datetime', sa.DateTime(timezone=True)),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('week', sa.Integer(), nullable=True),
    sa.Column('day', sa.Integer(), nullable=True),
    sa.Column('hour', sa.Integer(), nullable=True),
    sa.Column('full_month', sa.Integer(), nullable=True),
    sa.Column('full_week', sa.Integer(), nullable=True),
    sa.Column('full_day', sa.Integer(), nullable=True),
    sa.Column('full_hour', sa.Integer(), nullable=True),
    sa.Column('logs', sa.JSON(), default=None, server_default=None),
    sa.Column('spec_version_id', sa.String(64), nullable=False),
    sa.Column('debug_info', sa.JSON(), default=None, server_default=None)
)

data_block_total = sa.Table('data_block_total', BaseModel.metadata,
    sa.Column('id', sa.ForeignKey('data_block.id'), primary_key=True, autoincrement=False),
    sa.Column('parent_datetime', sa.DateTime()),
    sa.Column('blocktime', sa.Integer(), nullable=False),
    sa.Column('total_extrinsics', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_extrinsics_success', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_extrinsics_error', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_extrinsics_signed', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_extrinsics_unsigned', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_extrinsics_signedby_address', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_extrinsics_signedby_index', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_events', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_events_system', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_events_module', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_events_extrinsic', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_events_finalization', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_logs', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_blocktime', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_accounts', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_accounts_new', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_accounts_reaped', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_sessions_new', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('total_contracts_new', sa.Numeric(precision=65, scale=0), nullable=False),
    sa.Column('session_id', sa.Integer())
)


class Block(BaseModel):
    __table__ = sa.join(data_block, data_block_total)

    serialize_exclude = ['debug_info']

    serialize_type = 'block'

    id = column_property(
        data_block.c.id,
        data_block_total.c.id
    )
    parent_id = data_block.c.parent_id
    hash = data_block.c.hash
    parent_hash = data_block.c.parent_hash
    state_root = data_block.c.state_root
    extrinsics_root = data_block.c.extrinsics_root
    count_extrinsics = data_block.c.count_extrinsics
    count_extrinsics_unsigned = data_block.c.count_extrinsics_unsigned
    count_extrinsics_signed = data_block.c.count_extrinsics_signed
    count_extrinsics_error = data_block.c.count_extrinsics_error
    count_extrinsics_success = data_block.c.count_extrinsics_success
    count_extrinsics_signedby_address = data_block.c.count_extrinsics_signedby_address
    count_extrinsics_signedby_index = data_block.c.count_extrinsics_signedby_index
    count_events = data_block.c.count_events
    count_events_system = data_block.c.count_events_system
    count_events_module = data_block.c.count_events_module
    count_events_extrinsic = data_block.c.count_events_extrinsic
    count_events_finalization = data_block.c.count_events_finalization
    count_accounts = data_block.c.count_accounts
    count_accounts_new = data_block.c.count_accounts_new
    count_accounts_reaped = data_block.c.count_accounts_reaped
    count_sessions_new = data_block.c.count_sessions_new
    count_contracts_new = data_block.c.count_contracts_new
    count_log = data_block.c.count_log
    range10000 = data_block.c.range10000
    range100000 = data_block.c.range100000
    range1000000 = data_block.c.range1000000
    datetime = data_block.c.datetime
    year = data_block.c.year
    month = data_block.c.month
    week = data_block.c.week
    day = data_block.c.day
    hour = data_block.c.hour
    full_month = data_block.c.full_month
    full_week = data_block.c.full_week
    full_day = data_block.c.full_day
    full_hour = data_block.c.full_hour
    logs = data_block.c.logs
    spec_version_id = data_block.c.spec_version_id
    debug_info = data_block.c.debug_info

    parent_datetime = data_block_total.c.parent_datetime
    blocktime = data_block_total.c.blocktime
    total_extrinsics = data_block_total.c.total_extrinsics
    total_extrinsics_success = data_block_total.c.total_extrinsics_success
    total_extrinsics_error = data_block_total.c.total_extrinsics_error
    total_extrinsics_signed = data_block_total.c.total_extrinsics_signed
    total_extrinsics_unsigned = data_block_total.c.total_extrinsics_unsigned
    total_extrinsics_signedby_address = data_block_total.c.total_extrinsics_signedby_address
    total_extrinsics_signedby_index = data_block_total.c.total_extrinsics_signedby_index
    total_events = data_block_total.c.total_events
    total_events_system = data_block_total.c.total_events_system
    total_events_module = data_block_total.c.total_events_module
    total_events_extrinsic = data_block_total.c.total_events_extrinsic
    total_events_finalization = data_block_total.c.total_events_finalization
    total_logs = data_block_total.c.total_logs
    total_blocktime = data_block_total.c.total_blocktime
    total_accounts = data_block_total.c.total_accounts
    total_accounts_new = data_block_total.c.total_accounts_new
    total_accounts_reaped = data_block_total.c.total_accounts_reaped
    total_sessions_new = data_block_total.c.total_sessions_new
    total_contracts_new = data_block_total.c.total_contracts_new
    session_id = data_block_total.c.session_id

    @classmethod
    def get_head(cls, session):
        with session.begin():
            query = session.query(cls)
            model = query.order_by(cls.id.desc()).first()

        return model

    @classmethod
    def get_missing_block_ids(cls, session):
        return session.execute(text("""
                                            SELECT
                                              z.expected as block_from, z.got-1 as block_to
                                            FROM (
                                             SELECT
                                              @rownum:=@rownum+1 AS expected,
                                              IF(@rownum=id, 0, @rownum:=id) AS got
                                             FROM
                                              (SELECT @rownum:=0) AS a
                                              JOIN data_block
                                              ORDER BY id
                                             ) AS z
                                            WHERE z.got!=0
                                            ORDER BY block_from DESC
                                            """)
                               )


class Event(BaseModel):
    __tablename__ = 'data_event'

    block_id = sa.Column(sa.Integer(), primary_key=True, index=True)
    block = relationship(Block, foreign_keys=[block_id], primaryjoin=block_id == Block.id)

    event_idx = sa.Column(sa.Integer(), primary_key=True, index=True)

    extrinsic_idx = sa.Column(sa.Integer(), index=True)

    type = sa.Column(sa.String(4), index=True)

    spec_version_id = sa.Column(sa.Integer())

    module_id = sa.Column(sa.String(64), index=True)
    event_id = sa.Column(sa.String(64), index=True)

    system = sa.Column(sa.SmallInteger(), index=True, nullable=False)
    module = sa.Column(sa.SmallInteger(), index=True, nullable=False)
    phase = sa.Column(sa.SmallInteger())

    attributes = sa.Column(sa.JSON())

    codec_error = sa.Column(sa.Boolean())

    def serialize_id(self):
        return '{}-{}'.format(self.block_id, self.event_idx)

    def serialize_formatting_hook(self, obj_dict):

        for item in obj_dict['attributes']['attributes']:
            if item['type'] == 'AccountId' and item['value']:
                # SS58 format AccountId public keys
                item['value'] = ss58_encode(item['value'].replace('0x', ''))

        return obj_dict


class Extrinsic(BaseModel):
    __tablename__ = 'data_extrinsic'

    block_id = sa.Column(sa.Integer(), primary_key=True, index=True)
    block = relationship(Block, foreign_keys=[block_id], primaryjoin=block_id == Block.id)

    extrinsic_idx = sa.Column(sa.Integer(), primary_key=True, index=True)
    extrinsic_hash = sa.Column(sa.String(64), index=True, nullable=True)

    extrinsic_length = sa.Column(sa.String(10))
    extrinsic_version = sa.Column(sa.String(2))

    signed = sa.Column(sa.SmallInteger(), index=True, nullable=False)
    unsigned = sa.Column(sa.SmallInteger(), index=True, nullable=False)
    signedby_address = sa.Column(sa.SmallInteger(), nullable=False)
    signedby_index = sa.Column(sa.SmallInteger(), nullable=False)

    address_length = sa.Column(sa.String(2))
    address = sa.Column(sa.String(64), index=True)
    account_index = sa.Column(sa.String(16), index=True)
    account_idx = sa.Column(sa.Integer(), index=True)
    signature = sa.Column(sa.String(128))
    nonce = sa.Column(sa.Integer())

    era = sa.Column(sa.String(4))

    call = sa.Column(sa.String(4))
    module_id = sa.Column(sa.String(64), index=True)
    call_id = sa.Column(sa.String(64), index=True)
    params = sa.Column(sa.JSON())

    success = sa.Column(sa.SmallInteger(), default=0, nullable=False)
    error = sa.Column(sa.SmallInteger(), default=0, nullable=False)

    spec_version_id = sa.Column(sa.Integer())

    codec_error = sa.Column(sa.Boolean(), default=False)

    def serialize_id(self):
        return '{}-{}'.format(self.block_id, self.extrinsic_idx)

    def serialize_formatting_hook(self, obj_dict):

        if obj_dict['attributes'].get('address'):
            obj_dict['attributes']['address'] = ss58_encode(obj_dict['attributes']['address'].replace('0x', ''))

        for item in obj_dict['attributes']['params']:
            if item['type'] == 'Address' and item['value']:
                # SS58 format Addresses public keys
                item['value'] = ss58_encode(item['value'].replace('0x', ''))

        return obj_dict


class Log(BaseModel):
    __tablename__ = 'data_log'

    block_id = sa.Column(sa.Integer(), primary_key=True, autoincrement=False)
    log_idx = sa.Column(sa.Integer(), primary_key=True, autoincrement=False)
    type_id = sa.Column(sa.Integer())
    type = sa.Column(sa.String(64))
    data = sa.Column(sa.JSON())


class Account(BaseModel):
    __tablename__ = 'data_account'

    id = sa.Column(sa.String(64), primary_key=True)
    address = sa.Column(sa.String(48), index=True)
    is_reaped = sa.Column(sa.Boolean, default=False)
    is_validator = sa.Column(sa.Boolean, default=False)
    is_nominator = sa.Column(sa.Boolean, default=False)
    is_contract = sa.Column(sa.Boolean, default=False)
    count_reaped = sa.Column(sa.Integer(), default=0)
    balance = sa.Column(sa.Numeric(precision=65, scale=0), nullable=False)
    created_at_block = sa.Column(sa.Integer(), nullable=False)
    updated_at_block = sa.Column(sa.Integer(), nullable=False)

    def serialize_id(self):
        return self.address


class AccountAudit(BaseModel):
    __tablename__ = 'data_account_audit'

    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True)
    account_id = sa.Column(sa.String(64), primary_key=True)
    block_id = sa.Column(sa.Integer(), index=True, nullable=False)
    extrinsic_idx = sa.Column(sa.Integer())
    event_idx = sa.Column(sa.Integer())
    type_id = sa.Column(sa.Integer(), nullable=False)
    data = sa.Column(sa.JSON(), default=None, server_default=None, nullable=True)


data_session = sa.Table('data_session', BaseModel.metadata,
    sa.Column('id', sa.Integer(), primary_key=True, autoincrement=False),
    sa.Column('start_at_block', sa.Integer()),
    sa.Column('era', sa.Integer()),
    sa.Column('era_idx', sa.Integer()),
    sa.Column('created_at_block', sa.Integer(), nullable=False),
    sa.Column('created_at_extrinsic', sa.Integer()),
    sa.Column('created_at_event', sa.Integer()),
    sa.Column('count_validators', sa.Integer()),
    sa.Column('count_nominators', sa.Integer())
)


data_session_total = sa.Table('data_session_total', BaseModel.metadata,
    sa.Column('id', sa.Integer(), sa.ForeignKey('data_session.id'), primary_key=True, autoincrement=False),
    sa.Column('end_at_block', sa.Integer()),
    sa.Column('count_blocks', sa.Integer())
)


class Session(BaseModel):
    __table__ = sa.outerjoin(data_session, data_session_total)

    id = column_property(
        data_session.c.id,
        data_session_total.c.id
    )

    start_at_block = data_session.c.start_at_block
    era = data_session.c.era
    era_idx = data_session.c.era_idx
    created_at_block = data_session.c.created_at_block
    created_at_extrinsic = data_session.c.created_at_extrinsic
    created_at_event = data_session.c.created_at_event
    count_validators = data_session.c.count_validators
    count_nominators = data_session.c.count_nominators
    end_at_block = data_session_total.c.end_at_block
    count_blocks = data_session_total.c.count_blocks


class SessionValidator(BaseModel):
    __tablename__ = 'data_session_validator'

    session_id = sa.Column(sa.Integer(), primary_key=True, autoincrement=False)
    validator = sa.Column(sa.String(64), index=True, primary_key=True)
    rank_validator = sa.Column(sa.Integer(), nullable=True)
    count_nominators = sa.Column(sa.Integer(), nullable=True)


class SessionNominator(BaseModel):
    __tablename__ = 'data_session_nominator'

    session_id = sa.Column(sa.Integer(), primary_key=True, autoincrement=False)
    validator = sa.Column(sa.String(64), index=True, primary_key=True)
    nominator = sa.Column(sa.String(64), index=True, primary_key=True)


class AccountIndex(BaseModel):
    __tablename__ = 'data_account_index'

    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=False)
    short_address = sa.Column(sa.String(24), index=True)
    account_id = sa.Column(sa.String(64), index=True)
    is_reclaimable = sa.Column(sa.Boolean, default=False)
    is_reclaimed = sa.Column(sa.Boolean, default=False)
    created_at_block = sa.Column(sa.Integer(), nullable=False)
    updated_at_block = sa.Column(sa.Integer(), nullable=False)


class AccountIndexAudit(BaseModel):
    __tablename__ = 'data_account_index_audit'

    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True)
    account_index_id = sa.Column(sa.Integer(), nullable=True, index=True)
    account_id = sa.Column(sa.String(64), index=True, nullable=False)
    block_id = sa.Column(sa.Integer(), index=True, nullable=False)
    extrinsic_idx = sa.Column(sa.Integer())
    event_idx = sa.Column(sa.Integer())
    type_id = sa.Column(sa.Integer(), nullable=False)
    data = sa.Column(sa.JSON(), default=None, server_default=None, nullable=True)


class DemocracyProposal(BaseModel):
    __tablename__ = 'data_democracy_proposal'

    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=False)
    proposal = sa.Column(sa.JSON(), default=None, server_default=None, nullable=True)
    bond = sa.Column(sa.Numeric(precision=65, scale=0), nullable=False)
    created_at_block = sa.Column(sa.Integer(), nullable=False)
    updated_at_block = sa.Column(sa.Integer(), nullable=False)
    status = sa.Column(sa.String(64))


class DemocracyProposalAudit(BaseModel):
    __tablename__ = 'data_democracy_proposal_audit'

    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=True)
    democracy_proposal_id = sa.Column(sa.Integer(), nullable=False, index=True)
    block_id = sa.Column(sa.Integer(), index=True, nullable=False)
    extrinsic_idx = sa.Column(sa.Integer())
    event_idx = sa.Column(sa.Integer())
    type_id = sa.Column(sa.Integer(), nullable=False)
    data = sa.Column(sa.JSON(), default=None, server_default=None, nullable=True)


class Contract(BaseModel):
    __tablename__ = 'data_contract'

    code_hash = sa.Column(sa.String(64), primary_key=True)
    bytecode = sa.Column(LONGTEXT())
    source = sa.Column(LONGTEXT())
    abi = sa.Column(sa.JSON(), default=None, server_default=None, nullable=True)
    compiler = sa.Column(sa.String(64))
    created_at_block = sa.Column(sa.Integer(), nullable=False)
    created_at_extrinsic = sa.Column(sa.Integer())
    created_at_event = sa.Column(sa.Integer())

    def serialize_id(self):
        return self.code_hash


class Runtime(BaseModel):
    __tablename__ = 'runtime'

    serialize_exclude = ['json_metadata', 'json_metadata_decoded']

    id = sa.Column(sa.Integer(), primary_key=True, autoincrement=False)
    impl_name = sa.Column(sa.String(255))
    impl_version = sa.Column(sa.Integer())
    spec_version = sa.Column(sa.Integer(), nullable=False, unique=True)
    spec_name = sa.Column(sa.String(255))
    authoring_version = sa.Column(sa.Integer())
    apis = sa.Column(sa.JSON(), default=None, server_default=None, nullable=True)
    json_metadata = sa.Column(sa.JSON(), default=None, server_default=None, nullable=True)
    json_metadata_decoded = sa.Column(sa.JSON(), default=None, server_default=None, nullable=True)
    count_modules = sa.Column(sa.Integer(), default=0, nullable=False)
    count_call_functions = sa.Column(sa.Integer(), default=0, nullable=False)
    count_storage_functions = sa.Column(sa.Integer(), default=0, nullable=False)
    count_events = sa.Column(sa.Integer(), default=0, nullable=False)

    def serialize_id(self):
        return self.spec_version


class RuntimeModule(BaseModel):
    __tablename__ = 'runtime_module'
    __table_args__ = (sa.UniqueConstraint('spec_version', 'module_id'),)

    id = sa.Column(sa.Integer(), primary_key=True)
    spec_version = sa.Column(sa.Integer(), nullable=False)
    module_id = sa.Column(sa.String(64), nullable=False)
    prefix = sa.Column(sa.String(255))
    # TODO unused?
    code = sa.Column(sa.String(255))
    name = sa.Column(sa.String(255))
    # TODO unused?
    lookup = sa.Column(sa.String(4), index=True)
    count_call_functions = sa.Column(sa.Integer(), nullable=False)
    count_storage_functions = sa.Column(sa.Integer(), nullable=False)
    count_events = sa.Column(sa.Integer(), nullable=False)

    def serialize_id(self):
        return '{}-{}'.format(self.spec_version, self.module_id)


class RuntimeCall(BaseModel):
    __tablename__ = 'runtime_call'
    __table_args__ = (sa.UniqueConstraint('spec_version', 'module_id', 'call_id'),)

    id = sa.Column(sa.Integer(), primary_key=True)
    spec_version = sa.Column(sa.Integer(), nullable=False)
    module_id = sa.Column(sa.String(64), nullable=False)
    call_id = sa.Column(sa.String(64), nullable=False)
    index = sa.Column(sa.Integer(), nullable=False)
    prefix = sa.Column(sa.String(255))
    code = sa.Column(sa.String(255))
    name = sa.Column(sa.String(255))
    lookup = sa.Column(sa.String(4), index=True)
    documentation = sa.Column(sa.Text())
    count_params = sa.Column(sa.Integer(), nullable=False)

    def serialize_id(self):
        return '{}-{}-{}'.format(self.spec_version, self.module_id, self.call_id)


class RuntimeCallParam(BaseModel):
    __tablename__ = 'runtime_call_param'
    __table_args__ = (sa.UniqueConstraint('runtime_call_id', 'name'),)

    id = sa.Column(sa.Integer(), primary_key=True)
    runtime_call_id = sa.Column(sa.Integer(), nullable=False)
    name = sa.Column(sa.String(255))
    type = sa.Column(sa.String(255))


class RuntimeEvent(BaseModel):
    __tablename__ = 'runtime_event'
    __table_args__ = (sa.UniqueConstraint('spec_version', 'module_id', 'event_id'),)

    id = sa.Column(sa.Integer(), primary_key=True)
    spec_version = sa.Column(sa.Integer(), nullable=False)
    module_id = sa.Column(sa.String(64), nullable=False)
    event_id = sa.Column(sa.String(64), nullable=False)
    index = sa.Column(sa.Integer(), nullable=False)
    prefix = sa.Column(sa.String(255))
    code = sa.Column(sa.String(255))
    name = sa.Column(sa.String(255))
    lookup = sa.Column(sa.String(4), index=True)
    documentation = sa.Column(sa.Text())
    count_attributes = sa.Column(sa.Integer(), nullable=False)

    def serialize_id(self):
        return '{}-{}-{}'.format(self.spec_version, self.module_id, self.event_id)


class RuntimeEventAttribute(BaseModel):
    __tablename__ = 'runtime_event_attribute'
    __table_args__ = (sa.UniqueConstraint('runtime_event_id', 'index'),)

    id = sa.Column(sa.Integer(), primary_key=True)
    runtime_event_id = sa.Column(sa.Integer(), nullable=False)
    index = sa.Column(sa.Integer(), nullable=False)
    type = sa.Column(sa.String(255))


class RuntimeStorage(BaseModel):
    __tablename__ = 'runtime_storage'

    id = sa.Column(sa.Integer(), primary_key=True)
    spec_version = sa.Column(sa.Integer())
    module_id = sa.Column(sa.String(64))
    storage_key = sa.Column(sa.String(32))
    index = sa.Column(sa.Integer())
    name = sa.Column(sa.String(255))
    lookup = sa.Column(sa.String(4), index=True)
    default = sa.Column(sa.String(255))
    modifier = sa.Column(sa.String(64))
    type_hasher = sa.Column(sa.String(255))
    type_key1 = sa.Column(sa.String(255))
    type_key2 = sa.Column(sa.String(255))
    type_value = sa.Column(sa.String(255))
    type_is_linked = sa.Column(sa.SmallInteger())
    type_key2hasher = sa.Column(sa.String(255))
    documentation = sa.Column(sa.Text())

    def serialize_id(self):
        return '{}-{}-{}'.format(self.spec_version, self.module_id, self.name)


class RuntimeType(BaseModel):
    __tablename__ = 'runtime_type'
    __table_args__ = (sa.UniqueConstraint('spec_version', 'type_string'),)

    id = sa.Column(sa.Integer(), primary_key=True)
    spec_version = sa.Column(sa.Integer(), nullable=False)
    type_string = sa.Column(sa.String(255))
    decoder_class = sa.Column(sa.String(255), nullable=True)
