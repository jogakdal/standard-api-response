import http
from datetime import datetime, timezone
from typing import Type, Dict, Optional

from advanced_python_singleton.singleton import Singleton

from standard_api_response.standard_api_response.standard_response import PageableList, IncrementalList, P
from standard_api_response.standard_api_response.standard_response import _BaseList, StandardResponse


class StdResponseMapper(metaclass=Singleton):
    """
    표준화된 response 데이터를 파싱하여 StandardResponse 객체로 변환하는 Mapper 클래스.
    생성 시 response json 데이터와 해당 응답의 payload 타입을 명시해 주면 변환된 StandardResponse 객체를 제공한다.
    """

    def __init__(self, response: dict, payload_type: Type[P]):
        self.response_json = response
        self.payload_type = payload_type
        self.response = StdResponseMapper.map_standard_response(response, payload_type)

    # payload를 model로 변환
    # response: 표준화된 response 데이터(jsosn)
    # payload_type: 변환할 model 타입(class 명)
    @staticmethod
    def map_payload(response: dict, payload_type: Type[P], payload_key: str='payload') -> Type[P]:
        payload = response.get(payload_key) if response is not None else None
        return payload_type.model_validate(payload) if payload is not None else None


    # payload에 있는 list 데이터를 model로 변환
    # payload: 변환할 payload 데이터(json)
    # list_type: 변환할 model 타입(현재 PageableList, IncrementalList 두 타입만 지원)
    # list_key: list 데이터가 있는 key 값(기본갑: 'pageable')
    @staticmethod
    def map_list(payload: dict, list_type: Type[P], list_key: str='pageable') -> Optional[P]:
        if payload is None:
            return None

        return list_type.model_validate(payload.get(list_key, {}))

    @staticmethod
    def map_pageable_list(payload: dict, item_type: Type[P], list_key: str='pageable') -> PageableList[P]:
        return StdResponseMapper.map_list(payload, PageableList[item_type], list_key)

    @staticmethod
    def map_incremental_list(payload: dict, item_type: Type[P], list_key: str='incremental') -> IncrementalList[P]:
        return StdResponseMapper.map_list(payload, IncrementalList[item_type], list_key)


    # payload에 있는 list 데이터를 자동으로 변환
    # payload: 변환할 payload 데이터(json)
    # { '리스트 타입 키': 리스트 객체 } 형태의 dict 반환
    # 현재 PageableList, IncrementalList 두 타입만 지원
    # 리스트 타입 데이터가 없는 경우 빈 dict를 리턴하며 2개 이상인 경우는 모두 결과 dict에 포함하여 리턴
    @staticmethod
    def auto_map_list(payload: dict, item_type: Type[P]) -> Dict[str, _BaseList]:
        def check_type(value, list_type):
            try:
                return list_type.model_validate(value)
            except Exception:
                return None

        if payload is None:
            return {}

        validated_lists = {}
        for key, value in payload.items():
            validated = check_type(value, PageableList[item_type])
            if validated is None:
                validated = check_type(value, IncrementalList[item_type])
            if validated is not None:
                validated_lists[key] = validated

        return validated_lists


    # 표준화된 response 데이터를 StandardResponse 객체로 변환
    @staticmethod
    def map_standard_response(json: dict, payload_type: Type[P]) -> StandardResponse:
        return StandardResponse(
            code=json.get('code', http.HTTPStatus.OK),
            version=json.get('version', '1.0'),
            datetime=json.get('datetime', datetime.now(tz=timezone.utc)),
            duration=json.get('duration', 0),
            payload=StdResponseMapper.map_payload(json, payload_type)
        )
