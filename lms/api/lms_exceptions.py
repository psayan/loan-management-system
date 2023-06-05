from rest_framework import exceptions


class BadRequest(exceptions.APIException):
    status_code = 400
    default_detail = 'Missing parameter'
    default_code = 'bad_request'


class Conflict(exceptions.APIException):
    status_code = 409
    default_detail = 'Conflicts with already existing object.'
    default_code = 'object_exist'
