from django.db.models import Count, Q
from django.db import models
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, login_not_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, FileResponse, HttpResponse
from django.conf import settings
from django.views.decorators.cache import cache_control
from decimal import Decimal
import json
import hmac
import hashlib

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from sso_integration.session import establish_session, clear_session, revoke_refresh_token_cookie

import secrets
from .models import (
    Books,
    UserProfile,
    Cart,
    Transaction,
    Rating,
    Promocode,
    PasswordResetToken,
    BookImage,
    UserProfile,
    Cart,
    Transaction,
    Rating,
    Promocode,
)
from .mailer import send_email

BOOK_GENRES = [
    "Fiction",
    "Non-Fiction",
    "Science",
    "History",
    "Technology",
    "Self-Help",
    "Children",
    "Biography",
    "Comics",
    "Tamil",
    "Poetry",
    "Travel",
    "Business",
    "Health",
    "Education",
    "Romance",
    "Mystery",
    "Fantasy",
    "Horror",
    "Thriller",
]
from .serializers import (
    BooksSerializer,
    UserProfileSerializer,
    CartSerializer,
    TransactionSerializer,
    RatingSerializer,
    PromocodeSerializer,
)

staff_only = user_passes_test(lambda u: u.is_staff, login_url="panel-login")


# ════════════════════════════════════
#  PUBLIC HOME
# ════════════════════════════════════
@login_not_required
def home(request):
    q = request.GET.get("q", "").strip()
    qs = Books.objects.filter(title__icontains=q) if q else Books.objects.all()
    cart_ids = (
        list(Cart.objects.filter(user=request.user).values_list("book_id", flat=True))
        if request.user.is_authenticated else []
    )
    purchased_ids = (
        list(Transaction.objects.filter(user=request.user, status=Transaction.STATUS_COMPLETED).values_list("book_id", flat=True))
        if request.user.is_authenticated else []
    )
    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "books/home.html", {
        "books": page_obj,
        "page_obj": page_obj,
        "cart_ids": cart_ids,
        "purchased_ids": purchased_ids,
        "q": q,
    })


@login_not_required
def home_add_cart(request, book_id):
    if not request.user.is_authenticated:
        return redirect(f"/login/?next=/")
    book = get_object_or_404(Books, id=book_id)
    Cart.objects.get_or_create(user=request.user, book=book)
    messages.success(request, f'"{book.title}" added to cart!')
    return redirect("/")


@login_not_required
def home_buy_now(request, book_id):
    if not request.user.is_authenticated:
        return redirect(f"/login/?next=/")
    book = get_object_or_404(Books, id=book_id)
    Cart.objects.get_or_create(user=request.user, book=book)
    return redirect("user-cart")


# ════════════════════════════════════
#  ADMIN PANEL — HTML Views
# ════════════════════════════════════


@login_not_required
def panel_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("panel-dashboard")
        messages.error(request, "You do not have permission to access the admin panel.")
        return redirect("user-home")
    error = None
    if request.method == "POST":
        u = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"],
        )
        if u and u.is_staff:
            login(request, u)
            return redirect("panel-dashboard")
        error = "Invalid credentials or not an admin account."
    return render(request, "books/panel/login.html", {"error": error})


@login_not_required
def panel_logout(request):
    logout(request)
    return redirect("panel-login")


@login_required(login_url="panel-login")
@staff_only
def panel_dashboard(request):
    completed_txns = Transaction.objects.filter(status=Transaction.STATUS_COMPLETED)
    return render(
        request,
        "books/panel/dashboard.html",
        {
            "book_count": Books.objects.count(),
            "user_count": User.objects.filter(is_staff=False).count(),
            "txn_count": completed_txns.count(),
            "promo_count": Promocode.objects.count(),
            "recent_books": Books.objects.order_by("-id")[:6],
            "recent_txns": completed_txns.select_related("user", "book").order_by(
                "-transaction_date"
            )[:5],
        },
    )


