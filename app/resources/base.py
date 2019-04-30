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
#  base.py
from abc import ABC, abstractmethod

import falcon
from sqlalchemy.orm import Session

from app.settings import MAX_RESOURCE_PAGE_SIZE


class BaseResource(object):

    session: Session


class JSONAPIResource(BaseResource):

    def apply_filters(self, query, params):
        return query

    def get_meta(self):
        return {}

    def serialize_item(self, item):
        return item.serialize()

    def get_jsonapi_response(self, data, meta=None, errors=None, links=None, relationships=None, included=None):

        result = {
            'meta': {
                "authors": [
                    "WEB3SCAN",
                    "POLKASCAN",
                    "openAware BV"
                ]
            },
            'errors': [],
            "data": data,
            "links": {}
        }

        if meta:
            result['meta'].update(meta)

        if errors:
            result['errors'] = errors

        if links:
            result['links'] = links

        if included:
            result['included'] = included

        if relationships:
            result['data']['relationships'] = {}

            if 'included' not in result:
                result['included'] = []

            for key, objects in relationships.items():
                result['data']['relationships'][key] = {'data': [{'type': obj.serialize_type, 'id': obj.serialize_id()} for obj in objects]}
                result['included'] += [obj.serialize() for obj in objects]

        return result


class JSONAPIListResource(JSONAPIResource, ABC):

    @abstractmethod
    def get_query(self):
        raise NotImplementedError()

    def apply_paging(self, query, params):
        page = int(params.get('page[number]', 0))
        page_size = min(int(params.get('page[size]', 25)), MAX_RESOURCE_PAGE_SIZE)
        return query[page * page_size: page * page_size + page_size]

    def on_get(self, req, resp):

        items = self.get_query()
        items = self.apply_filters(items, req.params)
        items = self.apply_paging(items, req.params)

        resp.status = falcon.HTTP_200
        resp.media = self.get_jsonapi_response(
            data=[self.serialize_item(item) for item in items],
            meta=self.get_meta()
        )


class JSONAPIDetailResource(JSONAPIResource, ABC):

    def get_item_url_name(self):
        return 'item_id'

    @abstractmethod
    def get_item(self, item_id):
        raise NotImplementedError()

    def get_relationships(self, include_list, item):
        return {}

    def on_get(self, req, resp, **kwargs):
        item = self.get_item(kwargs.get(self.get_item_url_name()))

        if not item:
            resp.status = falcon.HTTP_404

        else:

            resp.status = falcon.HTTP_200
            resp.media = self.get_jsonapi_response(
                data=item.serialize(),
                relationships=self.get_relationships(req.params.get('include') or [], item),
                meta=self.get_meta()
            )
