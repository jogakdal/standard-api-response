from __future__ import annotations

import http
from datetime import datetime, timezone
from enum import Enum
from typing import TypeVar, Optional, Generic, Any, Union, List

from pydantic import BaseModel, ValidationError

from convertable_key_model.convertable_key_model.convertable_key_model import ConvertableKeyModel
from standard_api_response.standard_api_response.exception import KeyNotFoundError
from standard_api_response.standard_api_response.time_utility import time_diff

P = TypeVar('P', bound=BaseModel)
I = TypeVar('I', bound=BaseModel)


class OrderDirection(Enum):
    """
    정렬 방향.
    payload.{pageable|incremental}.order.by.direction 필드의 값으로 사용.
    코드 상으로는 OrderBy.direction 필드에 사용.
    """

    ASC = 'asc'
    DESC = 'desc'

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        return super().__eq__(other)

    def __str__(self):
        return self.value

    @staticmethod
    def from_string(text):
        for name, member in OrderDirection.__members__.items():
            if text.lower() == member.value.lower():
                return OrderDirection[name]

        return OrderDirection.ASC

class OrderBy(ConvertableKeyModel):
    """
    정렬에 사용된 필드와 방향 정보.
    payload.{pageable|incremental}.order.by 필드 대응 객체
    """

    field: str  # 정렬 필드
    direction: OrderDirection = OrderDirection.ASC  # 정렬 방향 (asc, desc)


class OrderInfo(ConvertableKeyModel):
    """
    순서 정보.
    payload.{pageable|incremental}.order 필드 대응 객체
    """

    sorted: bool  # 정렬 여부
    by: List[OrderBy]  # 정렬이 적용된 필드와 방향 정보


