import http
import json

import pytest
from convertable_key_model import ConvertableKeyModel, CaseConvention, ResponseKeyConverter
from starlette.testclient import TestClient

from src.service.sample_service import SampleService, SampleItem, SamplePageListPayload, SamplePayload, \
    SampleIncrementalListPayload
from standard_api_response.standard_response import StandardResponse, PageInfo, OrderInfo, Items, \
    PageableList, IncrementalList
from standard_api_response.standard_response_mapper import StdResponseMapper
from sample_main import sample_app

client = TestClient(sample_app)

def print_pretty_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


class SampleClass(ConvertableKeyModel):
    some_value_1: str
    someValue2: int

class SampleHaveConvertableKeyModel(ConvertableKeyModel):
    field_one: str
    ckm_field: SampleClass


class SampleClass2(ConvertableKeyModel):
    valueOne: str  # camelCase 필드
    ValueTwo: int  # PascalCase 필드
    value_three: bool  # snake_case 필드


def test_nested_convertable_mapping():
    class SampleAliasClass(ConvertableKeyModel):
        some_field_1: str
        someValue2: int

    class SampleClassWithReverseAliasMap(SampleClass):
        __alias_map_reference__ = {"some_value_1": "some_field_1"}

    class SampleHaveAliasConvertableKeyModel(ConvertableKeyModel):
        field_one: str
        ckm_field: SampleAliasClass

    class SampleHaveReverseAlistMapKeyModel(ConvertableKeyModel):
        field_one: str
        ckm_field: SampleClassWithReverseAliasMap

    def __lambda():
        payload = SampleHaveConvertableKeyModel(
            field_one='sample_field_1',
            ckm_field=SampleClassWithReverseAliasMap(
                some_value_1='sample',
                someValue2=0,
                alias_map={"some_value_1": "some_field_1"},
                case_convention=CaseConvention.CAMEL
            )
        )
        return payload, None, None

    json = StandardResponse.build(callback=__lambda).convert_key()
    print_pretty_json(json)

    # nested model에서 내부 필드 객체 생성자에 alias_map을 지정한 경우 바깥 쪽 객체 매핑이 불가능하다
    # 이런 경우 매핑된 필드로 구성된 클래스를 정의하고 해당 클래스를 내부 필드 객체를 가지는 별도의 클래스를 정의하여 매핑시켜야 한다.
    mapper = StdResponseMapper(json, SampleHaveAliasConvertableKeyModel)
    assert isinstance(mapper.response.payload, SampleHaveAliasConvertableKeyModel)
    assert mapper.response.payload.ckm_field.some_field_1 == 'sample'

    # 또는 원 클래스에 __alias_map_reference__를 정의해 줄 수 있다.
    json = StandardResponse.build(callback=lambda: (
        SampleHaveReverseAlistMapKeyModel(
            field_one='sample_field_1',
            ckm_field=SampleClassWithReverseAliasMap(
                some_value_1='sample',
                someValue2=0,
                alias_map={"some_value_1": "some_field_1"},
                case_convention=CaseConvention.CAMEL
            )
        ), None, None
    )).convert_key()
    mapper = StdResponseMapper(json, SampleHaveReverseAlistMapKeyModel)

    assert isinstance(mapper.response.payload, SampleHaveReverseAlistMapKeyModel)
    assert mapper.response.payload.ckm_field.some_value_1 == 'sample'


def test_convert_key_map():
    def __lambda():
        payload = SampleHaveConvertableKeyModel(
            field_one='sample_field_1',
            ckm_field=SampleClass(
                some_value_1='sample_value_1',
                someValue2=0
            )
        )
        return payload, None, None

    # SampleClass의 some_value_1 필드를 some_value_1_alias로 매핑
    # ResponseKeyConverter를 사용하면 지정된 클래스가 모델의 어떤 레벨에 있든 매핑된 필드명으로 serialize/deserialize가 가능하다.
    ResponseKeyConverter().add_alias(SampleClass, "some_value_1", "some_value_1_alias")

    response_object = StandardResponse.build(callback=__lambda)
    json = response_object.convert_key()
    print_pretty_json(json)

    mapper = StdResponseMapper(json, SampleHaveConvertableKeyModel)

    assert isinstance(mapper.response.payload, SampleHaveConvertableKeyModel)
    assert mapper.response.payload.ckm_field.some_value_1 == 'sample_value_1'


