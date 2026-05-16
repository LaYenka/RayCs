project = 'RayCs'
copyright = '2026, RayCs Team'
author = 'RayCs Team'
version = '1.0.0'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'alabaster'
html_static_path = ['_static']
html_sidebars = {
    '**': ['globaltoc.html', 'searchbox.html'],
}
html_theme_options = {
    'fixed_sidebar': True,
    'sidebar_width': '280px',
    'page_width': '1000px',
    'show_related': False,
}
