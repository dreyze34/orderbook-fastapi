from fastapi import Request

def get_order_service(request: Request):
    return request.app.state.order_service