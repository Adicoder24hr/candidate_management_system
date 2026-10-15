from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # Call DRF's default exception handler first to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            "error": {
                "code": "validation_error" if response.status_code in [400, 422] else "client_error",
                "message": "Validation failed" if response.status_code in [400, 422] else "An error occurred",
                "fields": response.data if isinstance(response.data, dict) else {"non_field_errors": response.data}
            }
        }
        
        # If detail string exists, surface it as message
        if isinstance(response.data, dict) and "detail" in response.data:
            custom_data["error"]["message"] = str(response.data["detail"])
            if response.status_code == 404:
                custom_data["error"]["code"] = "not_found"
            elif response.status_code == 409:
                custom_data["error"]["code"] = "conflict"
            elif response.status_code == 429:
                custom_data["error"]["code"] = "rate_limited"

        response.data = custom_data
        return response

    # Unhandled server exception -> 500 without stack trace
    logger.exception("Unhandled server exception: %s", exc)
    return Response(
        {
            "error": {
                "code": "internal_error",
                "message": "Something went wrong on the server. Please try again.",
                "fields": {}
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
