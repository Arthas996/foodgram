from rest_framework.pagination import PageNumberPagination

from constants import PAGE_SIZE, PAGE_SIZE_QUERY_PARAM


class Pagination(PageNumberPagination):
    page_size = PAGE_SIZE
    page_size_query_param = PAGE_SIZE_QUERY_PARAM
