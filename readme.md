# API 표준 응답 라이브러리

이 라이브러리는 API 응답 표준화를 위한 클래스와 메서드를 제공합니다.  
## 기능
* 응답 데이터를 표준화된 response 포맷으로 생성 (데이터 제공 측면)
  * 리스트가 없는 응답 데이터 표준화 구성
  * 페이지네이션 형태 리스트 구성
  * 더보기 형태 리스트 구성
* 응답 데이터로 표준화된 매핑 객체 생성 (데이터 소비 측면)
    * 표준화된 response 포맷을 데이터로 매핑
    * 표준화된 response 포맷을 데이터로 매핑 (페이지네이션 리스트)
    * 표준화된 response 포맷을 데이터로 매핑 (더보기 형태 리스트)

표준 API 스펙은 다음 링크에 정의되어 있습니다.  
휴넷 임직원: https://ihunet.atlassian.net/wiki/spaces/KUDOS/pages/3783786517/API+specification+V1.2  
일반 사용자: https://velog.io/@jogakdal/standard-api-specification

## 설치
```bash
pip install standard-api-response
```
이 프로젝트의 전체 소스 코드를 다운 받으시려면 저장소를 클론하고 필요한 종속성을 설치하십시오:

```sh
git clone https://github.com/jogakdal/standard-api-response.git
cd <repository-directory>
pip install -r requirements.txt
```

## 클래스 설명 - 응답 생성

### `StandardResponse`
표준 API 응답을 구성하는 클래스입니다.
- **속성:**
  - `status` (str): 응답 성공 여부, 'success' 또는 'error'로 지정됩니다.
  - `version` (str): API 버전.
  - `datetime` (datetime): 응답 시각.
  - `duration` (int): 처리 시간 (밀리초).
  - `payload` (generic): 응답 데이터.

- **메서드:**
  - `build(payload=None, callback=None, error_code=None, version=None)`: 
    - 응답 데이터, 에러 코드, API 버전을 이용하여 표준 응답 객체(StandardResponse)를 생성합니다.
    - payload가 None인 경우 callback 함수를 이용하여 payload를 생성합니다.
    - duration 자동 계산을 하려면 callback 함수를 이용하여 payload를 생성해야 합니다.
    - callback 함수는 payload, error_code, version을 반환해야 합니다.
    - callback 함수가 반환한 error_code가 None이 아니면 StandardResponse 객체의 code 필드에 지정됩니다.
    - callback 함수가 반환한 version이 None이 아니면 StandardResponse 객체의 version 필드에 지정됩니다.
    - 이는 페이로드 생성 중 발생할 수 있는 오류 코드를 StandardResponse 객체에 반영하기 위함입니다.
- **사용 예:**
```python
class SamplePayload(BaseModel):
    value_1: str
    value_2: int

@app.get('/item')
async def sample_item():
    def __lambda():
        payload = SamplePayload(value_1='sample', value_2=0)
        return payload, None, None

    return StandardResponse.build(callback=__lambda)
```
  
### `ErrorPayloadItem`
오류 페이로드의 errors 리스트의 오류 아이템을 구성합니다.
- **속성:**
   - `code` (str): 오류 코드.
   - `message` (str): 오류 메시지.
  
### `ErrorPayload`
오류 페이로드를 나타냅니다.
- **속성:**
  - `errors` List[ErrorPayloadItem]: 오류 리스트.
  - `appendix` (Optional[dict]): 추가 정보.
- **메서드:**
  - `add_error(code: str, message: str)`: 
    - 오류 아이템을 추가합니다.
  - `build(code, message, appendix: Optional[dict] = None)`:
    - 단일 오류 아이템으로 오류 페이로드 객체를 생성합니다.
    - `code`: 오류 코드.
    - `message`: 오류 메시지.
    - `appendix`: 추가 정보 (선택 사항).

### `PageableList`
페이지 형태의 리스트 응답을 생성할 때 사용합니다.  
Generic을 이용하여 리스트 아이템의 실제 타입을 지정할 수 있습니다.
- **속성:**
  - `page` (PageInfo): 페이지 정보.
  - `order` (Optional[OrderInfo]): 정렬 정보
  - `items`: (Items[I]): 아이템 정보
