from flask import request
from flask import current_app as app


def authenticated() -> bool:

    """
    Check authentication details
    :return:
    """

    if not request.authorization:
        return False

    if request.authorization.username != app.config["BASIC_AUTH_USERNAME"]:
        return False

    if request.authorization.password != app.config["BASIC_AUTH_PASSWORD"]:
        return False

    return True

