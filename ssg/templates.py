from jinja2 import Environment, FileSystemLoader, select_autoescape
def get_env(templates_dir: str):
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(['html','xml'])
    )
    env.globals['SITE_VERSION'] = 'sitesmith-1.0'
    return env