- **메서드:**
  - `build(total_items: int, page_size: int, current_page: int, items, order_info: OrderInfo=None)`: 
    - `PageableList` 객체를 생성합니다.
    - 총 아이템 수와 페이지 당 아이템 수를 이용하여 페이지 정보(PageInfo 객체)를 생성합니다.
- **사용 예:**
```python
class SampleItem(BaseModel):
    key: str
    value: int


class SamplePageListPayload(BaseModel):
    value_1: str
    value_2: int
    pageable: PageableList[SampleItem]


class SampleService:
    def __init__(self):
        self.item_list = []
        for i in range(100):
            self.item_list.append(SampleItem(key=f'key_{i}', value=i))

    def get_pageable_list(self, page: int, page_size: int):
        # page == 0 이면 모든 데이터 반환
        if page <= 0:
            page = 1
            page_size = len(self.item_list)

        page_list = PageableList[SampleItem].build(
            items=self.item_list[(page - 1) * page_size : page * page_size],
            total_items=len(self.item_list),
            page_size=page_size,
            current_page=page
        )

        payload = SamplePageListPayload(
            value_1='page_list_sample',
            value_2=0,
            pageable=page_list.model_dump()  # Pydantic에서 custom model에 대한 직렬화를 수행할 때 dict를 사용하므로 dict로 변환
        )
        return payload


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
```

### `IncrementalList`
증분 형식의 리스트 응답을 생성할 때 사용합니다.  
Generic을 이용하여 리스트 아이템의 실타입을 지정할 수 있습니다.
- **속성:**
  - `cursor` (CursorInfo): 커서 정보.
  - `order` (Optional[OrderInfo]): 정렬 정보
  - `items`: (Items[I]): 아이템 정보
- **사용 예:**
```python
class SampleItem(BaseModel):
    key: str
    value: int


class SampleIncrementalListPayload(BaseModel):
    value_1: str
    value_2: int
    incremental: IncrementalList[SampleItem]


class SampleService:
    def __init__(self):
        self.item_list = []
        for i in range(100):
            self.item_list.append(SampleItem(key=f'key_{i}', value=i))

    def get_incremental_list(self, start_index: int, how_many: int):
        item_count = len(self.item_list)

        if start_index >= item_count:
            return SampleIncrementalListPayload(
                value_1='no more item',
                value_2=0,
                incremental=IncrementalList[SampleItem](
                    cursor=CursorInfo(field='sequence', start=start_index, end=None, expandable=False),
                    order=OrderInfo(sorted=True, by=[OrderBy(field='key', direction=OrderDirection.ASC)]).model_dump(),
                    items=Items[SampleItem](total=item_count, current=0, list=[]).model_dump()
                ).model_dump()
            )

        real_fetch_size = min(how_many, item_count - start_index)

        order = OrderInfo(
            sorted=True,
            by=[
                OrderBy(field='key', direction=OrderDirection.ASC),
                OrderBy(field='value', direction=OrderDirection.ASC)
            ]
        )

        items = Items.build(item_count, self.item_list[start_index: start_index + real_fetch_size])

        cursor = CursorInfo.build_from_total(
            start_index=start_index,
            how_many=how_many,
            total_items=item_count,
            field='sequence'
        )

        incremental = IncrementalList[SampleItem](
            cursor=cursor,
            order=order.model_dump(),
            items=items.model_dump()
        )

        return SampleIncrementalListPayload(
            value_1='expandable_list_sample',
            value_2=0,
            incremental=incremental.model_dump()
        )


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
```

### `PageInfo`
페이지 정보를 구성합니다. PageableList의 page 속성을 구성할 때 사용합니다.
- **속성:**
  - `size` (int): 페이지 당 아이템 수
  - `current` (int): 현재 페이지 번호
    `total` (int): 전체 페이지 수
- **메서드:**
  - `calc_total_pages(total_items: int, page_size: int)`: 
      - 전체 아이템 수와 페이지 당 아이템 수를 이용하여 전체 페이지 수를 계산합니다.

