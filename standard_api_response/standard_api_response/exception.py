class KeyNotFoundError(Exception):
    """ Exception raised when a key is not found in the database """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ErrorPayloadError(Exception):
    def __init__(self, message="Not Found", additional_info:dict=None):
        if additional_info is None:
            additional_info = {}
        self.message = message # 메시지
        self.additional_info: dict = additional_info  # 추가 정보
        super().__init__(self.message)

class DataNotFoundError(ErrorPayloadError):
    def __init__(self, message="Data Not Found", additional_info:dict=None):
        super().__init__(message, additional_info)
        if additional_info is None:
            additional_info = {}


class DataModifyError(ErrorPayloadError):
    def __init__(self, message="Data Modify Error", additional_info:dict=None):
        super().__init__(message, additional_info)
        if additional_info is None:
            additional_info = {}