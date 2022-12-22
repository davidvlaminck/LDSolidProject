import json
import time
import os, psutil
from enum import Enum

import pyparsing
from fastapi import FastAPI, HTTPException
from fastapi.responses import ORJSONResponse
from rdflib import URIRef
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response

from TripleAPI.HtmlTemplates.HTMLTemplater import HTMLTemplater
from TripleAPI.HtmlTemplates import VisualizeD3
from TripleAPI.TripleStore import TripleStore
from TripleAPI.TripleStoreAPI import TripleStoreAPI

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
store_source = 'CreatingData/vkb_oslo_30k.ttl'
api_start = time.time()
store.get_graph(store_source)
api_end = time.time()
api_time_spent = round(api_end - api_start, 2)
print(f'Time to load db: {api_time_spent}')
triple_store_api = TripleStoreAPI(store)


@app.get("/")
async def root():
    return 'root'


@app.get("/sparql", response_class=Response)
async def sparql(request: Request, query: str = ''):
    if 'text/html' in request.headers['accept']:
        with open('TripleAPI/HtmlTemplates/HtmlSparql.html', 'r+') as f:
            html_str = f.read()
        return html_str
    else:
        encoder = json.encoder.JSONEncoder()
        try:
            result = encoder.encode(o=triple_store_api.perform_sparql_query(query))
        except PermissionError:
            print('403')
            raise HTTPException(status_code=403, detail="Not allowed to run this query")
        except pyparsing.exceptions.ParseException as exc:
            print('400')
            error_msg = f'Not able to parse this query: {exc}'
            raise HTTPException(status_code=400, detail=error_msg)
        return result


class Format(str, Enum):
    ttl = 'ttl'
    turtle = 'turtle'
    json = 'json'
    jsonld = 'jsonld'


@app.get("/opstelling/wegsegment", response_class=Response)
async def get_opstelling_by_wegsegment(wegsegment_id: str, format: Format = Format.ttl):
    start = time.time()
    triples = triple_store_api.get_opstellingen_by_wegsegment(wegsegment_id)
    end = time.time()
    time_spent = round(end - start, 3)
    print(f'Time to process query: {time_spent}')

    h = await triple_store_api.create_graph_from_triples(triples)

    if format in [Format.json, Format.jsonld]:
        json_content = h.serialize(format='json-ld')
        return ORJSONResponse(json.loads(json_content))
    elif format in [Format.ttl, Format.turtle]:
        ttl_content = h.serialize(format='turtle')
        return Response(ttl_content)


@app.get("/opstelling/bounds", response_class=Response)
async def get_opstelling_by_bounds(lower_lat: float, lower_long: float, upper_lat: float, upper_long: float,
                                   format: Format = Format.ttl):
    start = time.time()
    triples = triple_store_api.get_opstellingen_by_bounds(lower_lat, lower_long, upper_lat, upper_long)
    end = time.time()
    time_spent = round(end - start, 3)
    print(f'Time to process query: {time_spent}')

    h = await triple_store_api.create_graph_from_triples(triples)

    if format in [Format.json, Format.jsonld]:
        json_content = h.serialize(format='json-ld')
        return ORJSONResponse(json.loads(json_content))
    elif format in [Format.ttl, Format.turtle]:
        ttl_content = h.serialize(format='turtle')
        return Response(ttl_content)


@app.get("/opstelling/bounds_sparql", response_class=Response)
async def get_opstelling_by_bounds_sparql(lower_lat: float, lower_long: float, upper_lat: float, upper_long: float,
                                   format: Format = Format.ttl):
    start = time.time()
    triples = triple_store_api.get_opstellingen_by_bounds_by_sparql(lower_lat, lower_long, upper_lat, upper_long)
    end = time.time()
    time_spent = round(end - start, 3)
    print(f'Time to process query: {time_spent}')

    h = await triple_store_api.create_graph_from_triples(triples)

    if format in [Format.json, Format.jsonld]:
        json_content = h.serialize(format='json-ld')
        return ORJSONResponse(json.loads(json_content))
    elif format in [Format.ttl, Format.turtle]:
        ttl_content = h.serialize(format='turtle')
        return Response(ttl_content)


@app.get("/opstelling/{id}", response_class=Response)
async def get_opstelling_by_id(request: Request, format: Format = Format.ttl, id: str = ''):
    start = time.time()
    triples = triple_store_api.get_full_opstelling_triples(id)
    end = time.time()
    time_spent = round(end - start, 3)
    print(f'Time to process query: {time_spent}')

    if 'text/html' in request.headers['accept']:
        html_page = HTMLTemplater.get_opstelling_html(id, triples)
        print(f'Time to process query: {time_spent}')
        html_page = html_page.replace('$time_spent$', str(time_spent))

        return HTMLResponse(content=html_page)
    else:
        h = await triple_store_api.create_graph_from_triples(triples)

        if format in [Format.json, Format.jsonld]:
            json_content = h.serialize(format='json-ld')
            return ORJSONResponse(json.loads(json_content))
        elif format in [Format.ttl, Format.turtle]:
            ttl_content = h.serialize(format='turtle')
            return Response(ttl_content)


@app.get("/opstelling/{asset_id}/visualize", response_class=HTMLResponse)
async def visualize_opstelling_by_id(asset_id: str = ''):
    start = time.time()
    relations_to_use = [URIRef('https://data.vlaanderen.be/ns/mobiliteit#omvatVerkeersbord'),
                        URIRef('https://data.vlaanderen.be/ns/mobiliteit#realiseert'),
                        URIRef('https://data.vlaanderen.be/ns/mobiliteit#heeftVerkeersbordconcept')]
    triples = triple_store_api.get_all_related_triples(
        asset_ref=URIRef('https://apps.mow.vlaanderen.be/verkeersborden/rest/zi/verkeersborden/' + asset_id),
        use_relations=relations_to_use)

    end = time.time()
    time_spent = round(end - start, 3)
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

    html_content = VisualizeD3.html_template_string
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
