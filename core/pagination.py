from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class GlobalPagination(PageNumberPagination):
    page_size = 6
    page_query_param = "page"
    # page_size_query_param = 'page_size'   # if you want to allow clients to override page_size
    invalid_page_message = "Invalid page number."
    invalid_page_message_format = (
        "Invalid page number. Must be between 1 and {max_page_size}."
    )

    def get_page_number(self, request, paginator):
        # grab the raw query-param
        raw_page = request.query_params.get(self.page_query_param)
        # if it's missing or empty, default to '1'
        if not raw_page:
            return 1
        # otherwise defer to the built-in validation (it will convert to int, enforce bounds, etc.)
        return super().get_page_number(request, paginator)

    def get_paginated_response(self, data):
        """
        Returns a Response with the standard pagination keys plus
        'total_pages', computed from the paginator.
        """
        return Response(
            {
                "count": len(data),
                # "next": self.get_next_link(),
                # "previous": self.get_previous_link(),
                "total_pages": self.page.paginator.num_pages,
                "results": data,
            }
        )