#### `CursorInfo`
커서 정보를 구성합니다. IncrementalList의 cursor 속성을 구성할 때 사용합니다.
- **속성:**
  - `field` (Optional[str]): 커서의 기준이 되는 필드 명.
  - `start` (Any): 시작 인덱스 또는 키.
  - `end` (Any): 끝 인덱스 또는 키.
  - `expandable` (Optional[bool]): 다음 아이템 존재 여부.
- **메서드:**
  - `build_from_total(start_index: int, how_many: int, total_items: int, field: str=None, convert_index=lambda field_name, index: index)` 
    - 총 아이템 수와 시작 인덱스, 리턴할 아이템 수를 사용하여 `CursorInfo` 객체를 생성합니다.
    - `start_index`는 실제 커서 기준 필드의 타입과 관계없이 정수형 (리스트의) 인덱스 정보를 전달해야 합니다.
    - 리턴할 커서의 실제 값이 리스트의 인덱스 정보가 아니라면 `convert_index` 콜백 함수를 이용하여 커서 기준 필드의 겂으로 변환해 줄 수 있습니다.
- **사용 예:**
  - `IncrementalList` 클래스의 사용 예를 참조하십시오. 

### `Items`
아이템 정보를 구성합니다.  
PageableList, IncrementalList의 items 속성을 구성할 때 사용합니다.
- **속성:**
  - `total` (Optional[int]): 전체 아이템 수.
  - `current` (Optional[int]): 현재 아이템 수.
  - `list` (list): 아이템 리스트.
- **메서드:**
  - `build(total_items: int, items)`
    - `Items` 객체를 생성합니다.
    - `current`는 `items` 리스트의 실제 size로 지정됩니다.
- **사용 예:**
    - `IncrementalList` 클래스의 사용 예를 참조하십시오.

### `OrderInfo`
정렬 정보를 나타냅니다.  
PageableList, IncrementalList의 order 속성을 구성할 때 사용합니다.
- **속성:**
    - `sorted` (bool): 정렬 여부.
    - `by` (List[OrderBy]): 정렬된 필드. 
- **사용 예:**
    - `IncrementalList` 클래스의 사용 예를 참조하십시오.

### `OrderBy`
정렬된 필드 정보를 나타냅니다.  
OrderInfo의 by 속성을 구성할 때 사용합니다.
- **속성:**
    - `field` (str): 정렬할 필드 명.
    - `direction` (OrderDirection): 정렬 방향. ("ASC": `OrderDirection.ASC`, "DESC": `OrderDirection.DESC`)
- **사용 예:**
    - `IncrementalList` 클래스의 사용 예를 참조하십시오.

### `OrderDirection`
정렬 방향을 지정하는 Enum 클래스입니다.  
OrderBy의 direction 속성을 지정할 때 사용합니다.
- **속성:**
    - `ASC` (str): 오름차순.
    - `DESC` (str): 내림차순.
- **사용 예:**
    - `IncrementalList` 클래스의 사용 예를 참조하십시오.

## 클래스 설명 - 응답 결과 매핑

