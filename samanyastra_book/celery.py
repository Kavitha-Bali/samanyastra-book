import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'samanyastra_book.settings')

app = Celery('samanyastra_book')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
