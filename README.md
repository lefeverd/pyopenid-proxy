# PyOpenID-Proxy

<!-- TOC -->

- [PyOpenID-Proxy](#pyopenid-proxy)
    - [Description](#description)
    - [Endpoints](#endpoints)
    - [Configuration](#configuration)
        - [Redis](#redis)
    - [Development](#development)
        - [Locally](#locally)
        - [Mock client](#mock-client)
        - [Docker](#docker)
        - [Tests](#tests)
    - [WSGI](#wsgi)
    - [OpenID/OAuth providers](#openidoauth-providers)
    - [Notes](#notes)

<!-- /TOC -->

## Description

This project is a simple proxy (written in Python) able to handle OpenID authentication
and OAuth authorization.  
It is highly opinionated, and I mainly use it on side projects where I don't want
to deal with the same OAuth problematics every time.

The application acts as a gateway between the client applications (frontends) and the
API's.  

It's inspired by this great talk from Jacob Ideskog: [https://www.youtube.com/watch?v=BdKmZ7mPNns&feature=youtu.be&t=901](https://www.youtube.com/watch?v=BdKmZ7mPNns&feature=youtu.be&t=901).  
As he explains, it allows to have this proxy in front of our "internal" services, creating a session
for the users with an opaque token, and translating it to pass the JWT token (and ID token) to the
internal services.  

## Endpoints

Multiple endpoints are defined to trigger and handle the OpenID flow, the `authorization code` flow:

- **/login**, can be called by the clients and redirects to the OAuth provider, allowing the user to log in.
- **/callback**, called by the OAuth provider when the user has logged in.  
This endpoint receives the authorization code and exchanges it with an `access token` and
an `id token` (OpenID).  
A client-side session is then created, and its id (also called opaque token or reference token) 
is stored in a cookie (httpOnly).  
The tokens are kept on the server, either in redis or in an in-memory cache (default).  
For the following requests made by the user, this cookie is sent along and the application
can map the session_id from the cookie to the tokens.  
The `access token` is injected in the request going to the proxied API in a header.  
The API's can also get the `id token` vie the `/userinfo` endpoint, providing the `access token`.
- **/logout**, called by the clients to logout, thus removing the client-side session (cookie),
and deleting the server-side session (actual access and id tokens).
- **/me**, can be called by the clients to retrieve the content of the `id token`.

## Configuration

Application configuration is done via environment variables.  
Check the .env.local.example file for the available variables.

Routing configuration is done via the `routes.yaml` file.  
It contains all the upstreams you want to proxy to.  
You can rename `routes.yaml.example` to `routes.yaml` to use it.

### Redis

You can use redis as a cache for the client-side session_id <-> server-side tokens mapping.  
You simply need to have a running redis instance and declare the environment variables:

- REDIS_HOST
- REDIS_PORT

By default, without these variables set, a simple in-memory cache is used.  
It is easier for development purposes, but can cause issues in a multi-threaded environment.

## Development

First rename the `.env.local.example` file to `.env.local`:

```bash
cp .env.local.example .env.local
```

To configure the proxy and route trafic to your API's, rename `routes.yaml.example` to `routes.yaml`:

```bash
cp routes.yaml.example routes.yaml
```

And edit its content.

To enable redis, uncomment the REDIS_ environment variables in the `.env.local` file.  
You need to either have a redis instance running locally, or you can run the one in
the compose file:

```bash
docker-compose up -d redis
```

### Locally

You need `Pipenv` to be able to install the required dependencies.

To run the application locally, execute:

```bash
make init
make run
```

### Mock client

You can use, in the .env.local file:

```bash
MOCK_OAUTH=1
```

To use the Mock OAuth client, which simply always authorize the requests and return a mock token.

### Docker

You can use Docker and Docker-compose to run the dockerized version:

```bash
docker-compose up -d
```

### Tests

To run the tests, execute:

```bash
make test
```

## WSGI

By default, the Docker image uses gunicorn to serve the application.  
The logging is thus setup to use gunicorn handler, and you can specify the level
directly with gunicorn:

```
set -a && source .env.test && set +a && ./venv/bin/gunicorn -b 0.0.0.0:8080 --reload wsgi:app --log-level debug
```

## OpenID/OAuth providers

This application is compatible with auth0.  
I guess other OpenID/OAuth providers should be compatible, but this was not tested.

## Notes

Access tokens and id tokens have different audience.  
The access token has all the APIs defined in auth0 as audience.  
The id token has the client id of the application as audience.  
When decoding the tokens, the audience field must match.  
The issuer will be compared against `settings.OAUTH_BASE_URL + "/"`.  
