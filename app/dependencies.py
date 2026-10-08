from fastapi import Request

def get_order_service(request: Request):
    return request.app.state.order_service

def get_trade_service(request: Request):
    return request.app.state.trade_service