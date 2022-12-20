import concurrent.futures
import json
import platform
import time
from pathlib import Path

from termcolor import colored

from CreatingData.JsonToVkbFeatureProcessor import JsonToVkbFeatureProcessor
from CreatingData.VkbFeatureToOSLOProcessor import VkbFeatureToOSLOProcessor

if __name__ == '__main__':
    with open(Path('Data/00001.json'), encoding='utf-8') as f:
        data_list = json.load(f)

    features = []

    # use multithreading
    start = time.time()
    to_feature_processor = JsonToVkbFeatureProcessor()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = [executor.submit(to_feature_processor.process_json_object, dict_list=dict_list) for dict_list in data_list]
        for f in concurrent.futures.as_completed(results):
            features.append(f.result())
    end = time.time()
    print(colored(f'Processed to vkb features: {len(features)} in {round(end - start, 2)} seconds', 'green'))

    start = time.time()
    to_oslo_processor = VkbFeatureToOSLOProcessor()
    file_path = Path('vkb_oslo_1000.ttl')
    for feature in features:
        to_oslo_processor.process_to_oslo(feature)
    end = time.time()
    print(colored(f'Processed vkb features to OSLO compliant file in {round(end - start, 2)} seconds', 'green'))

    print(to_oslo_processor.graph.serialize(format='turtle'))
    to_oslo_processor.graph.serialize('vkb_oslo_1000.ttl')