@login_required(login_url="panel-login")
@staff_only
def panel_books(request):
    books = Books.objects.annotate(
        preview_count=Count("images"),
        copies_sold=Count("transaction", filter=models.Q(transaction__status="completed")),
    ).order_by("title")
    total = books.count()
    covers_count = books.exclude(cover_image="").exclude(cover_image=None).count()
    no_cover_count = total - covers_count
    total_sold = sum(b.copies_sold for b in books)
    return render(
        request,
        "books/panel/books_list.html",
        {
            "books": books,
            "covers_count": covers_count,
            "no_cover_count": no_cover_count,
            "total_sold": total_sold,
        },
    )


@login_required(login_url="panel-login")
@staff_only
def panel_book_add(request):
    if request.method == "POST":
        d, f = request.POST, request.FILES
        book = Books.objects.create(
            name=d["name"],
            title=d["title"],
            author=d["author"],
            description=d["description"],
            language=d["language"],
            isbn=d["isbn"],
            pages=int(d["pages"]),
            amount=Decimal(d["amount"]),
            published_date=d["published_date"],
            cover_image=f.get("cover_image") or None,
            thumb=d.get("thumb") or None,
            file=f.get("file") or None,
            tags=d.get("tags", ""),
        )
        for i, img_file in enumerate(request.FILES.getlist("preview_images")):
            BookImage.objects.create(book=book, image=img_file, order=i)
        messages.success(request, f'Book "{d["title"]}" added successfully.')
        return redirect("panel-books")
    return render(request, "books/panel/book_form.html", {"genres": BOOK_GENRES})


@login_required(login_url="panel-login")
@staff_only
def panel_book_edit(request, book_id):
    book = get_object_or_404(Books, id=book_id)
    if request.method == "POST":
        d, f = request.POST, request.FILES
        book.name = d["name"]
        book.title = d["title"]
        book.author = d["author"]
        book.language = d["language"]
        book.description = d["description"]
        book.isbn = d["isbn"]
        book.pages = int(d["pages"])
        book.amount = Decimal(d["amount"])
        book.published_date = d["published_date"]
        book.thumb = d.get("thumb") or None
        book.tags = d.get("tags", "")
        if f.get("cover_image"):
            book.cover_image = f["cover_image"]
        if f.get("file"):
            book.file = f["file"]
        book.save()
        existing_count = book.images.count()
        for i, img_file in enumerate(request.FILES.getlist("preview_images")):
            BookImage.objects.create(
                book=book, image=img_file, order=existing_count + i
            )
        messages.success(request, f'Book "{book.title}" updated.')
        return redirect("panel-books")
    return render(
        request,
        "books/panel/book_form.html",
        {
            "book": book,
            "genres": BOOK_GENRES,
            "preview_images": book.images.all(),
        },
    )


@login_required(login_url="panel-login")
@staff_only
def panel_regenerate_thumbnail(request, book_id):
    from .signals import build_thumbnail
    book = get_object_or_404(Books, id=book_id)
    if not book.cover_image:
        messages.error(request, f'"{book.title}" has no cover image to generate thumbnail from.')
        return redirect('panel-books')
    success = build_thumbnail(book)
    if success:
        messages.success(request, f'Thumbnail regenerated for "{book.title}".')
    else:
        messages.error(request, f'Thumbnail generation failed for "{book.title}".')
    return redirect('panel-books')


@login_required(login_url="panel-login")
@staff_only
def panel_regenerate_all_thumbnails(request):
    if request.method != 'POST':
        return redirect('panel-books')
    from .signals import build_thumbnail
    books = Books.objects.exclude(cover_image='').exclude(cover_image=None)
    total = books.count()
    count = sum(1 for book in books if build_thumbnail(book))
    messages.success(request, f'Regenerated thumbnails for {count}/{total} books.')
    return redirect('panel-books')


@login_required(login_url="panel-login")
@staff_only
def panel_book_cover_upload(request, book_id):
    book = get_object_or_404(Books, id=book_id)
    if request.method == "POST" and request.FILES.get("cover_image"):
        book.cover_image = request.FILES["cover_image"]
        book.save()
        messages.success(request, f'Cover image updated for "{book.title}".')
    else:
        messages.error(request, "No image file received.")
    return redirect("panel-books")


