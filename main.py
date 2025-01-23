import uvicorn
from fastapi import FastAPI
from fastapi.params import Query, Path

from standard_api_response.standard_response import StandardResponse
from src.service.sample_service import SampleService

app = FastAPI()


@app.get('/item')
async def sample_item():
    def __lambda():
        payload = sample_service.get_item()
        return payload, None, None

    sample_service = SampleService()
    return StandardResponse.build(callback=__lambda)


@app.get('/page_list/{page}')
async def sample_page_list(
    page: int = Path(description='페이지 번호, 0인 경우 모든 데이터 반환', ge=0),
    page_size: int = Query(default=10, description='페이지 당 아이템 수', ge=1),
):
    def __lambda():
        payload = sample_service.get_pageable_list(page, page_size)
        return payload, None, None

    sample_service = SampleService()
    return StandardResponse.build(callback=__lambda)


@app.get('/page_only/{page}')
async def sample_page_only(
    page: int = Path(description='페이지 번호, 0인 경우 모든 데이터 반환', ge=0),
    page_size: int = Query(default=10, description='페이지 당 아이템 수', ge=1),
):
    def __lambda():
        payload = sample_service.get_pageable_only(page, page_size)
        return payload, None, None

    sample_service = SampleService()
    return StandardResponse.build(callback=__lambda)


@app.get('/more_list/{start_index}')
async def sample_incremental_list(
    start_index: int = Path(description='시작 인덱스', ge=0),
    how_many: int = Query(default=10, description='한 번에 가져올 아이템 수', ge=1),
):
    def __lambda():
        payload = sample_service.get_incremental_list(start_index, how_many)
        return payload, None, None

    sample_service = SampleService()
    return StandardResponse.build(callback=__lambda)


@app.get('/more_list_by_key/{start_key}')
async def sample_incremental_by_key_list(
    start_key: str = Path(description='시작 키'),
    how_many: int = Query(default=10, description='한 번에 가져올 아이템 수', ge=1),
):
    def __lambda():
        payload = sample_service.get_incremental_list_by_key(start_key, how_many)
        return payload, None, None

    sample_service = SampleService()
    return StandardResponse.build(callback=__lambda)


if __name__ == '__main__':
    uvicorn.run(
        app="main:app",
        host='127.0.0.1',
        port=5010,
        reload=True,
        reload_dirs=['src', "standard_api_response"],
        loop='asyncio',
    )
