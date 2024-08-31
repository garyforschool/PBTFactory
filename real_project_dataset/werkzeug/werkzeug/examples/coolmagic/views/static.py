from coolmagic.utils import export


@export("/", template="static/index.html")
def index():
    pass


@export("/about", template="static/about.html")
def about():
    pass


@export("/broken")
def broken():
    raise RuntimeError("that's really broken")


@export(None, template="static/not_found.html")
def not_found():
    pass
