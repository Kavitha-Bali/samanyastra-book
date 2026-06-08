from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Books(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    thumb=models.URLField(blank=True, null=True)
    file=models.FileField(upload_to='books/', blank=True, null=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    published_date = models.DateField()
    isbn = models.CharField(max_length=13, unique=True)
    pages = models.IntegerField()
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    cover_image = models.URLField(blank=True, null=True)
    language = models.CharField(max_length=30)

    def __str__(self):
        return self.title
    

class User(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    favorite_books = models.ManyToManyField(Books, blank=True)


    def __str__(self):
        return self.user.username
    


class Userbook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Books, on_delete=models.CASCADE)
    purchased_book=models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.user.username} - {self.book.title}"


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Books, on_delete=models.CASCADE)
    transaction_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)


    def __str__(self):
        return f"{self.user.user.username} - {self.book.title}"
    


class promocodes(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    expiration_date = models.DateField()

    def __str__(self):
        return self.code