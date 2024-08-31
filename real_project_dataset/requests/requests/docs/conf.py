import sys
import os

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("_themes"))
import requests

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"
project = "Requests"
copyright = (
    'MMXVIX. A <a href="https://kenreitz.org/projects">Kenneth Reitz</a> Project'
)
author = "Kenneth Reitz"
version = requests.__version__
release = requests.__version__
language = None
exclude_patterns = ["_build"]
add_function_parentheses = False
add_module_names = True
pygments_style = "flask_theme_support.FlaskyStyle"
todo_include_todos = True
html_theme = "alabaster"
html_theme_options = {
    "show_powered_by": False,
    "github_user": "requests",
    "github_repo": "requests",
    "github_banner": True,
    "show_related": False,
    "note_bg": "#FFF59C",
}
html_static_path = ["_static"]
html_use_smartypants = False
html_sidebars = {
    "index": ["sidebarintro.html", "sourcelink.html", "searchbox.html", "hacks.html"],
    "**": [
        "sidebarlogo.html",
        "localtoc.html",
        "relations.html",
        "sourcelink.html",
        "searchbox.html",
        "hacks.html",
    ],
}
html_show_sourcelink = False
html_show_sphinx = False
html_show_copyright = True
htmlhelp_basename = "Requestsdoc"
latex_elements = {}
latex_documents = [
    (master_doc, "Requests.tex", "Requests Documentation", "Kenneth Reitz", "manual")
]
man_pages = [(master_doc, "requests", "Requests Documentation", [author], 1)]
texinfo_documents = [
    (
        master_doc,
        "Requests",
        "Requests Documentation",
        author,
        "Requests",
        "One line description of project.",
        "Miscellaneous",
    )
]
epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright
epub_exclude_files = ["search.html"]
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "urllib3": ("https://urllib3.readthedocs.io/en/latest", None),
}
