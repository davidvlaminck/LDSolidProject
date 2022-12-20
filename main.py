import itertools
import json
import time
import os, psutil
from enum import Enum

import pyparsing
from fastapi import FastAPI, HTTPException
from fastapi.responses import ORJSONResponse
from rdflib import Graph, URIRef
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response

from TripleAPI import HtmlTemplate
from TripleAPI.TripleStore import TripleStore

app = FastAPI()

origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = TripleStore()
store_source = 'CreatingData/vkb_oslo_1000.ttl'
start = time.time()
store.get_graph(store_source)
end = time.time()
time_spent = round(end - start, 2)
print(f'Time to load db: {time_spent}')


@app.get("/")
async def root():
    return 'root'


@app.get("/sparql", response_class=Response)
async def sparql(request: Request, query: str = ''):
    if 'text/html' in request.headers['accept']:
        with open('TripleAPI/HtmlSparql.html', 'r+') as f:
            html_str = f.read()
        return html_str
    else:
        encoder = json.encoder.JSONEncoder()
        print(f'query: {query}')
        try:
            result = encoder.encode(o=store.perform_sparql_query(query))
        except PermissionError:
            print('403')
            raise HTTPException(status_code=403, detail="Not allowed to run this query")
        except pyparsing.exceptions.ParseException as exc:
            print('400')
            error_msg = f'Not able to parse this query: {exc}'
            raise HTTPException(status_code=400, detail=error_msg)
        return result


@app.get("/opstelling/{asset_id}", response_class=HTMLResponse)
async def get_asset(asset_id: str = ''):
    start = time.time()
    relations_to_use = [URIRef('https://data.vlaanderen.be/ns/mobiliteit#omvatVerkeersbord'),
                        URIRef('https://data.vlaanderen.be/ns/mobiliteit#realiseert'),
                        URIRef('https://data.vlaanderen.be/ns/mobiliteit#heeftVerkeersbordconcept')]
    triples = store.get_all_related_triples(
        asset_ref=URIRef('https://apps.mow.vlaanderen.be/verkeersborden/rest/zi/verkeersborden/' + asset_id),
        use_relations=relations_to_use)

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
                        <h4>id {asset_id} matches no opstelling!</h4>
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
                <h2>opstelling {asset_id}</h2>
                <h4>Triple representation</h4>
                {triple_table}"""

    end = time.time()
    time_spent = round(end - start, 3)
    print(f'Time to process query: {time_spent}')
    html_content += f"""
        <p>Took {time_spent} seconds to generate</p>
        </body>
    </html>
    """

    return HTMLResponse(content=html_content)

@app.get("/opstelling/{asset_id}/visualize", response_class=HTMLResponse)
async def get_asset(asset_id: str = ''):
    relations_to_use = [URIRef('https://data.vlaanderen.be/ns/mobiliteit#omvatVerkeersbord'),
                        URIRef('https://data.vlaanderen.be/ns/mobiliteit#realiseert'),
                        URIRef('https://data.vlaanderen.be/ns/mobiliteit#heeftVerkeersbordconcept')]
    triples = store.get_all_related_triples(
        asset_ref=URIRef('https://apps.mow.vlaanderen.be/verkeersborden/rest/zi/verkeersborden/' + asset_id),
        use_relations=relations_to_use)

    end = time.time()
    time_spent = round(end - start, 2)
    print(f'Time to process query: {time_spent}')

    triple_lines = []
    triple_count = 0
    for s, p, o in triples:
        triple_count += 1
        triple_lines.append('{subject:"' + str(s) + '", predicate:"' + str(p) + '", object:"' + str(o) + '"},')

    if triple_count == 0:
        html_content = f"""
                <!-- if you were expecting a json reponse, add 'application/json' to the 'accept' header -->
                <html>
                    <head>
                        <title>Opstelling information</title>
                    </head>
                    <body>
                        <h4>id {asset_id} matches no opstelling!</h4>
                    </body>
                </html>
                """
        return HTMLResponse(content=html_content)

    html_content = HtmlTemplate.html_template_string
    html_content = html_content.replace('$$$triples$$$', '\n'.join(triple_lines))
    html_content = html_content.replace('$time_spent$', str(time_spent))
    html_content = html_content.replace('$triple_count$', str(triple_count))

    return HTMLResponse(content=html_content)

process = psutil.Process(os.getpid())
print(f'using {process.memory_info().rss / 1024 ** 2} MB of memory')  # in Mbytes

# uvicorn main:app --reload

# https://fastapi.tiangolo.com/tutorial/first-steps/

# http://127.0.0.1:8000/docs#/default
# http://127.0.0.1:8000/opstelling/1000007 table
# http://127.0.0.1:8000/opstelling/1000007/visualize
# http://127.0.0.1:8000/opstelling/1000007/visualize2
