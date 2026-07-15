from storages.backends.azure_storage import AzureStorage
from django.conf import settings


class ProxiedAzureStorage(AzureStorage):
    """
    Stores files in Azure Blob Storage but returns /media/<name>
    so all media is served through Django's proxy view, never directly.
    """
    def url(self, name):
        return f"{settings.MEDIA_URL}{name}"


class ProxiedAzureStaticStorage(AzureStorage):
    """
    Stores static files in Azure Blob Storage but returns /static/<name>
    so all static assets are served through Django's proxy view, never directly.
    """
    def url(self, name):
        return f"{settings.STATIC_URL}{name}"