class PageInfo(ConvertableKeyModel):
    """
    페이지 정보.
    payload.pageable.page 필드 대응 객체
    """

    size: int  # 페이지 당 아이템 수
    current: int  # 현재 페이지 번호
    total: int  # 전체 페이지 수

    # 전체 아이템 수와 페이지 당 아이템 수를 이용하여 전체 페이지 수를 계산
    @staticmethod
    def calc_total_pages(total_items: int, page_size: int) -> int:
        return ((total_items + page_size - 1) // page_size) if page_size > 0 else total_items


class Items(ConvertableKeyModel, Generic[I]):
    """
    아이템 정보
    payload.{pageable|incremental}.items 필드 대응 객체
    """

    total: Optional[int] = None  # 전체 아이템 수
    current: Optional[int] = None  # 현재 아이템 수
    list: List[I] # 아이템 리스트

    # 전체 아이템 수와 현재 아이템 리스트를 이용하여 Items 객체 생성. current는 전달된 items 리스트 길이로 설정된다.
    @staticmethod
    def build(total_items: int, items: List[I]) -> 'Items[I]':
        return Items(
            total=total_items,
            current=len(items),
            list=items
        )


class _BaseList(ConvertableKeyModel, Generic[I]):
    """
    PageableList, IncrementalList에서 공통으로 사용하는 필드를 정의한 추상 클래스
    라이브러리 외부에서 직접 사용할 필요가 없다.
    """

    order: Optional[OrderInfo] = None  # 정렬 정보
    items: Items[I]  # 아이템 정보


class PageableList(_BaseList, Generic[I]):
    """
    페이지 형식의 리스트 응답을 생성할 때 사용
    payload.pageable 필드 대응 객체
    """

    page: PageInfo  # 페이지 정보


    # 전체 아이템 수, 페이지 당 아이템 수, 현재 페이지 번호, 아이템 리스트, 정렬 정보를 이용하여 PageableList 객체 생성
    # page_size가 0 이하인 경우 1로 변환
    # page, items 정보는 자동 생성
    @staticmethod
    def build(
            items: List[I],
            total_items: int,
            page_size: int,
            current_page: int,
            order_info: OrderInfo=None
    ) -> 'PageableList[I]':
        _page_size = page_size if page_size > 0 else 1

        result = PageableList[I](
            page=PageInfo(
                size=_page_size,
                current=current_page,
                total=PageInfo.calc_total_pages(total_items, _page_size)
            ),
            order=order_info,
            items=Items.build(total_items=total_items, items=items)
        )
        return result


class CursorInfo(ConvertableKeyModel):
    """
    커서 정보
    payload.incremental.cursor 필드 대응 객체
    """

    field: Optional[str] = None  # 기준 필드(optional)
    start: Any = None  # 시작 인덱스 또는 키, 타입 무관
    end: Any = None  # 끝 인덱스 또는 키, 타입 무관
    expandable: Optional[bool] = None  # 다음 아이템 존재 여부(optional)

    # 전체 아이템 수, 시작 인덱스, 한 번에 가져올 아이템 수, 기준 필드, 인덱스 변환 함수를 이용하여 CursorInfo 객체 생성
    # 기본적으로 이 빌더는 특정 리스트의 순차 인덱스를 기준으로 커서를 생성한다. 순차 인덱스에 해당하는 실제 필드 값을 변환하기 위해 convert_index 콜백 함수를 사용한다.
    # convert_index 함수:
    #   필드 명과 인덱스 값으로 실제 커서로 사용되는 값으로 변환하는 함수
    @staticmethod
    def build_from_total(
            start_index: int,
            how_many: int,
            total_items: int,
            field: str=None,
            convert_index=lambda field_name, index : index
    ):
        if start_index < 0: start_index = 0
        if how_many < 1: how_many = 1

        if total_items <= 0 or start_index >= total_items:
            return CursorInfo(
                field=field,
                start=convert_index(field, total_items),
                end=convert_index(field, total_items),
                expandable=False
            )
        else:
            real_fetch_size = min(how_many, total_items - start_index)
            return CursorInfo(
                field=field,
                start=convert_index(field, start_index),
                end=convert_index(field, start_index + real_fetch_size - (1 if real_fetch_size > 0 else 0)),
                expandable=start_index + how_many < total_items
            )


class IncrementalList(_BaseList, Generic[I]):
    """
    증분 형식의 리스트 응답을 생성할 때 사용
    payload.incremental 필드 대응 객체
    """

    cursor: CursorInfo

    @staticmethod
    def build(items: List[I], start_index, how_many, total_items, cursor_field=None, order_info: OrderInfo=None,
              convert_index=lambda field_name, index : index) -> 'IncrementalList[I]':
        return IncrementalList[I](
            cursor=CursorInfo.build_from_total(
                start_index=start_index,
                how_many=how_many,
                total_items=total_items,
                field=cursor_field,
                convert_index=convert_index
            ),
            order=order_info,
            items=Items.build(total_items=total_items, items=items)
        )


class ErrorPayload(ConvertableKeyModel):
    message: str  # 에러 메시지
    appendix: Optional[dict] = {}  # 추가 정보


class StandardResponse(ConvertableKeyModel):
    """
    표준 응답 객체
    """

    code: int  # 응답 코드
    version: str  # API 버전
    datetime: datetime  # 응답 시각
    duration: Union[int, float]  # 처리 시간 (ms)
    payload: P  # 응답 데이터

    # 응답 데이터, 에러 코드, API 버전을 이용하여 표준 응답 객체 생성
    # payload가 None인 경우 callback 함수를 이용하여 payload를 생성
    # duration 자동 계산을 하려면 callback 함수를 이용하여 payload를 생성해야 한다.
    # callback 함수는 payload, error_code, version을 반환해야 한다.
    # callback 함수가 반환한 error_code가 None이 아니면 StandardResponse 객체의 code 필드에 지정된다.
    # callback 함수가 반환한 version이 None이 아니면 StandardResponse 객체의 version 필드에 지정된다.
    # 이는 페이로드 생성 중 발생할 수 있는 오류 코드를 StandardResponse 객체에 반영하기 위함이다.
    @staticmethod
    def build(payload=None, callback=None, error_code=None, version=None) -> StandardResponse:
        _create_time = datetime.now(tz=timezone.utc)

        try:
            if payload is None:
                if callable(callback):
                    payload, _error_code, _version = callback()
                    if _error_code is not None:
                        error_code = _error_code
                    if _version is not None:
                        version = _version

            _response_time = datetime.now(tz=timezone.utc)

            return StandardResponse(
                code=http.HTTPStatus.OK if error_code is None else error_code,
                version='1.0' if version is None else version,
                datetime=_response_time,
                duration=time_diff(_create_time, _response_time),
                payload=payload
            )
        except ValidationError as e:
            raise ValidationError(f'Validation Error: {e}')
        except KeyNotFoundError as e:
            raise KeyNotFoundError(f'Key is not found: {e}')

    @staticmethod
    def build_from_response(response: dict) -> StandardResponse:
        try:
            return StandardResponse(
                code=response.get('code', http.HTTPStatus.OK),
                version=response.get('version', '1.0'),
                datetime=response.get('datetime', datetime.now(tz=timezone.utc)),
                duration=response.get('duration', 0),
                payload=response.get('payload')
            )
        except ValidationError as e:
            raise ValidationError(f'Validation Error: {e}')
        except KeyNotFoundError as e:
            raise KeyNotFoundError(f'Key is not found: {e}')
