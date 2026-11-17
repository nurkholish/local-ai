from fastapi import Request


def get_use_case(request: Request):
    return request.app.state.use_case