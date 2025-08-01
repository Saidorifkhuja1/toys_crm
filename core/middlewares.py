from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest


class LoggingMiddleware(MiddlewareMixin):
    def process_request(self, request: HttpRequest):
        print(f"Request Method: {request.method}")
        print(f"Request Headers: {request.headers}")
        print(f"Request Cookies: {request.COOKIES}")

        # Only log body for known safe types
        content_type = request.headers.get("Content-Type", "")
        if content_type.startswith("application/json"):
            try:
                print(f"Request Body: {request.body.decode('utf-8')}")
            except UnicodeDecodeError:
                print("Request Body: [Binary data, cannot decode]")
        elif request.method in ["POST", "PUT", "PATCH"]:
            print("Request Body: [Non-text body, not displayed]")
