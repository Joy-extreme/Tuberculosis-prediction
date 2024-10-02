# Generated by Django 3.0.5 on 2024-09-04 06:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('TBApp', '0003_userinfo_is_premium_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_start_date', models.DateTimeField(blank=True, null=True)),
                ('subscription_end_date', models.DateTimeField(blank=True, null=True)),
                ('user_info', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='TBApp.userInfo')),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_file', models.FileField(upload_to='reports/')),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('user_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='TBApp.userInfo')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_status', models.BooleanField(default=False)),
                ('payment_method', models.CharField(blank=True, choices=[('credit_card', 'Credit Card'), ('paypal', 'PayPal'), ('bank_transfer', 'Bank Transfer')], max_length=50, null=True)),
                ('payment_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('payment_date', models.DateTimeField(blank=True, null=True)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='TBApp.Subscription')),
            ],
        ),
    ]