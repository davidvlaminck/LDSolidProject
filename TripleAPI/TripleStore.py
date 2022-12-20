from collections import defaultdict
from typing import Generator, Set

from rdflib import Graph, URIRef, BNode


class TripleStore:
    def __init__(self):
        self._graph = None
        self._source = None

    def get_graph(self, source):
        if self._graph is None:
            self.load(source)
        else:
            if source != self._source:
                self.load(source)
        return self._graph

    def load(self, source):
        g = Graph()
        g.parse(source=source, format='turtle')
        self._graph = g
        print(f'loaded {len(self._graph)} triples')
        self._source = source

    def perform_sparql_query(self, q: str = '') -> dict:
        if q == '':
            return {}
        while '\n' in q:
            q = q.replace('\n', ' ')
        while '\r' in q:
            q = q.replace('\r', ' ')
        while '  ' in q:
            q = q.replace('  ', ' ')
        q = q.lower()

        reserved_list = ['update', 'delete', 'insert', 'load', 'create', 'drop', 'clear']
        for keyword in reserved_list:
            if keyword in q:
                raise PermissionError('Not allow to run this query')

        query = '''
        SELECT ?t
        WHERE { ?n a ?t }
'''
        result = self._graph.query(q)
        result_dict = {'headers': [], 'data': []}
        for key in result.vars:
            result_dict['headers'].append(str(key))
        for row in result:
            result_row = []
            for key in result.vars:
                result_row.append(str(row[key]))
            result_dict['data'].append(result_row)

        return result_dict

    def get_asset_triples(self, asset_id: str) -> Generator:
        if self._graph is None:
            raise RuntimeError('There is no datasource loaded yet')

        asset_ref = URIRef(f'https://data.awvvlaanderen.be/id/asset/{asset_id}')

        yield from self.yield_triples_found_by_subject(asset_ref)

    def yield_triples_found_by_subject(self, asset_ref: [URIRef, BNode]):
        for s, p, o in self._graph.triples((asset_ref, None, None)):
            yield s, p, o
            if isinstance(o, BNode):
                yield from self.yield_triples_found_by_subject(o)

    def get_all_related_triples(self, asset_ref: URIRef, use_relations=None):
        if use_relations is None:
            use_relations = []
        also_get = []
        for s, p, o in self.yield_triples_found_by_subject(asset_ref):
            yield s, p, o
            if p in use_relations:
                also_get.append(o)
        for also in also_get:
            yield from self.get_all_related_triples(also, use_relations=use_relations)
