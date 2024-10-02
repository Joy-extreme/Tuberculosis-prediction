from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
import stripe
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import userInfo, Subscription, Payment, Report
import uuid
from .utils import *


def homeView(request):
    if request.user.is_authenticated:
        if request.user.username == "Admin":
            return redirect('/adminDashboard')
        return redirect('/userDashboard')
    return render(request, 'index.html')


def signupView(request):
    if request.method == "POST":
        name = request.POST.get('firstName') + " " + request.POST.get('lastName')
        email = request.POST.get('email')
        password = request.POST.get('password')
        username = request.POST.get('username')
        token = str(uuid.uuid4())

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Your username is already taken')
            return redirect('/register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Your email is already taken')
            return redirect('/register')

        if not validateEmail(email) or not isRealEmail(email):
            messages.error(request, 'Invalid email')
            return redirect('/register')

        if sendMailAfterRegistration(email, token):
            userObj = User.objects.create(username=username, email=email)
            userObj.set_password(password)
            userObj.save()

            userInfoObj = userInfo.objects.create(user=userObj, name=name, email_verification_token=token)
            userInfoObj.save()
            messages.success(request, 'We have sent you an email for account verification.')
            return redirect('/register')
        else:
            return redirect('/register')
    return render(request, 'signup.html')


def accountVerification(request, token):
    userInfoObj = userInfo.objects.filter(email_verification_token=token).first()
    if userInfoObj:
        userInfoObj.is_email_verified = True
        userInfoObj.save()
        messages.success(request, 'Your account is registered successfully.')
        return redirect('/register')
    else:
        return redirect('/error')


def signinView(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        userObj = User.objects.filter(email=email).first()

        if userObj is None:
            messages.error(request, 'Your email address is not found.')
            return redirect('/signin')

        userInfoObj = userInfo.objects.filter(user=userObj).first()

        if not userInfoObj.is_email_verified:
            messages.error(request, 'Your email address is not verified. Kindly check your email.')
            return redirect('/signin')

        if userObj.check_password(password):
            login(request, userObj)
            if userObj.username == 'Admin':
                return redirect('/adminDashboard')
            return redirect('/userDashboard')
        else:
            messages.error(request, 'Your password is wrong.')
            return redirect('/signin')

    return render(request, 'signin.html')


def logoutView(request):
    logout(request)
    return redirect('/')


@login_required(login_url='/signin')
@user_passes_test(isAdmin, login_url='/error')
def adminDashboardView(request):
    total_users = userInfo.objects.exclude(user__username='Admin').count()
    premium_users = userInfo.objects.filter(is_premium_user=True).count()

    subscriptions = Subscription.objects.all()
    active_subscriptions = subscriptions.filter(subscription_end_date__gt=timezone.now()).count()
    expired_subscriptions = subscriptions.filter(subscription_end_date__lte=timezone.now()).count()

    recent_payment = Payment.objects.order_by('-payment_date').first()
    total_payments = Payment.objects.aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0

    total_reports = Report.objects.count()
    reports_this_month = Report.objects.filter(generated_at__month=timezone.now().month).count()

    # Handle the case where no payments have been made yet
    recent_payment_amount = recent_payment.payment_amount if recent_payment else 0

    context = {
        'total_users': total_users,
        'premium_users': premium_users,
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions,
        'recent_payment': recent_payment_amount,
        'total_payments': total_payments,
        'total_reports': total_reports,
        'reports_this_month': reports_this_month,
    }

    return render(request, 'adminDashboard.html', context)

@login_required(login_url='/signin')
def UpdatePasswordView(request):
    if request.method == 'POST':
        currentPassword = request.POST.get('currentPassword')
        newPassword = request.POST.get('newPassword')
        confirmPassword = request.POST.get('confirmPassword')
        userObj = User.objects.filter(email=request.user.email).first()

        if userObj.check_password(currentPassword):
            if newPassword == confirmPassword:
                userObj.set_password(newPassword)
                userObj.save()
                messages.success(request, "Your password is successfully updated")
                login(request, userObj)
                return redirect('/UpdatePassword')
            else:
                messages.error(request, "New and Confirm passwords are not matching")
                return redirect('/UpdatePassword')
        else:
            messages.error(request, "Current password is not matching")
            return redirect('/UpdatePassword')

    return render(request, 'updatePassword.html')


def errorPageView(request):
    return render(request, 'errorPage.html')


@user_passes_test(isUser, login_url='/error')
@login_required(login_url='/signin')
def userDashboardView(request):
    try:
        user_info = request.user.userinfo
        if user_info.is_premium_user:
            subscription = user_info.subscription
            if subscription.is_subscription_active():
                return render(request, 'userDashboard.html', userDashboardCalculations(subscription))
            else:
                user_info.is_premium_user = False
                user_info.save()
                messages.error(request, 'Your subscription has expired. Please renew to access premium features.')
                return render(request, 'subscription.html')
        else:
            return render(request, 'subscription.html')
    except userInfo.subscription.RelatedObjectDoesNotExist:
        messages.error(request, 'You do not have an active subscription. Please subscribe to access premium features.')
        return render(request, 'subscription.html')


@user_passes_test(isPremiumUser, login_url='/error')
@login_required(login_url='/signin')
def predictDiseaseView(request):
    return render(request, 'predictDisease.html');


def create_checkout_session(request, plan):
    if plan == 'monthly':
        price_id = "price_1Pvqk3ELppahqjfQ4XYbZHSN"
    elif plan == 'yearly':
        price_id = "price_1PvqkkELppahqjfQgBc3grGB"
    else:
        return redirect('/errorPage')

    try:
        user_info = userInfo.objects.get(user=request.user)
        if not user_info.stripe_customer_id:
            stripe_customer = stripe.Customer.create(email=request.user.email)
            user_info.stripe_customer_id = stripe_customer.id
            user_info.save()

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url="http://127.0.0.1:8000/userDashboard/",
            cancel_url="http://127.0.0.1:8000/userDashboard/",
            customer=user_info.stripe_customer_id,
            metadata={
                'plan': plan
            },
        )
        return redirect(checkout_session.url)
    except Exception as e:
        return JsonResponse({'error': str(e)})


stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

@csrf_exempt
def stripe_webhook(request):
    if request.method != 'POST':
        return HttpResponse("Invalid request method. Expected POST.", status=405)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return HttpResponse(f"Invalid payload: {e}", status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(f"Invalid signature: {e}", status=400)

    event_type = event['type']
    event_data = event['data']['object']

    if event_type == 'checkout.session.completed':
        handle_checkout_session_completed(event_data)
    elif event_type == 'invoice.payment_succeeded':
        handle_invoice_payment_succeeded(event_data)
    elif event_type == 'customer.subscription.created':
        handle_subscription_created(event_data)
    elif event_type == 'invoice.payment_failed':
        handle_invoice_payment_failed(event_data)

    return HttpResponse(status=200)


def handle_checkout_session_completed(session):
    print("\n\n\n")
    print(session.get('metadata', {}).get('plan'))
    print("\n\n\n")
    print(f"Checkout session completed: {session}")
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    user_info = userInfo.objects.filter(stripe_customer_id=customer_id).first()

    if user_info:
        subscription = Subscription.objects.filter(user_info=user_info).first()

        if subscription:
            subscription.stripe_subscription_id = subscription_id
            subscription.subscription_start_date = timezone.now()
            subscription.subscription_end_date = calculate_end_date(session.get('metadata', {}).get('plan'))
        else:
            subscription = Subscription(
                user_info=user_info,
                subscription_start_date=timezone.now(),
                stripe_subscription_id=subscription_id,
                subscription_end_date= calculate_end_date(session.get('metadata', {}).get('plan'))
                # subscription_end_date=subscription.calculate_end_date(session.get('metadata', {}).get('plan'))
            )


        subscription.save()
        user_info.is_premium_user = True
        user_info.save()
    else:
        print(f"No user found for Stripe customer ID: {customer_id}")


def handle_invoice_payment_succeeded(invoice):
    print(f"Invoice payment succeeded: {invoice}")
    subscription_id = invoice.get('subscription')
    payment_intent_id = invoice.get('payment_intent')
    subscription = Subscription.objects.filter(stripe_subscription_id=subscription_id).first()
    if subscription:
        Payment.objects.create(
            subscription=subscription,
            payment_status=True,
            payment_amount=invoice.get('amount_paid') / 100,
            payment_date=timezone.now(),
            stripe_payment_intent_id=payment_intent_id,
            transaction_id=invoice.get('id')
        )


def handle_subscription_created(subscription):
    print(f"Subscription created: {subscription}")
    customer_id = subscription.get('customer')
    user_info = userInfo.objects.filter(stripe_customer_id=customer_id).first()
    if user_info:
        user_info.is_premium_user = True
        user_info.save()


def handle_invoice_payment_failed(invoice):
    print(f"Invoice payment failed: {invoice}")
    subscription_id = invoice.get('subscription')
    subscription = Subscription.objects.filter(stripe_subscription_id=subscription_id).first()
    if subscription:
        subscription.payment_status = False
        subscription.save()
        user_info = subscription.user_info
        user_info.is_premium_user = False
        user_info.save()

