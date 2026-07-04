from django.urls import path
from . import views

urlpatterns = [

    # ── Public Home ──
    path('', views.home, name='home'),
    path('home/cart/add/<int:book_id>/', views.home_add_cart, name='home-add-cart'),
    path('home/buy/<int:book_id>/',      views.home_buy_now,  name='home-buy-now'),

    # ── Admin Panel ──
    path('panel/login/',                        views.panel_login,        name='panel-login'),
    path('panel/logout/',                       views.panel_logout,       name='panel-logout'),
    path('panel/',                              views.panel_dashboard,    name='panel-dashboard'),
    path('panel/books/',                        views.panel_books,        name='panel-books'),
    path('panel/books/add/',                    views.panel_book_add,     name='panel-book-add'),
    path('panel/books/regenerate-all-thumbnails/', views.panel_regenerate_all_thumbnails, name='panel-regenerate-all-thumbnails'),
    path('panel/books/<int:book_id>/edit/',     views.panel_book_edit,         name='panel-book-edit'),
    path('panel/books/<int:book_id>/delete/',   views.panel_book_delete,       name='panel-book-delete'),
    path('panel/books/<int:book_id>/cover/',           views.panel_book_cover_upload,        name='panel-book-cover'),
    path('panel/books/<int:book_id>/previews/',        views.panel_book_preview_upload,      name='panel-book-previews'),
    path('panel/books/<int:book_id>/regenerate-thumbnail/', views.panel_regenerate_thumbnail, name='panel-regenerate-thumbnail'),
    path('panel/books/image/<int:image_id>/delete/',   views.panel_book_image_delete,        name='panel-book-image-delete'),
    path('panel/users/',                        views.panel_users,        name='panel-users'),
    path('panel/users/<int:user_id>/delete/',   views.panel_user_delete,  name='panel-user-delete'),
    path('panel/transactions/',                 views.panel_transactions, name='panel-transactions'),
    path('panel/promos/',                       views.panel_promos,       name='panel-promos'),
    path('panel/promos/add/',                   views.panel_promo_add,    name='panel-promo-add'),
    path('panel/promos/<int:promo_id>/edit/',   views.panel_promo_edit,   name='panel-promo-edit'),
    path('panel/promos/<int:promo_id>/delete/', views.panel_promo_delete, name='panel-promo-delete'),

    # ── User Auth ──
    path('register/',         views.user_register,   name='user-register'),
    path('login/',             views.user_login,      name='user-login'),
    path('logout/',            views.user_logout,     name='user-logout'),
    path('forgot-password/',          views.forgot_password, name='forgot-password'),
    path('reset-password/<str:token>/', views.reset_password,  name='reset-password'),

    # ── User Panel ──
    path('shop/',                            views.user_home,         name='user-home'),
    path('shop/book/<int:book_id>/',         views.user_book_detail,  name='user-book-detail'),
    path('shop/cart/',                       views.user_cart,         name='user-cart'),
    path('shop/cart/add/<int:book_id>/',     views.add_to_cart,       name='add-to-cart'),
    path('shop/cart/remove/<int:book_id>/',  views.remove_from_cart,  name='remove-from-cart'),
    path('shop/purchase/<int:book_id>/',          views.purchase_book,             name='purchase-book'),
    path('shop/purchase/cart/',                   views.purchase_cart,             name='purchase-cart'),
    path('shop/transactions/',                    views.user_transactions,         name='user-transactions'),
    path('shop/rate/<int:book_id>/',              views.rate_book,                 name='rate-book'),
    path('shop/cart/checkout/',                   views.razorpay_create_cart_order,  name='razorpay-create-cart-order'),
    path('shop/cart/verify/',                     views.razorpay_verify_cart_payment, name='razorpay-verify-cart-payment'),
    path('shop/book/<int:book_id>/checkout/',     views.razorpay_create_order,       name='razorpay-create-order'),
    path('shop/book/<int:book_id>/verify/',       views.razorpay_verify_payment,     name='razorpay-verify-payment'),
    path('shop/book/<int:book_id>/download/',     views.download_book,             name='download-book'),

    # ── SEO ──
    path('robots.txt',  views.robots_txt,  name='robots-txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap-xml'),

    # ── REST API ──
    path('api/books/',                          views.api_books,              name='api-books'),
    path('api/books/<int:book_id>/',            views.api_book_detail,        name='api-book-detail'),
    path('api/users/',                          views.api_users,              name='api-users'),
    path('api/users/<int:user_id>/',            views.api_user_detail,        name='api-user-detail'),
    path('api/cart/',                           views.api_cart,               name='api-cart'),
    path('api/cart/remove/<int:book_id>/',      views.api_cart_remove,        name='api-cart-remove'),
    path('api/transactions/',                   views.api_transactions,       name='api-transactions'),
    path('api/transactions/<int:txn_id>/',      views.api_transaction_detail, name='api-transaction-detail'),
    path('api/books/<int:book_id>/ratings/',    views.api_ratings,            name='api-ratings'),
    path('api/promos/',                         views.api_promos,             name='api-promos'),
    path('api/promos/<int:promo_id>/',          views.api_promo_detail,       name='api-promo-detail'),
]
