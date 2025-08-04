#!/usr/bin/env python3
from jinja2 import Environment, FileSystemLoader

content = "This is about page"
user_id = "2"
file_loader = FileSystemLoader("templates")
env = Environment(loader=file_loader)
template = env.get_template("notifications.html")
output = template.render(content=content, user_id=user_id)
print(output)
