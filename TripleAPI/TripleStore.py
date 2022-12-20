from rdflib import Graph


class TripleStore:
    def __init__(self):
        self._graph = None
        self._source = None

    def get_graph(self, source=None):
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

    def perform_sparql_query(self, query: str = '') -> dict:
        result = self._graph.query(query)
        result_dict = {'headers': [], 'data': []}
        for key in result.vars:
            result_dict['headers'].append(str(key))
        for row in result:
            result_row = []
            for key in result.vars:
                result_row.append(str(row[key]))
            result_dict['data'].append(result_row)

        return result_dict
