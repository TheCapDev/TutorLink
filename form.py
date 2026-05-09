"""Compatibility WSGI entrypoint for legacy hosting start commands.

The Django project entrypoint is ``tutorLink.wsgi:application``. This module
keeps hosts configured with ``gunicorn form`` or ``gunicorn form:app`` working
without changing application behavior.
"""

from tutorLink.wsgi import application

app = application
