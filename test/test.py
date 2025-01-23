import http
import json

import pytest
from httpx import AsyncClient

from src.service.sample_service import SamplePageListPayload, SampleIncrementalListPayload, SampleItem, SamplePayload
from standard_api_response.standard_response import PageableList, IncrementalList, Items
from standard_api_response.standard_response_mapper import StdResponseMapper


@pytest.fixture(scope="session", autouse=True)
def start_api_server():
    pass
    # # 서버를 백그라운드에서 실행
    # process = subprocess.Popen(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5010"])
    # process.wait()
    # yield
    # # 테스트가 끝난 후 서버 종료
    # process.terminate()


def async_client():
    return AsyncClient(base_url="http://localhost:5010")

def print_pretty_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


@pytest.mark.asyncio
async def test_sample_item(start_api_server):
    client = async_client()

    response = await client.get('/item')
    assert response.status_code == http.HTTPStatus.OK
    json = response.json()
    assert json['code'] == 200

    # response_object = StdResponseMapper.map_standard_response(json, SamplePayload)
    mapper = StdResponseMapper(json, SamplePayload)
    assert mapper.response.code == 200
    assert isinstance(mapper.response.payload, SamplePayload)
    assert mapper.response.payload.value_1 == 'sample'
    assert mapper.response.payload.value_2 == 0

@pytest.mark.asyncio
async def test_page_list(start_api_server):
    client = async_client()

    response = await client.get(
        url=f'/page_list/{1}',
        params={
            "page_size": 5
        }
    )
    assert response.status_code == http.HTTPStatus.OK
    json = response.json()
    assert json['code'] == 200

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


@pytest.mark.asyncio
async def test_page_only(start_api_server):
    client = async_client()

    response = await client.get(
        url=f'/page_only/{1}',
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
async def test_more_list(start_api_server):
    client = async_client()

    response = await client.get(
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

    # incremental = StdResponseMapper.map_list(response.get('payload'), IncrementalList[SampleItem], 'incremental')
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

    response = await client.get(
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

    response = await client.get(
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
async def test_more_list_by_key(start_api_server):
    client = async_client()

    response = await client.get(
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

    response = await client.get(
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

    response = await client.get(
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
