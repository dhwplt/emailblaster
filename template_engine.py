from jinja2 import Template, Environment, meta

def render_template(template_str, context_dict):
    """
    Renders a Jinja2 template string using the provided context dictionary.
    """
    # If the user leaves the field empty, return empty
    if not template_str:
        return ""
        
    template = Template(template_str)
    return template.render(**context_dict)
