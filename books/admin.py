from django.contrib import admin
from .models import Books, UserProfile, Cart, Transaction, Rating, Promocode

admin.site.site_header = "📚 Samanyastra"
admin.site.site_title  = "Samanyastra"
admin.site.index_title = "Samanyastra Dashboard"

admin.site.register(Books)
admin.site.register(UserProfile)
admin.site.register(Cart)
admin.site.register(Transaction)
admin.site.register(Rating)
admin.site.register(Promocode)
