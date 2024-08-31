from werkzeug.routing import EndpointPrefix
from werkzeug.routing import Map
from werkzeug.routing import Rule
from werkzeug.routing import Subdomain
from werkzeug.routing import Submount

m = Map(
    [
        EndpointPrefix(
            "static/",
            [
                Rule("/", endpoint="index"),
                Rule("/about", endpoint="about"),
                Rule("/help", endpoint="help"),
            ],
        ),
        Subdomain(
            "kb",
            [
                EndpointPrefix(
                    "kb/",
                    [
                        Rule("/", endpoint="index"),
                        Submount(
                            "/browse",
                            [
                                Rule("/", endpoint="browse"),
                                Rule(
                                    "/<int:id>/",
                                    defaults={"page": 1},
                                    endpoint="browse",
                                ),
                                Rule("/<int:id>/<int:page>", endpoint="browse"),
                            ],
                        ),
                    ],
                )
            ],
        ),
    ]
)
