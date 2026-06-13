from django.db import models
from django.contrib.auth.models import User


class Books(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    description = models.TextField()
    language = models.CharField(max_length=30)
    isbn = models.CharField(max_length=13, unique=True)
    pages = models.IntegerField()
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    published_date = models.DateField( models.DateField, auto_now_add=True)
    cover_image = models.ImageField(upload_to="covers/", blank=True, null=True)
    thumb = models.URLField(blank=True, null=True)
    file = models.FileField(upload_to="books/", blank=True, null=True)
    tags = models.CharField(max_length=400, blank=True, default='')

    def __str__(self):
        return self.title

    @property
    def tags_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()] if self.tags else []

    @property
    def avg_rating(self):
        ratings = self.ratings.all()
        return (
            round(sum(r.stars for r in ratings) / ratings.count(), 1)
            if ratings.count()
            else 0
        )


class BookImage(models.Model):
    book    = models.ForeignKey(Books, on_delete=models.CASCADE, related_name='images')
    image   = models.ImageField(upload_to='book_previews/')
    caption = models.CharField(max_length=200, blank=True)
    order   = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.book.title} — preview {self.id}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    favorite_books = models.ManyToManyField(Books, blank=True)

    def __str__(self):
        return self.user.username


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart")
    book = models.ForeignKey(Books, on_delete=models.CASCADE)
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")

    def __str__(self):
        return f"{self.user.username} — {self.book.title}"


class Transaction(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions"
    )
    book = models.ForeignKey(Books, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    promo_used = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} — {self.book.title}"


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Books, on_delete=models.CASCADE, related_name="ratings")
    stars = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    review = models.TextField(blank=True)
    rated_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")

    def __str__(self):
        return f"{self.user.username} — {self.book.title} ({self.stars}★)"


class Promocode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    expiration_date = models.DateField()

    def __str__(self):
        return self.code