@login_required(login_url="panel-login")
@staff_only
def panel_book_preview_upload(request, book_id):
    book = get_object_or_404(Books, id=book_id)
    next_url = request.POST.get("next") or request.GET.get("next") or "panel-books"
    if request.method == "POST":
        files = request.FILES.getlist("preview_images")
        if files:
            base_order = book.images.count()
            for i, img_file in enumerate(files):
                BookImage.objects.create(
                    book=book, image=img_file, order=base_order + i
                )
            messages.success(
                request,
                f'{len(files)} preview image{"s" if len(files) > 1 else ""} added to "{book.title}".',
            )
        else:
            messages.error(request, "No images received.")
    if next_url == "panel-books" or next_url.startswith("/panel/"):
        return redirect("panel-books")
    return redirect(next_url)


@login_required(login_url="panel-login")
@staff_only
def panel_book_image_delete(request, image_id):
    img = get_object_or_404(BookImage, id=image_id)
    book_id = img.book.id
    if request.method == "POST":
        img.image.delete(save=False)
        img.delete()
        messages.success(request, "Preview image removed.")
    return redirect("panel-book-edit", book_id=book_id)


@login_required(login_url="panel-login")
@staff_only
def panel_book_delete(request, book_id):
    book = get_object_or_404(Books, id=book_id)
    if request.method == "POST":
        title = book.title
        book.delete()
        messages.success(request, f'Book "{title}" deleted.')
        return redirect("panel-books")
    return render(request, "books/panel/book_delete.html", {"book": book})


@login_required(login_url="panel-login")
@staff_only
def panel_users(request):
    return render(
        request,
        "books/panel/users_list.html",
        {"users": User.objects.filter(is_staff=False).order_by("-date_joined")},
    )


@login_required(login_url="panel-login")
@staff_only
def panel_user_delete(request, user_id):
    del_user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        name = del_user.username
        del_user.delete()
        messages.success(request, f'User "{name}" deleted.')
        return redirect("panel-users")
    return render(request, "books/panel/user_delete.html", {"del_user": del_user})


@login_required(login_url="panel-login")
@staff_only
def panel_transactions(request):
    return render(
        request,
        "books/panel/transactions_list.html",
        {
            "transactions": Transaction.objects.filter(status=Transaction.STATUS_COMPLETED)
                .select_related("user", "book").order_by("-transaction_date")
        },
    )


@login_required(login_url="panel-login")
@staff_only
def panel_promos(request):
    return render(
        request,
        "books/panel/promos_list.html",
        {"promos": Promocode.objects.all().order_by("expiration_date")},
    )


@login_required(login_url="panel-login")
@staff_only
def panel_promo_add(request):
    if request.method == "POST":
        d = request.POST
        Promocode.objects.create(
            code=d["code"],
            discount_percentage=d["discount_percentage"],
            expiration_date=d["expiration_date"],
        )
        messages.success(request, f'Promo "{d["code"]}" added.')
        return redirect("panel-promos")
    return render(request, "books/panel/promo_form.html")


@login_required(login_url="panel-login")
@staff_only
def panel_promo_edit(request, promo_id):
    promo = get_object_or_404(Promocode, id=promo_id)
    if request.method == "POST":
        d = request.POST
        promo.code = d["code"]
        promo.discount_percentage = d["discount_percentage"]
        promo.expiration_date = d["expiration_date"]
        promo.save()
        messages.success(request, f'Promo "{promo.code}" updated.')
        return redirect("panel-promos")
    return render(request, "books/panel/promo_form.html", {"promo": promo})


@login_required(login_url="panel-login")
@staff_only
def panel_promo_delete(request, promo_id):
    promo = get_object_or_404(Promocode, id=promo_id)
    if request.method == "POST":
        code = promo.code
        promo.delete()
        messages.success(request, f'Promo "{code}" deleted.')
        return redirect("panel-promos")
    return render(request, "books/panel/promo_delete.html", {"promo": promo})