def test_case_convention_mapping():
    alias_map = {
        "valueOne": "value_one_alias",
        "ValueTwo": "value_two_alias",
    }

    original_data = {
        "value_one": "값1",  # alias_map을 통해 매핑되어야 함
        "valueTwo": 999,  # alias_map과 case 변환 적용
        "ValueThree": True,  # snake_case로 변환하여 매핑
    }

    converted_data = {
        "value_one_alias": "값2",  # alias_map을 통해 매핑되어야 함
        "valueTwoAlias": 999,  # alias_map과 case 변환 적용
        "ValueThree": True,  # snake_case로 변환하여 매핑
    }

    sample = SampleClass2(case_convention=CaseConvention.CAMEL, **original_data)
    print()
    print(f'sample object: {sample}')

    assert sample.valueOne == '값1'  # 객체는 camelCase이고 json 데이터는 snake_case이어도 매핑이 잘 되어야 함
    assert sample.ValueTwo == 999  # 객체는 PascalCase이고 json 데이터는 camelCase이어도 매핑이 잘 되어야 함
    assert sample.value_three  # 객체는 snake_case이고 json 데이터는 PascalCase이어도 매핑이 잘 되어야 함

    dump_data = sample.convert_key()
    print_pretty_json(dump_data)
    assert dump_data['valueTwo'] == 999  # convert_key()에 아무런 인자가 없으면 객체의 case_convention에 따라 변환
    assert dump_data['valueThree']  # convert_key()에 아무런 인자가 없으면 객체의 case_convention에 따라 변환

    dump_data = sample.convert_key(case_convention=CaseConvention.CAMEL)
    print_pretty_json(dump_data)
    assert dump_data['valueTwo'] == 999  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환
    assert dump_data['valueThree']  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환

    dump_data = sample.convert_key(case_convention=CaseConvention.SNAKE)
    print_pretty_json(dump_data)
    assert dump_data['value_one'] == '값1'  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환
    assert dump_data['value_two'] == 999  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환

    dump_data = sample.convert_key(case_convention=CaseConvention.PASCAL)
    print_pretty_json(dump_data)
    assert dump_data['ValueOne'] == '값1'  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환
    assert dump_data['ValueThree']  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환

    # alias_map을 적용하여 매핑될 필드명이 변경되어도 지정된 case convention으로 serialize/deserialize가 가능해야 한다.
    sample2 = SampleClass2(alias_map=alias_map, case_convention=CaseConvention.CAMEL, **converted_data)
    print(f'sample2: {sample2}')
    assert sample2.valueOne == '값2'  # 객체는 camelCase이고 json 데이터는 snake_case이어도 매핑이 잘 되어야 함
    assert sample2.ValueTwo == 999  # 객체는 PascalCase이고 json 데이터는 camelCase이어도 매핑이 잘 되어야 함
    assert sample2.value_three  # 객체는 snake_case이고 json 데이터는 PascalCase이어도 매핑이 잘 되어야 함

    dump_data = sample2.convert_key()
    print('sample2 dump_data with class parameter: ')
    print_pretty_json(dump_data)
    assert dump_data['valueOneAlias'] == '값2'  # convert_key()에 아무런 인자가 없으면 객체의 case_convention에 따라 변환
    assert dump_data['valueTwoAlias'] == 999  # convert_key()에 아무런 인자가 없으면 객체의 case_convention에 따라 변환
    assert dump_data['valueThree']  # convert_key()에 아무런 인자가 없으면 객체의 case_convention에 따라 변환, alias_map에 없는 키는 원 필드명이 변환되어야 함

    dump_data = sample2.convert_key(case_convention=CaseConvention.CAMEL)
    print('sample2 dump_data with convert_key function parameter: ')
    print_pretty_json(dump_data)
    assert dump_data['valueOneAlias'] == '값2'  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환
    assert dump_data['valueTwoAlias'] == 999  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환
    assert dump_data['valueThree']  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환

    dump_data = sample2.convert_key(case_convention=CaseConvention.SNAKE)
    print_pretty_json(dump_data)
    assert dump_data['value_one_alias'] == '값2'  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환
    assert dump_data['value_two_alias'] == 999  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환
    assert dump_data['value_three']  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환

    dump_data = sample2.convert_key(case_convention=CaseConvention.PASCAL)
    print_pretty_json(dump_data)
    assert dump_data['ValueOneAlias'] == '값2'  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환
    assert dump_data['ValueTwoAlias'] == 999  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환
    assert dump_data['ValueThree']  # convert_key()에 case_convention 인자가 있으면 해당 case로 변환


