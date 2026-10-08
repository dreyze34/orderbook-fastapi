from fastapi import Request

def get_orderbooks(request: Request):
    return request.app.state.orderbooks