# ════════════════════════════════════
#  USER AUTH
# ════════════════════════════════════


@login_not_required
def user_register(request):
    if request.user.is_authenticated:
        return redirect("user-home")
    errors = []
    form_data = {}
    if request.method == "POST":
        d = request.POST
        username = d.get("username", "").strip()
        email = d.get("email", "").strip()
        password = d.get("password", "")
        password2 = d.get("password2", "")
        form_data = {"username": username, "email": email}

        # 1. Username format — letters, digits, @/./+/-/_ only
        try:
            UnicodeUsernameValidator()(username)
        except ValidationError as e:
            errors.extend(e.messages)

        # 2. Username length
        if len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        elif len(username) > 150:
            errors.append("Username must be 150 characters or fewer.")

        # 3. Username already taken (case-insensitive)
        if not errors:
            if User.objects.filter(username__iexact=username).exists():
                errors.append("That username is already taken.")

        # 4. Passwords match
        if password != password2:
            errors.append("Passwords do not match.")

        # 5. Django password validators (length, similarity, common, numeric)
        if not errors:
            try:
                validate_password(password, user=User(username=username, email=email))
            except ValidationError as e:
                errors.extend(e.messages)

        if not errors:
            u = User.objects.create_user(
                username=username, email=email, password=password
            )
            UserProfile.objects.create(user=u)
            login(request, u)
            return redirect("user-home")

    return render(
        request, "books/user/register.html", {"errors": errors, "form_data": form_data}
    )


@login_not_required
def user_login(request):
    if request.user.is_authenticated:
        return redirect("user-home")
    error = None
    if request.method == "POST":
        u = authenticate(
            request,
            username=request.POST["username"],
            password=request.POST["password"],
        )
        if u:
            login(request, u)
            # response = redirect(next_url or settings.LOGIN_REDIRECT_URL)
            # establish_session(response, u, auth_source="local")
            return redirect("user-home")
        error = "Invalid username or password."
    return render(request, "books/user/login.html", {"error": error})


@login_not_required
def user_logout(request):
    revoke_refresh_token_cookie(request.COOKIES.get("refresh_token", ""))
    logout(request)
    response = redirect("user-login")
    clear_session(response)
    return response


@login_not_required
def reset_password(request, token):
    token_obj = PasswordResetToken.objects.filter(token=token, is_expired=False).select_related('user').first()

    if token_obj is None:
        return render(request, 'books/user/token_invalid.html')

    error = None
    if request.method == 'POST':
        # Re-validate token on submit to prevent replay after expiry
        token_obj = PasswordResetToken.objects.filter(token=token, is_expired=False).select_related('user').first()
        if token_obj is None:
            return render(request, 'books/user/token_invalid.html')

        password  = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        user      = token_obj.user

        if not password:
            error = 'Password cannot be empty.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters.'
        elif password != password2:
            error = 'Passwords do not match.'
        elif user.check_password(password):
            error = 'New password must be different from your current password.'
        else:
            user.set_password(password)
            user.save()
            token_obj.is_expired = True
            token_obj.save()
            messages.success(request, 'Password reset successful. Please log in.')
            return redirect('user-login')

    return render(request, 'books/user/reset_password.html', {'token': token, 'error': error})


@login_not_required
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user  = User.objects.filter(email=email).first()
        if user:
            # Expire any existing tokens for this user
            PasswordResetToken.objects.filter(user=user, is_expired=False).update(is_expired=True)

            token = secrets.token_hex(16)  # 32-char hex string
            PasswordResetToken.objects.create(user=user, token=token)

            reset_link = request.build_absolute_uri(f'/reset-password/{token}/')
            send_email('forgot_password', user.email, user_name=user.get_full_name() or user.username, reset_link=reset_link)

        # Always show success to avoid email enumeration
        messages.success(request, 'If that email exists, a reset link has been sent.')
        return redirect('forgot-password')
    return render(request, 'books/user/forgot_password.html')


# ════════════════════════════════════
#  USER PANEL — HTML Views
# ════════════════════════════════════


