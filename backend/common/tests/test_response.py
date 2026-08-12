from common.response import success_response, error_response
from rest_framework.response import Response

def test_success_response():
    r = success_response({'a': 1})
    assert isinstance(r, Response)
    assert r.data == {'code': 0, 'message': 'success', 'data': {'a': 1}}

def test_error_response():
    r = error_response(1001, 'invalid', status=400)
    assert r.status_code == 400
    assert r.data == {'code': 1001, 'message': 'invalid', 'data': None}
