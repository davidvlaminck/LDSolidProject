from typing import Generator

from rdflib import URIRef, BNode, Graph, Namespace

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

    @staticmethod
    async def create_graph_from_triples(triples):
        g = Graph()
        g.bind('mob', Namespace('https://data.vlaanderen.be/ns/mobiliteit#'))
        g.bind('vkb', Namespace('https://apps.mow.vlaanderen.be/verkeersborden/rest/zi/verkeersborden/'))
        g.bind('asset', Namespace('https://data.awvvlaanderen.be/id/asset/'))
        g.bind('wr',
               Namespace('https://www.vlaanderen.be/digitaal-vlaanderen/onze-oplossingen/wegenregister/'))
        g.bind('orgvl', 'https://data.vlaanderen.be/doc/organisatie/')
        g.bind('od', 'https://data.vlaanderen.be/ns/openbaardomein#')
        g.bind('geo', 'http://www.w3.org/2003/01/geo/wgs84_pos#')
        g.bind('loc', 'http://www.w3.org/ns/locn#')
        g.bind('skos', 'http://www.w3.org/2004/02/skos/core#')
        g.bind('weg', 'https://data.vlaanderen.be/ns/weg#')
        g.bind('org', 'http://www.w3.org/ns/org#')
        for triple in triples:
            g.add(triple)
        return g

    def get_opstellingen_by_bounds(self, lower_lat: float, lower_long: float, upper_lat: float, upper_long: float):
        query = '''
prefix mob: <https://data.vlaanderen.be/ns/mobiliteit#>
prefix loc: <http://www.w3.org/ns/locn#>
prefix geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

SELECT ?s
WHERE {
    ?s loc:geometry ?g .
    ?g geo:lat ?lat .
    ?g geo:long ?long .''' + \
                f'FILTER ({lower_lat} < ?lat && ?lat < {upper_lat} && {lower_long} < ?long && ?long < {upper_long}) .' \
                + '}'
        results = self.perform_sparql_query(query)
        for row in results['data']:
            yield from self.yield_triples_found_by_subject(URIRef(row[0]))

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
