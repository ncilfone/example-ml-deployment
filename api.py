from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse, text, JSONResponse

import numpy as np


# DEFINE YOUR MODEL SOMEWHERE -- NOT GOING TO DO IT HERE


async def invocations(request: Request):
    # Probably would want to enforce schema on the way in and out with something like msgspec
    # too much work to implement 

    # so we assume our payload is a simple integer in the body of a json
    # e.g. {'body': 2}

    # Write your model inference logic -- here's a dummy call for posterity
    # If you want to be pedantic this is technically a probabilistic model :-)
    new_value = np.random.normal(request.json['body'])
    return JSONResponse({"fancy_model": new_value})
    pass



async def ping(request: Request) -> HTTPResponse:
    return text("Pong!\n", status=200)