def test_with_StandardResponse_and_StdResponseMapper():
    def __lambda():
        payload = SampleClass(
            some_value_1='sample',
            someValue2=0,
            case_convention=CaseConvention.CAMEL
        )
        return payload, None, None

    json = StandardResponse.build(callback=__lambda).convert_key()
    print_pretty_json(json)

    mapper = StdResponseMapper(json, SampleClass)

    assert isinstance(mapper.response.payload, SampleClass)
    assert mapper.response.payload.some_value_1 == 'sample'

def test_with_standard_response_class():
    def make_temporary_response():
        def __lambda():
            payload = sample_service.get_pageable_list(page=1, page_size=5)
            return payload, None, None

        sample_service = SampleService()

        ResponseKeyConverter().clear()
        ResponseKeyConverter().add_alias(StandardResponse, 'duration', 'duration_time')
        ResponseKeyConverter().add_alias(PageInfo, 'current', 'current_page')
        ResponseKeyConverter().add_alias(PageInfo, 'size', 'page_size')
        ResponseKeyConverter().add_alias(PageInfo, 'total', 'total_pages')
        ResponseKeyConverter().add_alias(OrderInfo, 'by', 'order_by')
        ResponseKeyConverter().add_alias(Items[SampleItem], 'current', 'current_page')
        ResponseKeyConverter().add_alias(PageableList[SampleItem], 'page', 'page_info')
        ResponseKeyConverter().set_default_case_convention(CaseConvention.CAMEL)

        result = StandardResponse.build(callback=__lambda)
        result = result.convert_key()
        ResponseKeyConverter().clear()
        return result

    response_json = make_temporary_response()
    print_pretty_json(response_json)

    ResponseKeyConverter().add_alias(StandardResponse, 'duration', 'duration_time')
    ResponseKeyConverter().add_alias(PageInfo, 'current', 'current_page')
    ResponseKeyConverter().add_alias(PageInfo, 'size', 'page_size')
    ResponseKeyConverter().add_alias(PageInfo, 'total', 'total_pages')
    ResponseKeyConverter().add_alias(OrderInfo, 'by', 'order_by')
    ResponseKeyConverter().add_alias(Items[SampleItem], 'current', 'current_page')
    ResponseKeyConverter().add_alias(PageableList[SampleItem], 'page', 'page_info')
    ResponseKeyConverter().set_default_case_convention(CaseConvention.CAMEL)

    mapper = StdResponseMapper(response_json, SamplePageListPayload)
    assert mapper.response.code == 200
    assert mapper.response.payload.pageable.page.size == 5
    assert isinstance(mapper.response.payload, SamplePageListPayload)
    assert isinstance(mapper.response.payload.pageable, PageableList)
    assert isinstance(mapper.response.payload.pageable.items, Items)
    assert isinstance(mapper.response.payload.pageable.items.list[0], SampleItem)
    assert mapper.response.payload.pageable.page.current == 1
    assert mapper.response.payload.pageable.items.current == 5
    assert len(mapper.response.payload.pageable.items.list) == 5
    assert mapper.response.payload.pageable.items.list[0].key == 'key_0'
    assert mapper.response.payload.pageable.items.list[0].value == 0

    payload = StdResponseMapper.map_payload(response_json, SamplePageListPayload)
    assert isinstance(payload, SamplePageListPayload)
    assert isinstance(payload.pageable, PageableList)
    assert isinstance(payload.pageable.items, Items)
    assert isinstance(payload.pageable.items.list[0], SampleItem)

    # pageable = StdResponseMapper().map_list(json.get('payload'), PageableList[SampleItem], 'pageable')
    pageable = StdResponseMapper.map_pageable_list(response_json.get('payload'), SampleItem, 'pageable')

    assert isinstance(pageable, PageableList)
    assert isinstance(pageable.items, Items)
    assert isinstance(pageable.items.list[0], SampleItem)
    assert pageable.page.size == 5
    assert pageable.page.current == 1
    assert pageable.items.current == 5
    assert len(pageable.items.list) == 5

    lists = StdResponseMapper.auto_map_list(response_json.get('payload'), SampleItem)
    assert len(lists) == 1
    assert isinstance(lists['pageable'], PageableList)
    assert isinstance(lists['pageable'].items, Items)
    assert isinstance(lists['pageable'].items.list[0], SampleItem)

    ResponseKeyConverter().clear()


