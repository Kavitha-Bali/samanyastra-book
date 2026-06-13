from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect
from books.models import Transaction, Books
from azure.storage.blob import BlobServiceClient


def _blob_client(blob_path):
    client = BlobServiceClient(
        account_url=f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net",
        credential=settings.AZURE_ACCOUNT_KEY,
    )
    return client.get_blob_client(container=settings.AZURE_CONTAINER_MEDIA, blob=blob_path)


def serve_media(request, path):
    """Proxy /media/* — streams from Azure, never exposes blob URL."""
    try:
        download = _blob_client(path).download_blob()
        props = download.properties
        content_type = (props.get('content_settings') or {}).get('content_type') or 'application/octet-stream'
        return StreamingHttpResponse(download.chunks(), content_type=content_type)
    except Exception:
        raise Http404


def protected_book_file(request, filename):
    """Only serve book PDFs to users who purchased them."""
    if not request.user.is_authenticated:
        return redirect(f'/login/?next={request.path}')
    book = get_object_or_404(Books, file=f'books/{filename}')
    if not Transaction.objects.filter(user=request.user, book=book).exists():
        raise Http404
    try:
        download = _blob_client(f'books/{filename}').download_blob()
        response = StreamingHttpResponse(download.chunks(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{book.title}.pdf"'
        return response
    except Exception:
        raise Http404


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('books.urls')),
    path('', include('django_messaging.urls')),
    re_path(r'^media/books/(?P<filename>.+)$', protected_book_file),
    re_path(r'^media/(?P<path>.+)$', serve_media),
]
