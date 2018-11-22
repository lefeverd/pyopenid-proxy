import logging
import yaml
from pathlib import Path
from flask import Flask
from app import api
from app.proxy_routes import ProxyRoute, proxy_routes

_logger = logging.getLogger(__name__)


def init_app(app: Flask):
    _logger.info("init_app routes")
    app.add_url_rule("/", "index", api.index)
    app.add_url_rule("/login", "login", api.login)
    app.add_url_rule("/logout", "logout", api.logout)
    app.add_url_rule("/callback", "callback", api.callback)
    app.add_url_rule("/me", "me", api.me)

    load_proxy_routes(app)


def load_proxy_routes(app):
    _logger.info("Loading proxy routes from configuration")
    routes_path = Path("routes.yaml")
    if not routes_path.exists():
        _logger.warning("No routes.yaml file found, nothing will be proxied.")
        return

    with routes_path.open() as stream:
        try:
            routes = yaml.load(stream)
            for route in routes.get("routes"):
                load_route(app, route)
        except yaml.YAMLError as exc:
            print(exc)


def load_route(app, route):
    proxy_route = ProxyRoute.from_dict(route)
    _logger.debug(f"Adding route {proxy_route}")
    proxy_routes[proxy_route.name] = proxy_route
    app.add_url_rule(f"{proxy_route.path}/<path:path>", proxy_route.name, api.proxy)
