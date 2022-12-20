import json
import math
from datetime import datetime

from termcolor import colored

from CreatingData.DataHelpers.VkbBevestiging import VkbBevestiging
from CreatingData.DataHelpers.VkbBord import VkbBord
from CreatingData.DataHelpers.VkbFeature import VkbFeature
from CreatingData.DataHelpers.VkbSteun import VkbSteun


class JsonToVkbFeatureProcessor:
    def process_json_object_to_vkb_features(self, json_list: [str]) -> [VkbFeature]:
        return_list = []
        for json_str in json_list:
            try:
                json_str = json_str.replace(r'\xc3\x98', '(diam)')
                dict_list = json.loads(json_str.replace('\n', ''))
                vkb_feature = self.process_json_object(dict_list)
                if vkb_feature is not None:
                    return_list.append(vkb_feature)
            except json.decoder.JSONDecodeError as ex:
                print(ex.args[0])
                if 'Invalid \escape' in ex.args[0]:
                    index_str = ex.args[0].replace('Invalid \escape: line 1 column ', '').split(' ')[0]
                    index = int(index_str)
                    problem_str = json_str[index - 20:index + 50]
                    print(problem_str)

        return return_list

    def process_json_object_and_add_to_list(self, dict_list: dict, features: list) -> None:
        features.append(self.process_json_object(dict_list))

    def process_json_object(self, dict_list: dict) -> VkbFeature:
        vkb_feature = VkbFeature()
        vkb_feature.id = dict_list['properties']['id']

        # if vkb_feature.id != 1001003:
        #     return None

        if 'externalId' in dict_list['properties']:
            vkb_feature.external_id = dict_list['properties']['externalId']
        vkb_feature.wktPoint = self.FSInputToWktPoint(dict_list['geometry']['coordinates'])
        vkb_feature.coords = dict_list['geometry']['coordinates']
        vkb_feature.beheerder_key = dict_list['properties']['beheerder']['key']
        if 'wegenregisterCode' in dict_list['properties']['beheerder']:
            vkb_feature.beheerder_code = dict_list['properties']['beheerder']['wegenregisterCode']
        vkb_feature.beheerder_naam = dict_list['properties']['beheerder']['naam']
        vkb_feature.borden = []
        vkb_feature.bevestigingen = []
        vkb_feature.steunen = []
        vkb_feature.wegsegment_ids = []

        for aanzicht in dict_list['properties']['aanzichten']:
            aanzicht_hoek = round(aanzicht['hoek'] * 180.0 / math.pi, 1)
            while aanzicht_hoek < 0:
                aanzicht_hoek += 360.0
            if aanzicht_hoek > 360.0:
                aanzicht_hoek = aanzicht_hoek % 360.0
            vkb_feature.wegsegment_ids.append(aanzicht['wegsegmentid'])

            for bord_dict in aanzicht['borden']:
                bord = VkbBord()
                vkb_feature.borden.append(bord)
                bord.id = bord_dict['id']
                bord.aanzicht_hoek = aanzicht_hoek
                if 'externalId' in bord_dict:
                    bord.external_id = bord_dict['externalId']
                if 'clientId' in bord_dict:
                    bord.client_id = bord_dict['clientId']
                bord.bord_code = bord_dict['code']
                bord.parameters = []
                if len(bord_dict['parameters']) > 0:
                    bord.parameters.extend(bord_dict['parameters'])

                if 'folieType' in bord_dict:
                    bord.folie_type = bord_dict['folieType']
                bord.x = bord_dict['x']
                bord.y = bord_dict['y']
                bord.breedte = bord_dict['breedte']
                bord.hoogte = bord_dict['hoogte']
                bord.vorm = bord_dict['vorm']

                if 'datumPlaasting' in bord_dict and bord_dict['datumPlaasting'] != '01/01/1950':
                    bord.plaatsing_datum = datetime.strptime(bord_dict['datumPlaatsing'], '%d/%m/%Y')

                if 'bevestigingsProfielen' not in bord_dict:
                    print( vkb_feature.id)
                    continue

                for beugel_dict in bord_dict['bevestigingsProfielen']:
                    bevestiging = VkbBevestiging()
                    vkb_feature.bevestigingen.append(bevestiging)
                    bevestiging.id = beugel_dict['id']
                    bevestiging.bord_id = bord.id
                    steun_ids = set()
                    for x in beugel_dict['bevestigingen']:
                        if 'ophangingId' in x:
                            steun_ids.add(x['ophangingId'])

                    bevestiging.steun_ids = list(steun_ids)

                    client_ids = list(map(lambda x: x.client_id, vkb_feature.steunen))
                    for steun_dict in beugel_dict['bevestigingen']:
                        if 'ophangingId' not in steun_dict or steun_dict['ophangingId'] in client_ids:
                            continue
                        if not steun_dict['type']['actief']:
                            continue
                        steun = VkbSteun()
                        vkb_feature.steunen.append(steun)
                        steun.client_id = steun_dict['ophangingId']
                        steun.type_key = steun_dict['type']['key']

        for ophanging_dict in dict_list['properties']['ophangingen']:
            # steunen + funderingen
            steun_existing = next((s for s in vkb_feature.steunen if s.client_id == ophanging_dict['clientId']), None)
            if steun_existing is None:
                print(colored(f'steun does not yet exist in feature {vkb_feature.id}', 'red'))
                continue
            steun_existing.id = ophanging_dict['id']
            steun_existing.x = ophanging_dict['x']
            steun_existing.diameter = ophanging_dict['diameter']
            steun_existing.lengte = ophanging_dict['lengte']
            if 'breedte' in ophanging_dict:
                steun_existing.breedte = ophanging_dict['breedte']
            steun_existing.kleur_key = ophanging_dict['kleur']['key']
            steun_existing.sokkel_key = ophanging_dict['sokkelAfmetingen']['key']

        return vkb_feature

    @staticmethod
    def FSInputToWktLineStringZM(FSInput) -> str:
        s = 'LINESTRING ZM ('
        for punt in FSInput:
            for fl in punt:
                s += str(fl) + ' '
            s = s[:-1] + ', '
        s = s[:-2] + ')'
        return s

    @staticmethod
    def FSInputToWktPoint(FSInput) -> str:
        s = ' '.join(list(map(str, FSInput)))
        return f'POINT Z ({s} 0)'
