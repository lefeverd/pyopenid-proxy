class ProxyRoute:
    def __init__(self, name, path, upstream):
        self.name = name
        self.path = path
        self.upstream = upstream

    @staticmethod
    def from_dict(dictionary):
        return ProxyRoute(
            dictionary.get("name"), dictionary.get("path"), dictionary.get("upstream")
        )

    def __repr__(self):
        return (
            f"<ProxyRoute name={self.name} path={self.path} upstream={self.upstream}>"
        )


proxy_routes = {}
