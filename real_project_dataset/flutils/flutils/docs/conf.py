import os
import sys
import typing
from datetime import datetime

typing.TYPE_CHECKING = True
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "flutils")
    ),
)
from flutils import __version__ as release

project = "flutils"
copyright = "%s, Finite Loop, LLC" % datetime.now().year
author = "Finite Loop, LLC"
version = ".".join(release.split(".")[:2])
release = "v%s" % release
version = "v%s" % version
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
]
add_module_names = False
set_type_checking_flag = False
typehints_fully_qualified = False
always_document_param_types = False
typehints_document_rtype = True
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
language = "en"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
pygments_style = "sphinx"
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "canonical_url": "",
    "analytics_id": "",
    "logo_only": True,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "collapse_navigation": False,
    "sticky_navigation": False,
    "navigation_depth": 4,
}
html_logo = "static/flutils-logo.svg"
html_static_path = ["_static"]
html_title = "flutils documentation"
html_short_title = "flutils"
htmlhelp_basename = "flutilsdoc"
latex_elements = {}
latex_documents = [
    (master_doc, "flutils.tex", "flutils Documentation", "Finite Loop, LLC", "manual")
]
man_pages = [(master_doc, "flutils", "flutils Documentation", [author], 1)]
texinfo_documents = [
    (
        master_doc,
        "flutils",
        "flutils Documentation",
        author,
        "flutils",
        "One line description of project.",
        "Miscellaneous",
    )
]
epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright
epub_exclude_files = ["search.html"]
todo_include_todos = True
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = False
napoleon_use_keyword = True
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
html_context = {
    "display_gitlab": True,
    "gitlab_user": "finite-loop",
    "gitlab_repo": "flutils",
    "gitlab_version": "master",
    "conf_py_path": "/docs/",
}
rst_epilog = f"""
.. |ProjectVersion| replace:: {release}
"""


def setup(app):
    app.add_css_file("css/style.css")
