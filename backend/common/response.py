from rest_framework.response import Response

def success_response(data=None, message='success'):
    return Response({'code': 0, 'message': message, 'data': data})

def error_response(code, message, status=400, data=None):
    return Response({'code': code, 'message': message, 'data': data}, status=status)
