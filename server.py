from sanic import Sanic
from sanic.worker.loader import AppLoader
from sanic.worker.manager import WorkerManager
from functools import partial
from info import ServerInfo
from api import invocations, ping


## THIS WOULD RUN YOUR SANIC SERVER - NOT COMPLETE WORKING CODE

def create_app() -> Sanic:

    app = Sanic()

    app.add_route(
        invocations,
        "/invocations",
        methods=["POST"]
    )
    app.add_route(
        ping,
        "/ping",
        methods=["GET"]
    )
    return app


def run(server_info):
    loader = AppLoader(
        factory=partial(
            create_app
        )
    )
    primary = loader.load()
    primary.prepare(
        host=server_info.host,
        port=server_info.port,
        dev=server_info.dev,
        workers=server_info.n_workers,
        access_log=server_info.dev
    )
    Sanic.serve(primary=primary, app_loader=loader)


if __name__ == "__main__":
    run()