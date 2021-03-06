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
    app.add_url_rule("/delete", "delete", api.delete, methods=["OPTIONS", "POST"])
    app.add_url_rule("/callback", "callback", api.callback)
    app.add_url_rule("/me", "me", api.me)

    load_proxy_routes(app)


def load_proxy_routes(app):
    _logger.info("Loading proxy routes from configuration")
    routes = get_routes_from_config_file()
    for route in routes.get("routes"):
        load_route(app, route)


def get_routes_from_config_file():
    routes_path = Path("routes.yaml")
    if not routes_path.exists():
        raise Exception("No routes.yaml file found, nothing will be proxied.")

    with routes_path.open() as stream:
        try:
            routes = yaml.load(stream)
            return routes
        except yaml.YAMLError as exc:
            print(exc)


def load_route(app, route):
    proxy_route = ProxyRoute.from_dict(route)
    _logger.info(f"Adding route {proxy_route}")
    proxy_routes[proxy_route.name] = proxy_route
    app.add_url_rule(
        f"{proxy_route.path}/<path:path>",
        proxy_route.name,
        api.proxy,
        methods=["GET", "HEAD", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"],
    )
