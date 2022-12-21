from unittest import TestCase

from rdflib import URIRef

from TripleAPI.TripleStore import TripleStore
from TripleAPI.TripleStoreAPI import TripleStoreAPI


class TripleStoreTests(TestCase):
    def test_get_all_related_assets(self):
        store = TripleStore()
        store_source = 'CreatingData/vkb_oslo_1000.ttl'
        store.get_graph(store_source)

        relations_to_use = [URIRef('https://data.vlaanderen.be/ns/mobiliteit#omvatVerkeersbord'),
                            URIRef('https://data.vlaanderen.be/ns/mobiliteit#realiseert'),
                            URIRef('https://data.vlaanderen.be/ns/mobiliteit#heeftVerkeersbordconcept'),
                            URIRef('https://data.vlaanderen.be/ns/mobiliteit#hoortBij')]

        result = store.get_all_related_triples(
            URIRef('https://apps.mow.vlaanderen.be/verkeersborden/rest/zi/verkeersborden/1044565'), # 102806 (simple)
            use_relations=relations_to_use)
        for s, p, o in result:
            print(f'{s} {p} {o}')

    def test_get_opstellingen_by_bounds(self):
        store = TripleStore()
        store_source = 'CreatingData/vkb_oslo_1000.ttl'
        store.get_graph(store_source)
        triple_api = TripleStoreAPI(store)
        for triple in triple_api.get_opstellingen_by_bounds(lower_lat=51.03, lower_long=3.65, upper_lat=51.05, upper_long=3.75):
            print(triple)

    def test_get_opstellingen_by_wegsegment(self):
        store = TripleStore()
        store_source = 'CreatingData/vkb_oslo_1000.ttl'
        store.get_graph(store_source)
        triple_api = TripleStoreAPI(store)
        for triple in triple_api.get_opstellingen_by_wegsegment(wegsegment_id='665218'):
            print(triple)


# example query for bounds
"""
prefix mob: <https://data.vlaanderen.be/ns/mobiliteit#> 
prefix loc: <http://www.w3.org/ns/locn#>
prefix geo: <http://www.w3.org/2003/01/geo/wgs84_pos#> 
prefix xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?s ?lat ?long
WHERE {
  ?s loc:geometry ?g .
  ?g geo:lat ?lat .
  ?g geo:long ?long .
  FILTER (51.03 < ?lat && ?lat < 51.05 && 3.65 < ?long && ?long < 3.75) .
}"""