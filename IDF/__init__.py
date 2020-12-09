from jinja2 import Environment, PackageLoader, Template, select_autoescape

class IDF:

    def __init__(self):
        env = Environment(
            loader=PackageLoader("IDF"),
            autoescape=select_autoescape()
        )
        self.template = Template(env.get_template("merged_idf.txt.j2"))





