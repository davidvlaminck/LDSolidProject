import concurrent.futures
import json
import os
import time
from pathlib import Path

from termcolor import colored

from CreatingData.JsonToVkbFeatureProcessor import JsonToVkbFeatureProcessor
from CreatingData.VkbFeatureToOSLOProcessor import VkbFeatureToOSLOProcessor


def load_file_into_graph(file_path, graph):
    with open(file_path, encoding='utf-8') as f:
        data_list = json.load(f)
    features = []

    # use multithreading
    start = time.time()
    to_feature_processor = JsonToVkbFeatureProcessor()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = [executor.submit(to_feature_processor.process_json_object, dict_list=dict_list) for dict_list in
                   data_list]
        for f in concurrent.futures.as_completed(results):
            features.append(f.result())
    end = time.time()
    print(colored(f'Processed to vkb features: {len(features)} in {round(end - start, 2)} seconds', 'green'))

    start = time.time()

    to_oslo_processor = VkbFeatureToOSLOProcessor()
    if graph is None:
        graph = to_oslo_processor.graph
    else:
        to_oslo_processor.graph = graph

    for feature in features:
        to_oslo_processor.process_to_oslo(feature)
    end = time.time()
    print(colored(f'Processed vkb features to graph in {round(end - start, 2)} seconds', 'green'))

    return graph


if __name__ == '__main__':
    graph = None
    directory = Path('Data')
    for filename in os.listdir(directory):
        graph = load_file_into_graph(file_path=os.path.join(directory, filename), graph=graph)
    graph.serialize('vkb_oslo_30k.ttl')