@pytest.mark.asyncio
async def test_convert_key():
    response = client.get('/key_convert')
    assert response.status_code == http.HTTPStatus.OK
    json = response.json()

    print_pretty_json(json)

    assert json.get('id') is None
    assert json.get('user_id') is None
    assert json.get('userId') == 1
    assert json.get('fullName') == '황용호'
    assert json['profile'].get('userAge') == 30 # Profile 객체에는 age로 정의되어 있으나 alias_map에 의해 userAge로 매핑되어야 함


@pytest.mark.asyncio
async def test_sample_item():
    response = client.get('/item')
    assert response.status_code == http.HTTPStatus.OK
    json = response.json()
    assert json['code'] == 200

    print_pretty_json(json)

    # response_object = StdResponseMapper.map_standard_response(json, SamplePayload)
    mapper = StdResponseMapper(json, SamplePayload)
    assert mapper.response.code == 200
    assert isinstance(mapper.response.payload, SamplePayload)
    assert mapper.response.payload.value_1 == 'sample'
    assert mapper.response.payload.value_2 == 0

@pytest.mark.asyncio
async def test_page_list():
    response = client.get(
        url=f'/page_list/1',
        params={
            "page_size": 5
        }
    )

    assert response.status_code == http.HTTPStatus.OK
    json = response.json()
    assert json['code'] == 200

    print('\ntest_page_list:')
    print_pretty_json(json)

    ResponseKeyConverter().add_alias(StandardResponse, 'duration', 'duration_time')
    ResponseKeyConverter().add_alias(PageInfo, 'current', 'current_page')
    ResponseKeyConverter().add_alias(PageInfo, 'size', 'page_size')
    ResponseKeyConverter().add_alias(PageInfo, 'total', 'total_pages')
    ResponseKeyConverter().add_alias(OrderInfo, 'by', 'order_by')
    ResponseKeyConverter().add_alias(Items[SampleItem], 'current', 'current_page')
    ResponseKeyConverter().add_alias(PageableList[SampleItem], 'page', 'page_info')
    ResponseKeyConverter().set_default_case_convention(CaseConvention.CAMEL)

    mapper = StdResponseMapper(json, SamplePageListPayload)
    assert mapper.response.code == 200
    assert mapper.response.payload.pageable.page.size == 5
    assert isinstance(mapper.response.payload, SamplePageListPayload)
    assert isinstance(mapper.response.payload.pageable, PageableList)
    assert isinstance(mapper.response.payload.pageable.items, Items)
    assert isinstance(mapper.response.payload.pageable.items.list[0], SampleItem)
    assert mapper.response.payload.pageable.page.current == 1
    assert mapper.response.payload.pageable.items.current == 5
    assert len(mapper.response.payload.pageable.items.list) == 5
    assert mapper.response.payload.pageable.items.list[0].key == 'key_0'
    assert mapper.response.payload.pageable.items.list[0].value == 0

    payload = StdResponseMapper.map_payload(json, SamplePageListPayload)
    assert isinstance(payload, SamplePageListPayload)
    assert isinstance(payload.pageable, PageableList)
    assert isinstance(payload.pageable.items, Items)
    assert isinstance(payload.pageable.items.list[0], SampleItem)

    # pageable = StdResponseMapper().map_list(json.get('payload'), PageableList[SampleItem], 'pageable')
    pageable = StdResponseMapper.map_pageable_list(json.get('payload'), SampleItem, 'pageable')

    assert isinstance(pageable, PageableList)
    assert isinstance(pageable.items, Items)
    assert isinstance(pageable.items.list[0], SampleItem)
    assert pageable.page.size == 5
    assert pageable.page.current == 1
    assert pageable.items.current == 5
    assert len(pageable.items.list) == 5

    lists = StdResponseMapper.auto_map_list(json.get('payload'), SampleItem)
    assert len(lists) == 1
    assert isinstance(lists['pageable'], PageableList)
    assert isinstance(lists['pageable'].items, Items)
    assert isinstance(lists['pageable'].items.list[0], SampleItem)

    ResponseKeyConverter().clear()


