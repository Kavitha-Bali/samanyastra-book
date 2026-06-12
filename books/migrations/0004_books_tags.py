from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0003_cart_promocode_rating_userprofile_delete_promocodes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='books',
            name='tags',
            field=models.CharField(blank=True, default='', max_length=400),
        ),
    ]
