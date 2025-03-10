import uvicorn
from fastapi import FastAPI
from fastapi.params import Query, Path

from convertable_key_model.convertable_key_model import ConvertableKeyModel
from convertable_key_model.convertable_key_model.convertable_key_model import to_camel, CaseConvention, \
    ResponseKeyConverter
from src.service.sample_service import SampleService, SampleItem
from standard_api_response.standard_api_response import StandardResponse, PageInfo, OrderInfo, Items, PageableList

app = FastAPI()

class Profile(ConvertableKeyModel):
    age: int

class User(ConvertableKeyModel):
    id: int
    name: str
    email: str
    profile: Profile

@app.get("/key_convert")
def get_user():
    alias_map = {
        "id": "user_id",
        "age": "user_age",
        "name": "full_name"
    }
    return User(
        id=1,
        name="황용호",
        email="jogakdal@gmail.com",
        profile=Profile(age=30, alias_map={"age": "user_age"}, case_converter=to_camel),
        alias_map=alias_map,
        # case_converter=to_camel  # 컨버터 함수를 직접 지정할 수도 있음
        case_convention=CaseConvention.CAMEL
    ).convert_key()

@app.get('/item')
async def sample_item():
    def __lambda():
        payload = sample_service.get_item()
        return payload, None, None

    sample_service = SampleService()
    result = StandardResponse.build(callback=__lambda).convert_key()
    return result


@app.get('/page_list/{page}')
async def sample_page_list(
    page: int = Path(description='페이지 번호, 0인 경우 모든 데이터 반환', ge=0),
    page_size: int = Query(default=10, description='페이지 당 아이템 수', ge=1),
):
    def __lambda():
        payload = sample_service.get_pageable_list(page, page_size)
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

    result = StandardResponse.build(callback=__lambda).convert_key()
    ResponseKeyConverter().clear()

    return result


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
