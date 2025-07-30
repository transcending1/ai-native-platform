from rest_framework.views import exception_handler
from rest_framework.response import Response


# TODO:制定自己的异常处理器,每个异常映射成对应的 error code


def global_exception_handler(exc, context):
    response = exception_handler(exc, context)  # Get the response from DRF.

    # If the response is None, it means that exception is not managed by DRF.
    # We can handle it ourselves, or leave it to Django to handle.
    if response is None:
        return Response({"error": str(exc)}, status=500)

    # If the response is not None, it means it's managed by DRF.
    # We can add some customized process here.
    return response
