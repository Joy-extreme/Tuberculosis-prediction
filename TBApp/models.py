from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class userInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default=None)
    email_verification_token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_email_verified = models.BooleanField(default=False)
    email_verification_sent_at = models.DateTimeField(default=timezone.now)
    is_premium_user = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.name}"


class Subscription(models.Model):
    user_info = models.OneToOneField(userInfo, on_delete=models.CASCADE, related_name='subscription')
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)  # Stripe subscription ID

    def is_subscription_active(self):
        if self.subscription_end_date:
            return self.subscription_end_date > timezone.now()
        return False

    def __str__(self):
        return f"Subscription for {self.user_info.user.username} - Status: {'Active' if self.is_subscription_active() else 'Expired'}"


class Payment(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    payment_status = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, choices=[('credit_card', 'Credit Card'), ('paypal', 'PayPal')], null=True, blank=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)  # Added field

    def get_plan_type(self):
        if self.payment_amount == 19.99:
            return 'Monthly'
        return 'Yearly'

    def __str__(self):
        return f"Payment of {self.payment_amount} for {self.subscription.user_info.name}"


class Report(models.Model):
    user_info = models.ForeignKey(userInfo, on_delete=models.CASCADE, related_name='reports')
    report_file = models.FileField(upload_to='reports/')
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.user_info.name} on {self.generated_at.strftime('%Y-%m-%d')}"



