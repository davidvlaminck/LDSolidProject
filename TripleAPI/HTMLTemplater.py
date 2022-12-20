from typing import Generator

from rdflib import URIRef
from starlette.responses import HTMLResponse


class HTMLTemplater:
    @staticmethod
    def get_opstelling_html(id: str, triples: Generator):
        triple_table = """<table>
        <tr>
        <th>subject</th>
        <th>predicate</th>
        <th>object</th>
        </tr>"""

        count = 0
        for s, p, o in triples:
            count += 1
            if isinstance(s, URIRef):
                s = f'<a href="{s}">{s}</a>'
            if isinstance(p, URIRef):
                p = f'<a href="{p}">{p}</a>'
            if isinstance(o, URIRef):
                o = f'<a href="{o}">{o}</a>'
            triple_table += f"""
            <tr>
                <td>{s}</td>
                <td>{p}</td>
                <td>{o}</td>
            </tr>"""

        triple_table += """
        </table>"""

        if count == 0:
            html_content = f"""
                    <!-- if you were expecting a json reponse, add 'application/json' to the 'accept' header -->
                    <html>
                        <head>
                            <title>Opstelling information</title>
                        </head>
                        <body>
                            <h4>id {id} matches no opstelling!</h4>
                        </body>
                    </html>
                    """
            return HTMLResponse(content=html_content)

        html_content = """
            <!-- if you were expecting a json reponse, add 'application/json' to the 'accept' header -->
            <html>
                <head>
                    <title>Opstelling information</title>  
                    <style>
                        table {
                            width: 100%;
                        }
                        table, th, td {
                            border: 1px solid;
                            border-collapse: collapse;
                            font-size: 0.95em;
                        }
                    </style>              
                </head>""" + f"""
                <body>
                    <h2>opstelling {id}</h2>
                    <h4>Triple representation</h4>
                    {triple_table}
                <p>Took $time_spent$ seconds to generate</p>
                </body>
            </html>
            """

        return html_content
