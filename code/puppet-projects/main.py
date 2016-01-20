# -*- coding: utf-8 -*-
from __future__ import absolute_import

# standard
import logging
from logging.handlers import RotatingFileHandler

# external
from flask import Flask
from flask.ext.assets import Environment, Bundle

from gitlaber.views import view
from gitlaber import config

application = Flask(__name__,\
	                static_folder="gitlaber/static/",\
	                template_folder="gitlaber/templates/",
	                static_url_path="/static")
application.secret_key = config.SECRET_KEY

application.register_blueprint(view)

# Scss
assets = Environment(application)
assets.versions = 'timestamp'
assets.url_expire = True
assets.manifest = 'file:c:\\manifest.to-be-deployed'  # explict filename
assets.cache = False
assets.auto_build = True

assets.url = application.static_url_path
scss = Bundle('scss/00_main.scss', filters='pyscss', output='css/main.css', depends=['scss/*.scss'])
assets.register('scss_all', scss)

assets.debug = False
application.config['ASSETS_DEBUG'] = False

# Set Logger
log = logging.getLogger("gitlaber")
console_formatter = logging.Formatter(
            '%(filename)s:%(lineno)d\t\t\t%(message)s', '%m-%d %H:%M:%S')
file_formatter = logging.Formatter(
            '%(levelname)s - %(asctime)s - %(process)s - %(pathname)s - %(lineno)d\n%(message)s', '%m-%d %H:%M:%S')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(console_formatter)

rotatingfile_handler = RotatingFileHandler('gitlaber.log', maxBytes=10000, backupCount=1)
rotatingfile_handler.setLevel(logging.DEBUG)
rotatingfile_handler.setFormatter(file_formatter)

log.addHandler(console_handler)
log.setLevel(10)



def run():
    # Start Application
    application.run(host="0.0.0.0", port=5000, debug=True)

if __name__ == '__main__':
    run()
