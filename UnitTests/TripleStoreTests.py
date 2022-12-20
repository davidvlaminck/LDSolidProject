from unittest import TestCase

from rdflib import URIRef

from TripleAPI.TripleStore import TripleStore


class TripleStoreTests(TestCase):
    def test_get_all_related_assets(self):
        store = TripleStore()
        store_source = 'CreatingData/vkb_oslo_1000.ttl'
        store.get_graph(store_source)

        relations_to_use = [URIRef('https://data.vlaanderen.be/ns/mobiliteit#omvatVerkeersbord'),
                            URIRef('https://data.vlaanderen.be/ns/mobiliteit#realiseert'),
                            URIRef('https://data.vlaanderen.be/ns/mobiliteit#heeftVerkeersbordconcept')]

        result = store.get_all_related_triples(
            URIRef('https://apps.mow.vlaanderen.be/verkeersborden/rest/zi/verkeersborden/1044565'), # 102806 (simple)
            use_relations=relations_to_use)
        for s, p, o in result:
            print(f'{s} {p} {o}')