@login_required(login_url="user-login")
def user_home(request):
    q = request.GET.get("q", "").strip()
    qs = Books.objects.filter(title__icontains=q) if q else Books.objects.all()
    cart_ids = list(Cart.objects.filter(user=request.user).values_list("book_id", flat=True))
    purchased_ids = list(Transaction.objects.filter(user=request.user, status=Transaction.STATUS_COMPLETED).values_list("book_id", flat=True))
    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "books/user/home.html", {
        "books": page_obj,
        "page_obj": page_obj,
        "cart_ids": cart_ids,
        "purchased_ids": purchased_ids,
        "q": q,
        "genres": BOOK_GENRES,
        "total_books": Books.objects.count(),
    })


@login_required(login_url="user-login")
def user_book_detail(request, book_id):
    book = get_object_or_404(Books, id=book_id)
    ratings = Rating.objects.filter(book=book).select_related("user")
    user_rating = ratings.filter(user=request.user).first()
    in_cart = Cart.objects.filter(user=request.user, book=book).exists()
    purchased = Transaction.objects.filter(user=request.user, book=book, status=Transaction.STATUS_COMPLETED).exists()
    return render(
        request,
        "books/user/book_detail.html",
        {
            "book": book,
            "ratings": ratings,
            "user_rating": user_rating,
            "in_cart": in_cart,
            "purchased": purchased,
            "preview_images": book.images.all(),
        },
    )


@login_required(login_url="user-login")
def add_to_cart(request, book_id):
    book = get_object_or_404(Books, id=book_id)
    Cart.objects.get_or_create(user=request.user, book=book)
    messages.success(request, f'"{book.title}" added to cart.')
    return redirect(request.META.get("HTTP_REFERER", "user-cart"))


@login_required(login_url="user-login")
def remove_from_cart(request, book_id):
    Cart.objects.filter(user=request.user, book_id=book_id).delete()
    return redirect("user-cart")


@login_required(login_url="user-login")
def user_cart(request):
    cart_items = Cart.objects.filter(user=request.user).select_related("book")
    total = sum(item.book.amount for item in cart_items)
    discount = Decimal("0")
    promo_msg = ""
    if request.method == "POST" and "apply_promo" in request.POST:
        code = request.POST.get("promo_code", "").strip().upper()
        try:
            promo = Promocode.objects.get(code=code)
            if promo.expiration_date >= timezone.now().date():
                discount = (total * promo.discount_percentage) / 100
                promo_msg = f'Promo "{code}" applied! {promo.discount_percentage}% off.'
            else:
                promo_msg = "Promo code expired."
        except Promocode.DoesNotExist:
            promo_msg = "Invalid promo code."
    return render(
        request,
        "books/user/cart.html",
        {
            "cart_items": cart_items,
            "total": total,
            "discount": discount,
            "final": total - discount,
            "promo_msg": promo_msg,
        },
    )


@login_required(login_url="user-login")
def purchase_book(request, book_id):
    book = get_object_or_404(Books, id=book_id)
    if request.method == "POST":
        Cart.objects.get_or_create(user=request.user, book=book)
        return redirect("user-cart")
    return redirect("user-book-detail", book_id=book_id)


@login_required(login_url="user-login")
def purchase_cart(request):
    # Legacy non-Razorpay path — redirect to cart for proper payment
    return redirect("user-cart")


@login_required(login_url="user-login")
def user_transactions(request):
    txns = (
        Transaction.objects.filter(user=request.user, status=Transaction.STATUS_COMPLETED)
        .select_related("book")
        .order_by("-transaction_date")
    )
    return render(request, "books/user/transactions.html", {"transactions": txns})


