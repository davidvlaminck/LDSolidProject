from typing import Generator

from rdflib import URIRef, BNode

from TripleAPI.TripleStore import TripleStore


class TripleStoreAPI:
    def __init__(self, store: TripleStore):
        self.store = store
        if self.store._source is not None:
            self.source = self.store._source

    def perform_sparql_query(self, query: str = '') -> dict:
        if query == '':
            return {}
        while '\n' in query:
            query = query.replace('\n', ' ')
        while '\r' in query:
            query = query.replace('\r', ' ')
        while '  ' in query:
            query = query.replace('  ', ' ')
        query = query.lower()

        reserved_list = ['update', 'delete', 'insert', 'load', 'create', 'drop', 'clear']
        for keyword in reserved_list:
            if keyword in query:
                raise PermissionError('Not allow to run this query')

        q = '''
        SELECT ?t (COUNT(?n) as ?count) 
        WHERE { ?n a ?t }
        GROUP BY ?t
        '''

        return self.store.perform_sparql_query(query=query)

    def get_asset_triples(self, asset_id: str) -> Generator:
        if self.store.get_graph(self.source) is None:
            raise RuntimeError('There is no datasource loaded yet')

        asset_ref = URIRef(f'https://data.awvvlaanderen.be/id/asset/{asset_id}')

        yield from self.yield_triples_found_by_subject(asset_ref)

    def yield_triples_found_by_subject(self, asset_ref: [URIRef, BNode]):
        for s, p, o in self.store.get_graph(self.source).triples((asset_ref, None, None)):
            yield s, p, o
            if isinstance(o, BNode):
                yield from self.yield_triples_found_by_subject(o)

    def get_all_related_triples(self, asset_ref: URIRef, use_relations=None) -> Generator:
        if use_relations is None:
            use_relations = []
        also_get = []
        for s, p, o in self.yield_triples_found_by_subject(asset_ref):
            yield s, p, o
            if p in use_relations:
                also_get.append(o)
        for also in also_get:
            yield from self.get_all_related_triples(also, use_relations=use_relations)

    def get_full_opstelling_triples(self, id) -> Generator:
        relations_to_use = [URIRef('https://data.vlaanderen.be/ns/mobiliteit#omvatVerkeersbord'),
                            URIRef('https://data.vlaanderen.be/ns/mobiliteit#realiseert'),
                            URIRef('https://data.vlaanderen.be/ns/mobiliteit#heeftVerkeersbordconcept'),
                            URIRef('https://data.vlaanderen.be/ns/mobiliteit#hoortBij')]
        yield from self.get_all_related_triples(
            asset_ref=URIRef('https://apps.mow.vlaanderen.be/verkeersborden/rest/zi/verkeersborden/' + id),
            use_relations=relations_to_use)


