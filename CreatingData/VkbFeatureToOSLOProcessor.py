from pathlib import Path

from rdflib import Graph, RDF, URIRef, Literal, BNode, XSD, Namespace
from pyproj import CRS, Transformer

from CreatingData.DataHelpers.VkbFeature import VkbFeature


class VkbFeatureToOSLOProcessor:
    def __init__(self):
        self.graph = Graph()
        self.graph.bind('mob', Namespace('https://data.vlaanderen.be/ns/mobiliteit#'))
        self.graph.bind('vkb', Namespace('https://apps.mow.vlaanderen.be/verkeersborden/rest/zi/verkeersborden/'))
        self.graph.bind('asset', Namespace('https://data.awvvlaanderen.be/id/asset/'))
        self.graph.bind('wr',
                        Namespace('https://www.vlaanderen.be/digitaal-vlaanderen/onze-oplossingen/wegenregister/'))
        self.graph.bind('orgvl', 'https://data.vlaanderen.be/doc/organisatie/')
        self.graph.bind('od', 'https://data.vlaanderen.be/ns/openbaardomein#')
        self.graph.bind('geo', 'http://www.w3.org/2003/01/geo/wgs84_pos#')
        self.graph.bind('loc', 'http://www.w3.org/ns/locn#')

        self.load_beheerders()

        crs_lambert72 = CRS.from_epsg(31370)
        crs_wgs = CRS.from_epsg(4326)
        self.transformer = Transformer.from_crs(crs_lambert72, crs_wgs)

    def process_to_oslo(self, feature: VkbFeature) -> None:

        opstelling_ref = URIRef(f'https://apps.mow.vlaanderen.be/verkeersborden/rest/zi/verkeersborden/{feature.id}')

        self.graph.add((opstelling_ref, RDF.type, URIRef('https://data.vlaanderen.be/ns/mobiliteit#Opstelling')))

        # geometrie van de opstelling
        # wgs84_pos.rdf
        coords = self.transformer.transform(feature.coords[0], feature.coords[1])
        geo_ref = BNode()
        self.graph.add((opstelling_ref, URIRef('http://www.w3.org/ns/locn#geometry'), geo_ref))
        self.graph.add((geo_ref, RDF.type, URIRef('http://www.w3.org/2003/01/geo/wgs84_pos#Point')))
        self.graph.add((geo_ref, URIRef('http://www.w3.org/2003/01/geo/wgs84_pos#lat'), Literal(coords[0], datatype=XSD.decimal)))
        self.graph.add((geo_ref, URIRef('http://www.w3.org/2003/01/geo/wgs84_pos#long'), Literal(coords[1], datatype=XSD.decimal)))


        feature_objects = [opstelling_ref]
        onderborden = []

        for index, wegsegment_id in enumerate(feature.wegsegment_ids):
            self.graph.add((
                opstelling_ref, URIRef('https://data.vlaanderen.be/ns/mobiliteit#hoortBij'),
                URIRef(
                    f'https://www.vlaanderen.be/digitaal-vlaanderen/onze-oplossingen/wegenregister/{wegsegment_id}')))

        for f_bord in feature.borden:
            bord_ref = URIRef(f'https://data.awvvlaanderen.be/id/asset/{feature.id}_bord_{f_bord.id}')
            feature_objects.append(bord_ref)

            # is onderbord
            if f_bord.bord_code[0] == 'G':
                onderborden.append(f_bord)

            self.graph.add(
                (opstelling_ref, URIRef('https://data.vlaanderen.be/ns/mobiliteit#omvatVerkeersbord'), bord_ref))

            # opstelhoogte
            if f_bord.y > 0:
                hoogte_kwant_node = BNode()
                self.graph.add(
                    (bord_ref, URIRef('https://data.vlaanderen.be/ns/mobiliteit#opstelhoogte'), hoogte_kwant_node))
                self.graph.add((hoogte_kwant_node, URIRef('https://schema.org/value'),
                                Literal(f_bord.y / 1000.0, datatype=XSD.decimal)))
                self.graph.add((hoogte_kwant_node, URIRef('https://schema.org/unitCode'), Literal('MTR')))

            # aanzicht
            self.graph.add((opstelling_ref, URIRef('https://data.vlaanderen.be/ns/mobiliteit#aanzicht'),
                            Literal(str(f_bord.aanzicht_hoek))))

            # beheerder
            ovo_code = self.beheerders.get(feature.beheerder_code, None)
            if ovo_code is None:
                ovo_code = self.beheerders.get(feature.beheerder_naam, None)
            if ovo_code is None:
                feature.beheerder_naam = feature.beheerder_naam.replace(' (na 2019)', '').replace('Provincie ', '').replace('Vlaams Brabant', 'Vlaams-Brabant')
            if ovo_code is None and 'Gemeente' in feature.beheerder_naam:
                ovo_code = self.beheerders.get(feature.beheerder_naam.replace('Gemeente', 'Stad'), None)
            if ovo_code is not None:
                self.graph.add((bord_ref, URIRef('https://data.vlaanderen.be/ns/openbaardomein#beheerder'),
                                URIRef(f'https://data.vlaanderen.be/doc/organisatie/{ovo_code}')))
            else:
                print(f'no beheerder: {feature.beheerder_code} {feature.beheerder_naam}')

            # verkeersteken
            teken_ref = URIRef(f'https://data.awvvlaanderen.be/id/asset/{feature.id}_bord_{f_bord.id}_teken')
            self.graph.add((bord_ref, URIRef('https://data.vlaanderen.be/ns/mobiliteit#realiseert'), teken_ref))

            if f_bord.bord_code[0] == 'G' and len(f_bord.parameters) > 0:
                self.graph.add((teken_ref, URIRef('https://data.vlaanderen.be/ns/mobiliteit#variabelOpschrift'),
                                Literal(' '.join(f_bord.parameters))))

            # verkeersbordconcept
            concept_ref = URIRef(f'https://data.awvvlaanderen.be/id/asset/{feature.id}_bord_{f_bord.id}_concept')
            self.graph.add(
                (teken_ref, URIRef('https://data.vlaanderen.be/ns/mobiliteit#heeftVerkeersbordconcept'), concept_ref))
            self.graph.add((concept_ref, URIRef('http://www.w3.org/2004/02/skos/core#prefLabel'),
                            Literal(f_bord.bord_code)))

        if len(onderborden) > 0:
            for onderbord in onderborden:
                if onderbord.y == 0:
                    continue
                candidates = list(filter(lambda b: b.y > onderbord.y and b.y > 0 and f_bord.bord_code[0] != 'G',
                                         feature.borden))
                if len(candidates) == 0:
                    continue
                candidates = list(reversed(sorted(candidates, key=lambda b: b.y)))

                onderbord_teken_ref = URIRef(
                    f'https://data.awvvlaanderen.be/id/asset/{feature.id}_bord_{onderbord.id}_teken')
                bord_teken_ref = URIRef(
                    f'https://data.awvvlaanderen.be/id/asset/{feature.id}_bord_{candidates[0].id}_teken')

                self.graph.add((bord_teken_ref, URIRef('https://data.vlaanderen.be/ns/mobiliteit#heeftOnderbord'),
                                onderbord_teken_ref))

    def load_beheerders(self):
        beheerders = {}

        with open(Path('export_organisaties_20221220_123854.csv'), encoding='utf-8') as f:
            for line in f.readlines()[1:]:
                splitted = line.split(';')
                beheerders[splitted[1].replace('\n', '')] = splitted[0]

        with open(Path('WDB_beheerders.txt'), encoding='utf-8') as f:
            while True:
                try:
                    line1 = f.readline()[:-1]
                    line2 = f.readline()[:-1]
                    line3 = f.readline()[:-1]
                    line4 = f.readline()[:-1]

                    if line1 == line2 == line3 == line4 == '':
                        break
                    if line2 == 'Nee':
                        continue

                    if line4[0:3] == 'OVO':
                        beheerders[line1] = line4
                        if line3 == ' ':
                            beheerders[line3] = line4

                except ValueError:
                    break

        self.beheerders = beheerders