@pytest.mark.asyncio
async def test_page_only():
    response = client.get(
        url=f'/page_only/1',
        params={
            "page_size": 5
        }
    )

    assert response.status_code == http.HTTPStatus.OK
    json = response.json()
    assert json['code'] == 200

    mapper = StdResponseMapper(json, PageableList[SampleItem])
    assert mapper.response.code == 200
    assert isinstance(mapper.response.payload, PageableList)
    assert isinstance(mapper.response.payload.items, Items)
    assert isinstance(mapper.response.payload.items.list[0], SampleItem)
    assert mapper.response.payload.page.size == 5
    assert mapper.response.payload.page.current == 1
    assert mapper.response.payload.items.current == 5
    assert len(mapper.response.payload.items.list) == 5
    assert mapper.response.payload.items.list[0].key == 'key_0'
    assert mapper.response.payload.items.list[0].value == 0


@pytest.mark.asyncio
async def test_more_list():
    response = client.get(
        url=f'/more_list/0',
        params={
            "how_many": 5
        }
    )

    assert response.status_code == http.HTTPStatus.OK
    json = response.json()
    assert json['code'] == 200

    # response_object = StdResponseMapper.map_standard_response(json, SampleIncrementalListPayload)
    mapper = StdResponseMapper(json, SampleIncrementalListPayload)
    assert mapper.response.code == 200
    assert isinstance(mapper.response.payload, SampleIncrementalListPayload)
    assert isinstance(mapper.response.payload.incremental, IncrementalList)
    assert isinstance(mapper.response.payload.incremental.items, Items)
    assert isinstance(mapper.response.payload.incremental.items.list[0], SampleItem)
    assert mapper.response.payload.incremental.cursor.start == 0
    assert mapper.response.payload.incremental.cursor.end == 4
    assert mapper.response.payload.incremental.items.current == 5
    assert len(mapper.response.payload.incremental.items.list) == 5

    payload = StdResponseMapper.map_payload(json, SampleIncrementalListPayload)
    assert isinstance(payload, SampleIncrementalListPayload)
    assert isinstance(payload.incremental, IncrementalList)
    assert isinstance(payload.incremental.items, Items)
    assert isinstance(payload.incremental.items.list[0], SampleItem)

    # incremental = StdResponseMapper.map_list(json.get('payload'), IncrementalList[SampleItem], 'incremental')
    incremental = StdResponseMapper.map_incremental_list(json.get('payload'), SampleItem, 'incremental')
    assert isinstance(incremental, IncrementalList)
    assert isinstance(incremental.items, Items)
    assert isinstance(incremental.items.list[0], SampleItem)
    assert incremental.cursor.start == 0
    assert incremental.cursor.end == 4
    assert incremental.cursor.expandable == True
    assert incremental.items.current == 5
    assert len(incremental.items.list) == 5

    lists = StdResponseMapper.auto_map_list(json.get('payload'), SampleItem)
    assert len(lists) == 1
    assert isinstance(lists['incremental'], IncrementalList)
    assert isinstance(lists['incremental'].items, Items)
    assert isinstance(lists['incremental'].items.list[0], SampleItem)

    response = client.get(
        url=f'/more_list/97',
        params={
            "how_many": 5
        }
    )
    assert response.status_code == http.HTTPStatus.OK
    json = response.json()
    assert json['code'] == 200

    # json 직접 조회도 당연히 가능
    assert json['payload']['incremental']['cursor']['start'] == 97
    assert json['payload']['incremental']['cursor']['end'] == 99
    assert json['payload']['incremental']['cursor']['expandable'] == False
    assert json['payload']['incremental']['items']['current'] == 3
    assert len(json['payload']['incremental']['items']['list']) == 3

    response = client.get(
        url=f'/more_list/100',
        params={
            "how_many": 5
        }
    )
    assert response.status_code == http.HTTPStatus.OK
    json = response.json()
    assert json['code'] == 200

    response_object = StdResponseMapper.map_standard_response(json, SampleIncrementalListPayload)
    assert response_object.code == 200
    assert response_object.payload.incremental.cursor.start == 100
    assert response_object.payload.incremental.cursor.end == None
    assert response_object.payload.incremental.cursor.expandable == False
    assert response_object.payload.incremental.items.current == 0
    assert response_object.payload.incremental.items.total == 100
    assert len(response_object.payload.incremental.items.list) == 0