@login_required(login_url="user-login")
def razorpay_create_cart_order(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    import razorpay

    data = json.loads(request.body)
    promo_code = data.get("promo_code", "").strip().upper()
    cart_items = Cart.objects.filter(user=request.user).select_related("book")
    if not cart_items.exists():
        return JsonResponse({"error": "Cart is empty"}, status=400)
    total = sum(item.book.amount for item in cart_items)
    discount = Decimal("0")
    if promo_code:
        try:
            promo = Promocode.objects.get(code=promo_code)
            if promo.expiration_date >= timezone.now().date():
                discount = (total * promo.discount_percentage) / 100
        except Promocode.DoesNotExist:
            pass
    final = total - discount
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )
    order = client.order.create(
        {
            "amount": int(final * 100),
            "currency": "INR",
            "receipt": f"cart_user{request.user.id}",
            "payment_capture": 1,
        }
    )
    return JsonResponse(
        {
            "order_id": order["id"],
            "amount": int(final * 100),
            "currency": "INR",
            "key": settings.RAZORPAY_KEY_ID,
            "user_name": request.user.get_full_name() or request.user.username,
            "user_email": request.user.email,
            "promo_code": promo_code,
            "razorpay_order_id": order["id"],
        }
    )


@login_required(login_url="user-login")
def razorpay_verify_cart_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    data = json.loads(request.body)
    order_id = data.get("razorpay_order_id", "")
    payment_id = data.get("razorpay_payment_id", "")
    signature = data.get("razorpay_signature", "")
    promo_code = data.get("promo_code", "").strip().upper()
    message = f"{order_id}|{payment_id}".encode()
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(), message, hashlib.sha256
    ).hexdigest()
    if expected != signature:
        return JsonResponse(
            {"success": False, "error": "Invalid signature"}, status=400
        )
    cart_items = Cart.objects.filter(user=request.user).select_related("book")
    discount = Decimal("0")
    if promo_code:
        try:
            promo = Promocode.objects.get(code=promo_code)
            if promo.expiration_date >= timezone.now().date():
                discount = promo.discount_percentage
        except Promocode.DoesNotExist:
            pass
    razorpay_order_id = data.get("razorpay_order_id", "") or order_id
    for item in cart_items:
        paid = item.book.amount - (item.book.amount * discount / 100)
        txn, _ = Transaction.objects.get_or_create(
            user=request.user,
            book=item.book,
            defaults={"amount_paid": paid, "promo_used": promo_code or None, "razorpay_order_id": razorpay_order_id},
        )
        if txn.status != Transaction.STATUS_COMPLETED:
            txn.status = Transaction.STATUS_COMPLETED
            txn.amount_paid = paid
            txn.promo_used = promo_code or None
            txn.razorpay_order_id = razorpay_order_id
            txn.save(update_fields=["status", "amount_paid", "promo_used", "razorpay_order_id"])
    cart_items.delete()
    return JsonResponse({"success": True, "redirect": "/shop/transactions/"})


@login_required(login_url="user-login")
def razorpay_create_order(request, book_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    import razorpay

    book = get_object_or_404(Books, id=book_id)
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )
    order = client.order.create(
        {
            "amount": int(book.amount * 100),  # paise
            "currency": "INR",
            "receipt": f"book{book_id}_user{request.user.id}",
            "payment_capture": 1,
        }
    )
    return JsonResponse(
        {
            "order_id": order["id"],
            "amount": int(book.amount * 100),
            "currency": "INR",
            "key": settings.RAZORPAY_KEY_ID,
            "book_title": book.title,
            "user_name": request.user.get_full_name() or request.user.username,
            "user_email": request.user.email,
            "razorpay_order_id": order["id"],
        }
    )


@login_required(login_url="user-login")
def razorpay_verify_payment(request, book_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    book = get_object_or_404(Books, id=book_id)
    data = json.loads(request.body)
    order_id = data.get("razorpay_order_id", "")
    payment_id = data.get("razorpay_payment_id", "")
    signature = data.get("razorpay_signature", "")
    message = f"{order_id}|{payment_id}".encode()
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(), message, hashlib.sha256
    ).hexdigest()  # noqa: hmac.new is valid in Py3
    if expected != signature:
        return JsonResponse(
            {"success": False, "error": "Invalid signature"}, status=400
        )
    txn, _ = Transaction.objects.get_or_create(
        user=request.user,
        book=book,
        defaults={"amount_paid": book.amount, "razorpay_order_id": order_id},
    )
    if txn.status != Transaction.STATUS_COMPLETED:
        txn.status = Transaction.STATUS_COMPLETED
        txn.amount_paid = book.amount
        txn.razorpay_order_id = order_id
        txn.save(update_fields=["status", "amount_paid", "razorpay_order_id"])
    Cart.objects.filter(user=request.user, book=book).delete()
    return JsonResponse({"success": True, "redirect": "/shop/transactions/"})


