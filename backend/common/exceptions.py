from rest_framework.views import exception_handler
from rest_framework.response import Response

ERROR_CODES = {
    400: 1001, 401: 1002, 403: 1003, 404: 1004, 500: 5000,
}

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        code = ERROR_CODES.get(response.status_code, 5000)
        if isinstance(response.data, dict) and 'detail' in response.data:
            message = response.data['detail']
        elif isinstance(response.data, dict):
            message = response.data
        else:
            message = str(response.data)
        response.data = {'code': code, 'message': message, 'data': None}
    return response
