from rest_framework.exceptions import APIException


class DomainConflict(APIException):
    status_code = 409
    default_detail = "The requested change conflicts with current application state."
    default_code = "domain_conflict"