@login_required(login_url="user-login")
def download_book(request, book_id):
    book = get_object_or_404(Books, id=book_id)
    if not Transaction.objects.filter(user=request.user, book=book, status=Transaction.STATUS_COMPLETED).exists():
        messages.error(request, "Please purchase this book before downloading.")
        return redirect("user-book-detail", book_id=book_id)
    if not book.file:
        messages.info(request, "No downloadable file is available for this book yet.")
        return redirect("user-transactions")
    return FileResponse(
        book.file.open("rb"), as_attachment=True, filename=f"{book.title}.pdf"
    )


@login_required(login_url="user-login")
def rate_book(request, book_id):
    book = get_object_or_404(Books, id=book_id)
    if not Transaction.objects.filter(user=request.user, book=book, status=Transaction.STATUS_COMPLETED).exists():
        messages.error(request, "You can only rate purchased books.")
        return redirect("user-book-detail", book_id=book_id)
    if request.method == "POST":
        stars = int(request.POST.get("stars", 5))
        review = request.POST.get("review", "")
        Rating.objects.update_or_create(
            user=request.user, book=book, defaults={"stars": stars, "review": review}
        )
        messages.success(request, "Your rating has been saved!")
        return redirect("user-book-detail", book_id=book_id)
    existing = Rating.objects.filter(user=request.user, book=book).first()
    return render(request, "books/user/rate.html", {"book": book, "existing": existing})


# ════════════════════════════════════
#  SEO — robots.txt & sitemap.xml
# ════════════════════════════════════

@login_not_required
@cache_control(max_age=86400)
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /panel/",
        "Disallow: /admin/",
        "Disallow: /shop/cart/",
        "Disallow: /shop/transactions/",
        "Disallow: /shop/purchase/",
        "Disallow: /api/",
        "",
        "Sitemap: https://books.samanyastra.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


@login_not_required
@cache_control(max_age=3600)
def sitemap_xml(request):
    books = Books.objects.only("id", "published_date").order_by("-id")
    base = "https://books.samanyastra.com"
    urls = [
        {"loc": f"{base}/shop/",     "changefreq": "daily",   "priority": "1.0", "lastmod": ""},
        {"loc": f"{base}/register/", "changefreq": "monthly", "priority": "0.5", "lastmod": ""},
        {"loc": f"{base}/login/",    "changefreq": "monthly", "priority": "0.5", "lastmod": ""},
    ]
    for book in books:
        urls.append({
            "loc": f"{base}/shop/book/{book.id}/",
            "changefreq": "weekly",
            "priority": "0.9",
            "lastmod": book.published_date.strftime("%Y-%m-%d") if book.published_date else "",
        })
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml_parts.append("  <url>")
        xml_parts.append(f"    <loc>{u['loc']}</loc>")
        if u["lastmod"]:
            xml_parts.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        xml_parts.append(f"    <changefreq>{u['changefreq']}</changefreq>")
        xml_parts.append(f"    <priority>{u['priority']}</priority>")
        xml_parts.append("  </url>")
    xml_parts.append("</urlset>")
    return HttpResponse("\n".join(xml_parts), content_type="application/xml")


# ════════════════════════════════════
#  REST API VIEWS
# ════════════════════════════════════


# ── Books ──
@api_view(["GET", "POST"])
def api_books(request):
    if request.method == "GET":
        q = request.GET.get("q", "")
        books = Books.objects.filter(title__icontains=q) if q else Books.objects.all()
        return Response(BooksSerializer(books, many=True).data)
    s = BooksSerializer(data=request.data)
    if s.is_valid():
        s.save()
        return Response(s.data, status=status.HTTP_201_CREATED)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def api_book_detail(request, book_id):
    book = get_object_or_404(Books, id=book_id)
    if request.method == "GET":
        return Response(BooksSerializer(book).data)
    if request.method in ("PUT", "PATCH"):
        s = BooksSerializer(book, data=request.data, partial=request.method == "PATCH")
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    book.delete()
    return Response({"message": "Book deleted"}, status=status.HTTP_204_NO_CONTENT)


