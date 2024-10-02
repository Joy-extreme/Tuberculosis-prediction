import re
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
import smtplib
import requests
from django.utils import timezone
import math


def isAdmin(user):
    return user.username == "Admin"


def isUser(user):
    return user.username != "Admin"


def isPremiumUser(user):
    return user.userinfo.is_premium_user


def validateEmail(email):
    gmailRegex = r'^[a-zA-Z0-9_.+-]+@gmail\.com$'
    return re.match(gmailRegex, email)


def sendMailAfterRegistration(email, token):
    subject = "Account verification"
    message = f"Use this link for your account verification http://127.0.0.1:8000/verify/{token}"
    hostEmail = settings.EMAIL_HOST_USER
    recipient = [email]
    try:
        send_mail(subject, message, hostEmail, recipient)
        return True
    except (BadHeaderError, smtplib.SMTPException) as e:
        return False


def isRealEmail(email):
    api_key = 'ae64c5d9023a1c8f13bf87bc089363472e9764a0'
    url = 'https://api.hunter.io/v2/email-verifier'
    params = {
        'email': email,
        'api_key': api_key
    }
    response = requests.get(url, params=params)
    data = response.json()

    if data.get('data', {}).get('status') == 'invalid':
        return False
    return True


def calculate_end_date(plan):
    if plan == 'monthly':
        return timezone.now() + timezone.timedelta(days=30)
    elif plan == 'yearly':
        return timezone.now() + timezone.timedelta(days=365)
    return timezone.now()


def userDashboardCalculations(subscription):
    remaining_days = (subscription.subscription_end_date - timezone.now()).days
    total_days = (subscription.subscription_end_date - subscription.subscription_start_date).days
    subscription_progress = math.ceil((total_days - remaining_days) / total_days * 100)
    last_payment = subscription.payments.order_by('-payment_date').first()  # get last payment

    context = {
        'subscription': subscription,
        'remaining_days': remaining_days,
        'subscription_progress': subscription_progress,
        'last_payment': last_payment,
    }

    return context