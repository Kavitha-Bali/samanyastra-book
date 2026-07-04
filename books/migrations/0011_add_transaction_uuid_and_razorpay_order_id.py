import uuid
from django.db import migrations, models


def populate_transaction_ids(apps, schema_editor):
    Transaction = apps.get_model('books', 'Transaction')
    for txn in Transaction.objects.filter(transaction_id__isnull=True):
        txn.transaction_id = uuid.uuid4()
        txn.save(update_fields=['transaction_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0010_add_transaction_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        # Step 1: add as nullable with no default so existing rows get NULL
        migrations.AddField(
            model_name='transaction',
            name='transaction_id',
            field=models.UUIDField(null=True, editable=False),
        ),
        # Step 2: populate unique UUIDs for all existing rows
        migrations.RunPython(populate_transaction_ids, migrations.RunPython.noop),
        # Step 3: make non-null and unique
        migrations.AlterField(
            model_name='transaction',
            name='transaction_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
