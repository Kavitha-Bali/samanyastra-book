from rest_framework import serializers
from .models import Books, UserProfile, Cart, Transaction, Rating, Promocode


class BooksSerializer(serializers.ModelSerializer):
    avg_rating = serializers.ReadOnlyField()
    class Meta:
        model  = Books
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UserProfile
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Cart
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Transaction
        fields = '__all__'

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Rating
        fields = '__all__'

class PromocodeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Promocode
        fields = '__all__'