@pytest.mark.asyncio
async def test_more_list_by_key():
    response = client.get(
        url=f'/more_list_by_key/key_40',
        params={
            "how_many": 5
        }
    )
    assert response.status_code == http.HTTPStatus.OK
    json = response.json()

    response_object = StdResponseMapper.map_standard_response(json, SampleIncrementalListPayload)
    assert response_object.code == 200
    assert isinstance(response_object.payload, SampleIncrementalListPayload)
    assert isinstance(response_object.payload.incremental, IncrementalList)
    assert isinstance(response_object.payload.incremental.items, Items)
    assert isinstance(response_object.payload.incremental.items.list[0], SampleItem)
    assert response_object.payload.incremental.cursor.start == 'key_40'
    assert response_object.payload.incremental.cursor.end == 'key_44'
    assert response_object.payload.incremental.items.current == 5
    assert len(response_object.payload.incremental.items.list) == 5

    # print_pretty_json(json)

    response = client.get(
        url=f'/more_list_by_key/key_97',
        params={
            "how_many": 5
        }
    )
    assert response.status_code == http.HTTPStatus.OK
    json = response.json()

    payload = StdResponseMapper.map_payload(json, SampleIncrementalListPayload)
    assert isinstance(payload, SampleIncrementalListPayload)
    assert isinstance(payload.incremental, IncrementalList)
    assert isinstance(payload.incremental.items, Items)
    assert isinstance(payload.incremental.items.list[0], SampleItem)

    assert payload.incremental.cursor.start == 'key_97'
    assert payload.incremental.cursor.end == 'key_99'
    assert payload.incremental.cursor.expandable == False
    assert payload.incremental.items.current == 3
    assert len(payload.incremental.items.list) == 3

    response = client.get(
        url=f'/more_list_by_key/key_100',
        params={
            "how_many": 5
        }
    )
    assert response.status_code == http.HTTPStatus.OK
    json = response.json()
    assert json['code'] == 200

    lists = StdResponseMapper.auto_map_list(json.get('payload'), SampleItem)
    assert len(lists) == 1
    assert isinstance(lists['incremental'], IncrementalList)
    assert isinstance(lists['incremental'].items, Items)

    assert lists['incremental'].cursor.start == 'key_100'
    assert lists['incremental'].cursor.end == None
    assert lists['incremental'].cursor.expandable == False
    assert lists['incremental'].items.current == 0
    assert len(lists['incremental'].items.list) == 0
