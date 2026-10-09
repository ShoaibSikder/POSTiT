from rest_framework.response import Response


def success_response(data, *, status=200):
    return Response(data, status=status)
