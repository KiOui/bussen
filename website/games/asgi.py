"""
ASGI config for games project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "games.settings")
django.setup()

from games.routing import application as application_websocket  # noqa

application = application_websocket