### `StandardResponseMapper`
표준 API 응답을 대응 객체로 매핑하는 클래스입니다.
기본적으로 클래스 파라미터로 응답 json을 지정하면 해당 json을 파이썬 객체로 변환하여 response 멤버 변수에 저장합니다. 
객체를 생성할 때 payload 타입을 지정하면 response.payload 멤버 변수fmf 해당 타입으로 명시해 줍니다.
- **메서드:**
    - `__init__(response: dict, payload_type: Type[BaseModel]=None)`: 
        - 응답 json과 payload 타입을 이용하여 객체를 생성합니다.
    - `map_payload(response: dict, payload_type: Type[P]) -> Type[P]`: 
        - 응답 json의 payload를 payload_type으로 매핑합니다.
    - `map_list(payload: dict, list_type: Type[P], list_key: str = 'pageable') -> Type[P]`:
      - 전달된 `payload` json의 `list_key` 키에 해당하는 리스트를 `list_type`으로 매핑합니다.
    - `map_pageable_list(payload: dict, item_type: Type[P], list_key: str = 'pageable') -> PageableList[P]`:
      - `map_list` 함수의 PageableList 버전입니다.
    - `map_incremental_list(payload: dict, item_type: Type[P], list_key: str = 'incremental') -> IncrementalList[P]`:
      - `map_list` 함수의 IncrementalList 버전입니다.
    - 'auto_map_list(payload: dict, item_type: Type[P]) -> Dict[str, _BaseList]'
      - `payload`에 있는 list 데이터를 자동으로 변환하여 반환합니다.
      - 현재 PageableList, IncrementalList 두 타입만 지원합니다.
      - `payload`에 한 개 이상의 리스트가 있을 경우, 모든 리스트를 변환하여 {'<키필드 명>: <객체>} 형태로 반환합니다.
- **사용 예:**

```python
@pytest.mark.asyncio
async def test_page_list(start_api_server):
  client = AsyncClient(base_url="http://localhost:5010")

  response = await client.get(
    url=f'/page_list/{1}',
    params={
      "page_size": 5
    }
  )
  assert response.status_code == http.HTTPStatus.OK
  json = response.json()
  assert json['status'] == PayloadStatus.SUCCESS

  mapper = StdResponseMapper(json, SamplePageListPayload)
  assert mapper.response.status == PayloadStatus.SUCCESS
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
```

## 응답 필드 변환
### `ResponseKeyConverter` 클래스
- ResponseKeyConverter 클래스를 사용하면 응답을 생성할 때나 응답을 모델로 매핑할 때 필드명이나 필드명의 케이스 컨벤션을 변환할 수 있습니다.
- 상세 설명은 <a href="https://github.com/jogakdal/convertable-key-model">convertable-key-model 모듈 설명서</a>를 참조하십시오.

## 응답 필드 변환 예제

```python
from pydantic import BaseModel


class SampleItem(BaseModel):
  key: str
  value: int


class SamplePageListPayload(ConvertableKeyModel):
  value_1: str
  value_2: int
  pageable: PageableList[SampleItem]


class SampleService:
  def __init__(self):
    self.item_list = []
    for i in range(100):
      self.item_list.append(SampleItem(key=f'key_{i}', value=i))

  def get_pageable_list(self, page: int, page_size: int):
    # page == 0 이면 모든 데이터 반환
    if page <= 0:
      page = 1
      page_size = len(self.item_list)

    page_list = PageableList[SampleItem].build(
      items=self.item_list[(page - 1) * page_size: page * page_size],
      total_items=len(self.item_list),
      page_size=page_size,
      current_page=page,
      order_info=OrderInfo(sorted=True, by=[OrderBy(field='key', direction=OrderDirection.ASC)]),
    )

    payload = SamplePageListPayload(
      value_1='page_list_sample',
      value_2=0,
      pageable=page_list.convert_key(),  # Pydantic에서 custom model에 대한 직렬화를 수행할 때 dict를 사용하므로 dict로 변환
    )
    return payload


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
  print(json.dumps(response_json, indent=2, ensure_ascii=False))

  ResponseKeyConverter().add_alias(StandardResponse, 'duration', 'duration_time')
  ResponseKeyConverter().add_alias(PageInfo, 'current', 'current_page')
  ResponseKeyConverter().add_alias(PageInfo, 'size', 'page_size')
  ResponseKeyConverter().add_alias(PageInfo, 'total', 'total_pages')
  ResponseKeyConverter().add_alias(OrderInfo, 'by', 'order_by')
  ResponseKeyConverter().add_alias(Items[SampleItem], 'current', 'current_page')
  ResponseKeyConverter().add_alias(PageableList[SampleItem], 'page', 'page_info')
  ResponseKeyConverter().set_default_case_convention(CaseConvention.CAMEL)

  mapper = StdResponseMapper(response_json, SamplePageListPayload)
  assert mapper.response.status == PayloadStatus.SUCCESS
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
```

## 라이선스
이 라이브러리는 누구나 사용할 수 있는 프리 소프트웨어입니다. 다만 코드를 수정할 경우 변경된 내용을 원작성자에게 통보해 주시면 감사하겠습니다.

## 작성자
황용호(jogakdal@gmail.com)
