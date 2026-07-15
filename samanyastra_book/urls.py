from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect
from books.models import Transaction, Books
from azure.storage.blob import BlobServiceClient
from django.contrib.auth.decorators import login_not_required


def _blob_client(blob_path, container=None):
    client = BlobServiceClient(
        account_url=f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net",
        credential=settings.AZURE_ACCOUNT_KEY,
    )
    return client.get_blob_client(container=container or settings.AZURE_CONTAINER_MEDIA, blob=blob_path)

@login_not_required
def serve_media(request, path):
    """Proxy /media/* — streams from Azure, never exposes blob URL."""
    try:
        download = _blob_client(path).download_blob()
        props = download.properties
        content_type = (props.get('content_settings') or {}).get('content_type') or 'application/octet-stream'
        return StreamingHttpResponse(download.chunks(), content_type=content_type)
    except Exception:
        raise Http404


@login_not_required
def serve_static(request, path):
    """Proxy /static/* — streams from Azure, never exposes blob URL.

    Must stay open (login_not_required): LoginRequiredMiddleware gates every
    view by default, and CSS/JS/login-page assets must load before a user
    is authenticated.
    """
    try:
        download = _blob_client(path, container=settings.AZURE_CONTAINER_STATIC).download_blob()
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
    # books.urls must come first: both it and sso_integration.urls register
    # "logout/", and books.views.user_logout is the one that clears the
    # Django session *and* the SSO JWT cookies. If sso_integration's own
    # logout/ matched first it would only clear the JWT cookies and leave
    # the sessionid cookie (and any locally-authenticated user) logged in.
    path('admin/', admin.site.urls),
    path('', include('books.urls')),
    path("", include("sso_integration.urls")),
    path('', include('django_messaging.urls')),
    re_path(r'^media/books/(?P<filename>.+)$', protected_book_file),
    re_path(r'^media/(?P<path>.+)$', serve_media),
    re_path(r'^static/(?P<path>.+)$', serve_static),
]