# ── Users ──
@api_view(["GET", "POST"])
def api_users(request):
    if request.method == "GET":
        profiles = UserProfile.objects.select_related("user").all()
        return Response(UserProfileSerializer(profiles, many=True).data)
    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email", "")
    if not username or not password:
        return Response(
            {"error": "Username and password required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST
        )
    u = User.objects.create_user(username=username, password=password, email=email)
    profile = UserProfile.objects.create(user=u)
    return Response(
        {"message": "User created", "id": profile.id, "username": u.username},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def api_user_detail(request, user_id):
    profile = get_object_or_404(UserProfile, id=user_id)
    if request.method == "GET":
        return Response(UserProfileSerializer(profile).data)
    if request.method in ("PUT", "PATCH"):
        s = UserProfileSerializer(
            profile, data=request.data, partial=request.method == "PATCH"
        )
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    profile.user.delete()
    return Response({"message": "User deleted"}, status=status.HTTP_204_NO_CONTENT)


# ── Cart ──
@api_view(["GET", "POST"])
def api_cart(request):
    if request.method == "GET":
        cart = (
            Cart.objects.filter(user=request.user)
            if request.user.is_authenticated
            else Cart.objects.none()
        )
        return Response(CartSerializer(cart, many=True).data)
    s = CartSerializer(data=request.data)
    if s.is_valid():
        s.save()
        return Response(s.data, status=status.HTTP_201_CREATED)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def api_cart_remove(request, book_id):
    Cart.objects.filter(user=request.user, book_id=book_id).delete()
    return Response({"message": "Removed from cart"}, status=status.HTTP_204_NO_CONTENT)


# ── Transactions ──
@api_view(["GET", "POST"])
def api_transactions(request):
    if request.method == "GET":
        txns = (
            Transaction.objects.filter(user=request.user)
            if request.user.is_authenticated
            else Transaction.objects.all()
        )
        return Response(TransactionSerializer(txns, many=True).data)
    s = TransactionSerializer(data=request.data)
    if s.is_valid():
        s.save()
        return Response(s.data, status=status.HTTP_201_CREATED)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "DELETE"])
def api_transaction_detail(request, txn_id):
    txn = get_object_or_404(Transaction, id=txn_id)
    if request.method == "GET":
        return Response(TransactionSerializer(txn).data)
    txn.delete()
    return Response(
        {"message": "Transaction deleted"}, status=status.HTTP_204_NO_CONTENT
    )


# ── Ratings ──
@api_view(["GET", "POST"])
def api_ratings(request, book_id):
    book = get_object_or_404(Books, id=book_id)
    if request.method == "GET":
        return Response(
            RatingSerializer(Rating.objects.filter(book=book), many=True).data
        )
    s = RatingSerializer(data=request.data)
    if s.is_valid():
        s.save()
        return Response(s.data, status=status.HTTP_201_CREATED)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Promos ──
@api_view(["GET", "POST"])
def api_promos(request):
    if request.method == "GET":
        return Response(PromocodeSerializer(Promocode.objects.all(), many=True).data)
    s = PromocodeSerializer(data=request.data)
    if s.is_valid():
        s.save()
        return Response(s.data, status=status.HTTP_201_CREATED)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def api_promo_detail(request, promo_id):
    promo = get_object_or_404(Promocode, id=promo_id)
    if request.method == "GET":
        return Response(PromocodeSerializer(promo).data)
    if request.method in ("PUT", "PATCH"):
        s = PromocodeSerializer(
            promo, data=request.data, partial=request.method == "PATCH"
        )
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    promo.delete()
    return Response({"message": "Promo deleted"}, status=status.HTTP_204_NO_CONTENT)
