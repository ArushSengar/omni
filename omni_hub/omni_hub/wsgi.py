"""
WSGI config for omni_hub project.

It exposes the WSGI callable as a module-level variable named ``application``.
For Vercel deployment, ``app`` is exported as an alias.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omni_hub.settings')

application = get_wsgi_application()
app = application
