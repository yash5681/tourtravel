import json
import csv
import hmac
import hashlib
import logging
import uuid
from decimal import Decimal
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils.html import escape
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from .models import Package, Booking, Payment, TripPlan, ContactMessage, CustomerUser
from .security import hash_password, verify_password
from .emails import send_admin_notification, send_customer_booking_confirmation, send_customer_plan_confirmation
from .upi_service import (
    UpiPaymentError,
    get_upi_config,
    generate_upi_payment_link,
    generate_upi_qr_code_url,
    validate_utr_reference,
    submit_upi_payment_verification,
    approve_upi_payment,
    reject_upi_payment,
)

logger = logging.getLogger(__name__)



def json_payload(request):
    """Safely parse JSON request body."""
    try:
        return json.loads(request.body.decode('utf-8'))
    except Exception:
        return {}


def is_admin(request):
    """Check if the current session has admin privileges."""
    return request.session.get('admin_logged_in') is True


# ============================================================
# CUSTOMER AUTH APIS
# ============================================================

@csrf_exempt
def api_register(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)

    data = json_payload(request)
    full_name = (data.get('fullName') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    confirm = data.get('confirm') or ''

    if not full_name or not email or not password:
        return JsonResponse({'message': 'Please fill all fields correctly.'}, status=400)

    if len(password) < 6:
        return JsonResponse({'message': 'Password must be at least 6 characters.'}, status=400)

    if password != confirm:
        return JsonResponse({'message': 'Passwords do not match.'}, status=400)

    if CustomerUser.objects.filter(email=email).exists():
        return JsonResponse({'message': 'An account with this email already exists.'}, status=400)

    pwd_hash, pwd_salt = hash_password(password)

    CustomerUser.objects.create(
        full_name=full_name,
        email=email,
        password_hash=pwd_hash,
        password_salt=pwd_salt
    )

    return JsonResponse({'message': 'Account created successfully.'}, status=200)


@csrf_exempt
def api_login(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)

    data = json_payload(request)
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    try:
        user = CustomerUser.objects.get(email=email)
    except CustomerUser.DoesNotExist:
        return JsonResponse({'message': 'Invalid email or password.'}, status=401)

    if not verify_password(password, user.password_hash, user.password_salt):
        return JsonResponse({'message': 'Invalid email or password.'}, status=401)

    # Set session
    request.session['customer_id'] = user.id
    request.session['customer_name'] = user.full_name
    request.session['customer_email'] = user.email

    return JsonResponse({
        'message': 'Login successful.',
        'name': user.full_name,
        'email': user.email
    }, status=200)


@csrf_exempt
def api_logout(request):
    request.session.pop('customer_id', None)
    request.session.pop('customer_name', None)
    request.session.pop('customer_email', None)
    return JsonResponse({'message': 'Logged out.'}, status=200)


def api_me(request):
    customer_id = request.session.get('customer_id')
    if customer_id:
        phone = ''
        try:
            u = CustomerUser.objects.get(id=customer_id)
            phone = u.phone or ''
        except Exception:
            pass
        return JsonResponse({
            'authenticated': True,
            'id': customer_id,
            'name': request.session.get('customer_name', ''),
            'email': request.session.get('customer_email', ''),
            'phone': phone
        })
    return JsonResponse({'authenticated': False})


def api_profile(request):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return JsonResponse({'message': 'Unauthorized. Please login.'}, status=401)

    try:
        user = CustomerUser.objects.get(id=customer_id)
    except CustomerUser.DoesNotExist:
        return JsonResponse({'message': 'User not found.'}, status=404)

    bookings = Booking.objects.filter(email__iexact=user.email).order_by('-created_at')
    plans = TripPlan.objects.filter(email__iexact=user.email).order_by('-created_at')

    # Calculate stats like Instagram
    destinations = set(b.package_title for b in bookings)

    return JsonResponse({
        'id': user.id,
        'fullName': user.full_name,
        'email': user.email,
        'phone': user.phone or '',
        'bio': user.bio or 'Passionate traveler exploring the world ✈️',
        'avatarUrl': user.avatar_url or 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80',
        'city': user.city or 'India',
        'joined': user.created_at.strftime('%B %Y'),
        'stats': {
            'bookingsCount': bookings.count(),
            'plansCount': plans.count(),
            'destinationsCount': len(destinations)
        },
        'bookings': [
            {
                'id': b.id,
                'bookingReference': b.booking_reference or f"DELUX-BK-{b.id:04d}",
                'packageTitle': b.package_title,
                'packagePrice': float(b.package_price),
                'totalAmount': float(b.total_amount or b.amount_paid or b.package_price),
                'amountPaid': float(b.amount_paid or 0),
                'currency': b.currency or 'INR',
                'paymentStatus': b.payment_status,
                'utrNumber': b.utr_number or '',
                'paymentSubmittedAt': b.payment_submitted_at.isoformat() if b.payment_submitted_at else None,
                'verifiedAt': b.verified_at.isoformat() if b.verified_at else None,
                'rejectionReason': b.rejection_reason or '',
                'travelMode': b.travel_mode,
                'travelers': b.travelers,
                'travelDate': b.travel_date.isoformat() if b.travel_date else None,
                'status': b.status,
                'canRetry': b.payment_status not in ('PAID', 'Paid'),
                'paymentUrl': f"/payment/upi/{b.id}/",
                'receiptUrl': f"/payment/success/{b.id}/",
                'createdAt': b.created_at.isoformat(),
                'imageUrl': b.package.image_url if b.package and b.package.image_url else 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=600&q=80'
            } for b in bookings
        ],
        'plans': [
            {
                'id': p.id,
                'destination': p.destination,
                'travelMode': p.travel_mode,
                'travelers': p.travelers,
                'budget': p.budget,
                'travelDate': p.travel_date.isoformat() if p.travel_date else None,
                'createdAt': p.created_at.isoformat()
            } for p in plans
        ]
    })


@csrf_exempt
def api_profile_update(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)

    customer_id = request.session.get('customer_id')
    if not customer_id:
        return JsonResponse({'message': 'Unauthorized. Please login.'}, status=401)

    try:
        user = CustomerUser.objects.get(id=customer_id)
    except CustomerUser.DoesNotExist:
        return JsonResponse({'message': 'User not found.'}, status=404)

    data = json_payload(request)
    full_name = (data.get('fullName') or '').strip()
    phone = (data.get('phone') or '').strip()
    bio = (data.get('bio') or '').strip()
    city = (data.get('city') or '').strip()
    avatar_url = (data.get('avatarUrl') or '').strip()

    if full_name:
        user.full_name = full_name
        request.session['customer_name'] = full_name
    if phone:
        user.phone = phone
    if bio:
        user.bio = bio
    if city:
        user.city = city
    if avatar_url:
        user.avatar_url = avatar_url

    user.save()

    return JsonResponse({
        'message': 'Profile updated successfully!',
        'fullName': user.full_name,
        'phone': user.phone,
        'bio': user.bio,
        'city': user.city,
        'avatarUrl': user.avatar_url
    })


# ============================================================
# PUBLIC FORMS & CATALOG APIS

# ============================================================

@csrf_exempt
def api_contact(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)

    data = json_payload(request)
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    subject = (data.get('subject') or '').strip()
    message = (data.get('message') or '').strip()

    if not name or not email or not subject or not message:
        return JsonResponse({'message': 'Please fill all fields correctly.'}, status=400)

    entry = ContactMessage.objects.create(
        name=name,
        email=email,
        subject=subject,
        message=message
    )

    # Email notification to admin
    html_body = f"""
    <h2>New Contact Message - Delux Tour & Travel</h2>
    <p><strong>Name:</strong> {escape(entry.name)}</p>
    <p><strong>Email:</strong> {escape(entry.email)}</p>
    <p><strong>Subject:</strong> {escape(entry.subject)}</p>
    <p><strong>Message:</strong><br>{escape(entry.message).replace(chr(10), '<br>')}</p>
    <p><small>Received: {timezone.localtime(entry.created_at).strftime('%d %b %Y, %I:%M %p')}</small></p>
    """
    send_admin_notification(f"New Contact Message from {entry.name}", html_body)

    return JsonResponse({'message': 'Thanks! Your message has been sent. We will get back to you soon.'})


@csrf_exempt
def api_plan(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)

    data = json_payload(request)
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    destination = (data.get('destination') or '').strip()
    date_str = data.get('date')
    travelers = (data.get('travelers') or '').strip()
    budget = (data.get('budget') or '').strip()
    travel_mode = (data.get('travelMode') or 'Flight').strip()
    message = (data.get('message') or '').strip()

    if not name or not email or not destination:
        return JsonResponse({'message': 'Please fill all required fields.'}, status=400)

    travel_date = None
    if date_str:
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
            try:
                travel_date = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                pass

    if travel_mode.lower() not in ('train', 'flight'):
        travel_mode = 'Flight'

    plan = TripPlan.objects.create(
        name=name,
        email=email,
        destination=destination,
        travel_date=travel_date,
        travelers=travelers,
        budget=budget,
        travel_mode=travel_mode,
        message=message
    )

    # Email notification to admin
    html_body = f"""
    <h2>New Custom Trip Plan Request - Delux Tour & Travel</h2>
    <p><strong>Traveler Name:</strong> {escape(plan.name)}</p>
    <p><strong>Email:</strong> {escape(plan.email)}</p>
    <p><strong>Destination:</strong> {escape(plan.destination)}</p>
    <p><strong>Travel Mode:</strong> {escape(plan.travel_mode)}</p>
    <p><strong>Travelers:</strong> {escape(plan.travelers or 'Not specified')}</p>
    <p><strong>Budget:</strong> {escape(plan.budget or 'Flexible')}</p>
    <p><strong>Preferred Date:</strong> {plan.travel_date.strftime('%d %b %Y') if plan.travel_date else 'Flexible'}</p>
    <p><strong>Notes:</strong> {escape(plan.message or 'None')}</p>
    """
    send_admin_notification(f"Custom Trip Request: {plan.destination} ({plan.travel_mode})", html_body)
    send_customer_plan_confirmation(plan)

    return JsonResponse({'message': 'Your trip request has been received! Our team will contact you soon.'})



def api_packages(request):
    packages = Package.objects.all()
    data = []
    for p in packages:
        data.append({
            'id': p.id,
            'title': p.title,
            'duration': p.duration,
            'location': p.location,
            'description': p.description,
            'price': float(p.price),
            'imageUrl': p.image_url,
            'featured': p.featured,
            'itinerary': p.itinerary,
            'inclusions': p.inclusions
        })
    return JsonResponse(data, safe=False)


@csrf_exempt
def api_upi_create_booking(request):
    """
    Creates a pending Booking and sets up the direct UPI Payment flow.
    Recalculates price on the server via Decimal; never trusts client-submitted amount.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Method not allowed'}, status=405)

    customer_id = request.session.get('customer_id')
    if not customer_id:
        return JsonResponse({
            'ok': False,
            'message': 'Please login to your account to book a tour package.',
            'requireLogin': True
        }, status=401)

    data = json_payload(request)
    package_id = data.get('packageId')
    full_name = (data.get('fullName') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()
    travelers_str = str(data.get('travelers') or '1').strip()
    travel_date_str = data.get('travelDate')
    travel_mode = (data.get('travelMode') or 'Flight').strip()
    notes = (data.get('notes') or '').strip()

    if not package_id or not full_name or not email or not phone:
        return JsonResponse({'ok': False, 'message': 'Please fill all required fields before proceeding to payment.'}, status=400)

    try:
        package = Package.objects.get(id=package_id)
    except Package.DoesNotExist:
        return JsonResponse({'ok': False, 'message': 'Selected package was not found.'}, status=404)

    # Parse traveler count safely
    try:
        if '-' in travelers_str:
            num_travelers = int(travelers_str.split('-')[0])
        elif '+' in travelers_str:
            num_travelers = int(travelers_str.replace('+', ''))
        else:
            num_travelers = int(travelers_str)
    except Exception:
        num_travelers = 1

    if num_travelers < 1:
        num_travelers = 1

    # Server-side Decimal calculation
    unit_price = Decimal(str(package.price))
    total_amount = unit_price * Decimal(num_travelers)
    currency = 'INR'

    travel_date = None
    if travel_date_str:
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
            try:
                travel_date = datetime.strptime(travel_date_str, fmt).date()
                break
            except ValueError:
                pass

    if travel_mode.lower() not in ('train', 'flight'):
        travel_mode = 'Flight'

    user = CustomerUser.objects.filter(id=customer_id).first()

    with transaction.atomic():
        booking = Booking.objects.create(
            user=user,
            package=package,
            package_title=package.title,
            package_price=unit_price,
            total_amount=total_amount,
            amount_paid=Decimal('0.00'),
            currency=currency,
            full_name=full_name,
            email=email,
            phone=phone,
            travel_mode=travel_mode,
            travelers=str(num_travelers),
            travel_date=travel_date,
            notes=notes,
            status='PENDING',
            payment_status='PENDING'
        )

        txn_id = f"TXN-UPI-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

        Payment.objects.create(
            booking=booking,
            user=user,
            transaction_id=txn_id,
            gateway='UPI',
            payment_method='UPI',
            amount=total_amount,
            currency=currency,
            status='PENDING'
        )

    upi_config = get_upi_config()
    upi_id = upi_config['upi_id']
    payee_name = upi_config['payee_name']
    upi_link = generate_upi_payment_link(
        upi_id=upi_id,
        payee_name=payee_name,
        amount=total_amount,
        booking_reference=booking.booking_reference
    )
    qr_url = generate_upi_qr_code_url(upi_link)

    return JsonResponse({
        'ok': True,
        'message': 'Booking initialized. Proceed to UPI payment.',
        'bookingId': booking.id,
        'bookingReference': booking.booking_reference,
        'redirectUrl': f'/payment/upi/{booking.id}/',
        'packageId': package.id,
        'packageTitle': package.title,
        'packagePrice': float(unit_price),
        'numTravelers': num_travelers,
        'totalAmount': float(total_amount),
        'currency': currency,
        'upiId': upi_id,
        'payeeName': payee_name,
        'upiLink': upi_link,
        'qrCodeUrl': qr_url,
        'fullName': full_name,
        'email': email,
        'phone': phone
    })


@csrf_exempt
def api_upi_submit_utr(request):
    """
    Submits UPI transaction reference / UTR for customer payment verification.
    Sets status to PENDING_VERIFICATION. Never auto-marks as paid.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Method not allowed'}, status=405)

    customer_id = request.session.get('customer_id')
    data = json_payload(request)
    booking_id = data.get('bookingId')
    utr_number = data.get('utrNumber')
    notes = data.get('notes')

    if not booking_id or not utr_number:
        return JsonResponse({
            'ok': False,
            'message': 'Booking ID and UPI Reference / UTR Number are required.'
        }, status=400)

    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'ok': False, 'message': 'Booking record not found.'}, status=404)

    # Permission check: booking belongs to logged in user or admin
    if customer_id and booking.user_id and booking.user_id != customer_id and not is_admin(request):
        return JsonResponse({'ok': False, 'message': 'Unauthorized access to this booking.'}, status=403)

    try:
        user = CustomerUser.objects.filter(id=customer_id).first() if customer_id else booking.user
        submit_upi_payment_verification(booking=booking, utr_number=utr_number, user=user, notes=notes)
        return JsonResponse({
            'ok': True,
            'message': 'UPI payment details submitted successfully. Our accounts team will verify and confirm your booking.',
            'bookingId': booking.id,
            'bookingReference': booking.booking_reference,
            'utrNumber': booking.utr_number,
            'status': booking.status,
            'paymentStatus': booking.payment_status,
            'redirectUrl': f'/payment/pending/{booking.id}/'
        })
    except UpiPaymentError as err:
        return JsonResponse({'ok': False, 'message': str(err)}, status=400)


@csrf_exempt
def api_payment_retry(request, booking_id):
    """
    Allows a customer to retry or reopen UPI payment for a pending or rejected booking.
    """
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'ok': False, 'message': 'Booking not found.'}, status=404)

    customer_id = request.session.get('customer_id')
    if customer_id and booking.user_id and booking.user_id != customer_id and not is_admin(request):
        return JsonResponse({'ok': False, 'message': 'Permission denied.'}, status=403)

    if booking.payment_status in ('PAID', 'Paid') and booking.status in ('CONFIRMED', 'Confirmed'):
        return JsonResponse({
            'ok': True,
            'message': 'This booking is already paid and confirmed.',
            'redirectUrl': f'/payment/success/{booking.id}/'
        })

    return JsonResponse({
        'ok': True,
        'bookingId': booking.id,
        'bookingReference': booking.booking_reference,
        'redirectUrl': f'/payment/upi/{booking.id}/'
    })


def api_payment_status(request, booking_id):
    """
    Returns live payment and booking status for customer verification screen.
    """
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'ok': False, 'message': 'Booking not found.'}, status=404)

    customer_id = request.session.get('customer_id')
    if customer_id and booking.user_id and booking.user_id != customer_id and not is_admin(request):
        return JsonResponse({'ok': False, 'message': 'Permission denied.'}, status=403)

    payments = [
        {
            'transactionId': p.transaction_id,
            'utrNumber': p.utr_number or '',
            'amount': float(p.amount),
            'status': p.status,
            'paymentMethod': p.payment_method,
            'createdAt': p.created_at.isoformat()
        }
        for p in booking.payments.all()
    ]

    return JsonResponse({
        'ok': True,
        'bookingId': booking.id,
        'bookingReference': booking.booking_reference,
        'packageTitle': booking.package_title,
        'status': booking.status,
        'paymentStatus': booking.payment_status,
        'utrNumber': booking.utr_number or '',
        'amountPaid': float(booking.amount_paid),
        'totalAmount': float(booking.total_amount or booking.package_price),
        'currency': booking.currency,
        'verifiedAt': booking.verified_at.isoformat() if booking.verified_at else None,
        'verifiedBy': booking.verified_by or '',
        'rejectionReason': booking.rejection_reason or '',
        'canRetry': booking.payment_status not in ('PAID', 'Paid'),
        'payments': payments
    })


@csrf_exempt
def api_admin_booking_approve_upi(request, booking_id):
    """
    Admin-only: Approves UPI payment, confirms booking, and dispatches Tax Invoice email.
    """
    if not is_admin(request):
        return JsonResponse({'ok': False, 'message': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Method not allowed'}, status=405)

    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'ok': False, 'message': 'Booking not found.'}, status=404)

    admin_email = request.session.get('admin_email', 'admin')
    approve_upi_payment(booking, verified_by=admin_email)

    return JsonResponse({
        'ok': True,
        'message': f"Booking #{booking.id} ({booking.booking_reference}) approved and confirmed! Tax invoice dispatched to {booking.email}.",
        'bookingId': booking.id,
        'status': booking.status,
        'paymentStatus': booking.payment_status,
        'verifiedAt': booking.verified_at.isoformat() if booking.verified_at else None,
        'verifiedBy': booking.verified_by
    })


@csrf_exempt
def api_admin_booking_reject_upi(request, booking_id):
    """
    Admin-only: Rejects UPI payment if no matching credit found or fake UTR submitted.
    """
    if not is_admin(request):
        return JsonResponse({'ok': False, 'message': 'Unauthorized'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Method not allowed'}, status=405)

    data = json_payload(request)
    reason = (data.get('reason') or 'UTR reference could not be matched with bank statements.').strip()

    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'ok': False, 'message': 'Booking not found.'}, status=404)

    admin_email = request.session.get('admin_email', 'admin')
    reject_upi_payment(booking, reason=reason, verified_by=admin_email)

    return JsonResponse({
        'ok': True,
        'message': f"Booking #{booking.id} ({booking.booking_reference}) payment rejected.",
        'bookingId': booking.id,
        'status': booking.status,
        'paymentStatus': booking.payment_status,
        'rejectionReason': booking.rejection_reason
    })


@csrf_exempt
def api_upi_demo_verify(request, booking_id):
    """
    College Presentation / Academic Demonstration Mode:
    Simulates instant verification and immediately dispatches the official
    GST Tax Invoice & Booking Confirmation email to the customer's email address.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'message': 'Method not allowed'}, status=405)

    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'ok': False, 'message': 'Booking not found.'}, status=404)

    customer_id = request.session.get('customer_id')
    if customer_id and booking.user_id and booking.user_id != customer_id and not is_admin(request):
        return JsonResponse({'ok': False, 'message': 'Permission denied.'}, status=403)

    # Set demo UTR reference if none exists
    if not booking.utr_number:
        booking.utr_number = f"DEMO-CLG-{uuid.uuid4().hex[:6].upper()}"
        booking.save(update_fields=['utr_number'])

    # Approve UPI payment and dispatch formal confirmation with GST Tax Invoice
    approve_upi_payment(booking, verified_by='College Presentation Demo')

    return JsonResponse({
        'ok': True,
        'message': f"College Demo Payment Verified! Official Tax Invoice email dispatched to {booking.email}.",
        'bookingId': booking.id,
        'bookingReference': booking.booking_reference,
        'utrNumber': booking.utr_number,
        'status': booking.status,
        'paymentStatus': booking.payment_status,
        'redirectUrl': f'/payment/success/{booking.id}/'
    })



@csrf_exempt
def api_bookings(request):
    """
    Instructs API clients that tour bookings are created via UPI payment flow.
    """
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)

    return JsonResponse({
        'message': 'Please initiate bookings via the UPI booking endpoint (/api/upi/create-booking).',
        'requiresUpi': True
    }, status=400)




# ============================================================
# NEW FEATURE: CUSTOMER PERSONAL DASHBOARD / MY BOOKINGS
# ============================================================

def api_my_bookings(request):
    customer_email = request.session.get('customer_email')
    if not customer_email:
        return JsonResponse({'message': 'Please log in to view your bookings.'}, status=401)

    bookings = Booking.objects.filter(email__iexact=customer_email).order_by('-created_at')
    plans = TripPlan.objects.filter(email__iexact=customer_email).order_by('-created_at')

    return JsonResponse({
        'bookings': [
            {
                'id': b.id,
                'bookingReference': b.booking_reference or f"DELUX-BK-{b.id:04d}",
                'packageTitle': b.package_title,
                'packagePrice': float(b.package_price),
                'totalAmount': float(b.total_amount or b.amount_paid or b.package_price),
                'amountPaid': float(b.amount_paid or 0),
                'currency': b.currency or 'INR',
                'paymentStatus': b.payment_status,
                'utrNumber': b.utr_number or '',
                'paymentSubmittedAt': b.payment_submitted_at.isoformat() if b.payment_submitted_at else None,
                'verifiedAt': b.verified_at.isoformat() if b.verified_at else None,
                'rejectionReason': b.rejection_reason or '',
                'travelMode': b.travel_mode,
                'travelers': b.travelers,
                'travelDate': b.travel_date.isoformat() if b.travel_date else None,
                'status': b.status,
                'canRetry': b.payment_status not in ('PAID', 'Paid'),
                'paymentUrl': f"/payment/upi/{b.id}/",
                'receiptUrl': f"/payment/success/{b.id}/",
                'createdAt': b.created_at.isoformat(),
                'imageUrl': b.package.image_url if b.package and b.package.image_url else 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=600&q=80'
            } for b in bookings
        ],
        'plans': [
            {
                'id': p.id,
                'destination': p.destination,
                'travelMode': p.travel_mode,
                'travelers': p.travelers,
                'budget': p.budget,
                'travelDate': p.travel_date.isoformat() if p.travel_date else None,
                'createdAt': p.created_at.isoformat()
            } for p in plans
        ]
    })


# ============================================================
# ADMIN APIS
# ============================================================

@csrf_exempt
def api_admin_login(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)

    data = json_payload(request)
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    configured = getattr(settings, 'ADMIN_CREDENTIALS', {})
    valid_email = configured.get('email', 'admin@deluxtour.com')
    valid_password = configured.get('password', 'Admin@123')

    if email.lower() == valid_email.lower() and password == valid_password:
        request.session['admin_logged_in'] = True
        request.session['admin_email'] = email
        return JsonResponse({'message': 'Welcome back, Admin.'})

    return JsonResponse({'message': 'Invalid admin email or password.'}, status=401)


@csrf_exempt
def api_admin_logout(request):
    request.session.pop('admin_logged_in', None)
    request.session.pop('admin_email', None)
    return JsonResponse({'message': 'Logged out.'})


def api_admin_me(request):
    if is_admin(request):
        return JsonResponse({
            'authenticated': True,
            'email': request.session.get('admin_email', 'admin@deluxtour.com')
        })
    return JsonResponse({'authenticated': False})


def api_admin_summary(request):
    if not is_admin(request):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status__in=['Pending', 'PENDING']).count()
    pending_verifications = Booking.objects.filter(payment_status='PENDING_VERIFICATION').count()
    total_plans = TripPlan.objects.count()
    total_contacts = ContactMessage.objects.count()
    total_users = CustomerUser.objects.count()
    train_bookings = Booking.objects.filter(travel_mode='Train').count()
    flight_bookings = Booking.objects.filter(travel_mode='Flight').count()
    total_packages = Package.objects.count()

    return JsonResponse({
        'totalBookings': total_bookings,
        'pendingBookings': pending_bookings,
        'pendingVerifications': pending_verifications,
        'totalTripPlans': total_plans,
        'totalContacts': total_contacts,
        'totalUsers': total_users,
        'trainBookings': train_bookings,
        'flightBookings': flight_bookings,
        'totalPackages': total_packages
    })


def api_admin_bookings(request):
    if not is_admin(request):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    bookings = Booking.objects.all().order_by('-created_at')
    result = []
    for b in bookings:
        result.append({
            'id': b.id,
            'bookingReference': b.booking_reference or f"DELUX-BK-{b.id:04d}",
            'packageId': b.package_id,
            'packageTitle': b.package_title,
            'packagePrice': float(b.package_price),
            'totalAmount': float(b.total_amount or b.amount_paid or b.package_price),
            'currency': b.currency or 'INR',
            'fullName': b.full_name,
            'email': b.email,
            'phone': b.phone,
            'travelMode': b.travel_mode,
            'travelers': b.travelers,
            'travelDate': b.travel_date.isoformat() if b.travel_date else None,
            'notes': b.notes,
            'status': b.status,
            'paymentStatus': b.payment_status,
            'utrNumber': b.utr_number or '',
            'paymentSubmittedAt': b.payment_submitted_at.isoformat() if b.payment_submitted_at else None,
            'verifiedAt': b.verified_at.isoformat() if b.verified_at else None,
            'verifiedBy': b.verified_by or '',
            'rejectionReason': b.rejection_reason or '',
            'amountPaid': float(b.amount_paid or 0),
            'canApprove': b.payment_status in ('PENDING_VERIFICATION', 'PENDING'),
            'canReject': b.payment_status in ('PENDING_VERIFICATION', 'PENDING'),
            'createdAt': b.created_at.isoformat()
        })
    return JsonResponse(result, safe=False)


@csrf_exempt
def api_admin_booking_status(request, booking_id):
    if not is_admin(request):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    if request.method not in ('POST', 'PUT'):
        return JsonResponse({'message': 'Method not allowed'}, status=405)

    data = json_payload(request)
    new_status = data.get('status')
    if new_status not in ('Pending', 'Confirmed', 'Cancelled'):
        return JsonResponse({'message': 'Status must be Pending, Confirmed or Cancelled.'}, status=400)

    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'message': 'Booking not found.'}, status=404)

    booking.status = new_status
    booking.save(update_fields=['status'])

    return JsonResponse({'message': 'Booking status updated.'})


def api_admin_plans(request):
    if not is_admin(request):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    plans = TripPlan.objects.all().order_by('-created_at')
    result = []
    for p in plans:
        result.append({
            'id': p.id,
            'name': p.name,
            'email': p.email,
            'destination': p.destination,
            'travelDate': p.travel_date.isoformat() if p.travel_date else None,
            'travelers': p.travelers,
            'budget': p.budget,
            'travelMode': p.travel_mode,
            'message': p.message,
            'createdAt': p.created_at.isoformat()
        })
    return JsonResponse(result, safe=False)


def api_admin_contacts(request):
    if not is_admin(request):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    contacts = ContactMessage.objects.all().order_by('-created_at')
    result = []
    for c in contacts:
        result.append({
            'id': c.id,
            'name': c.name,
            'email': c.email,
            'subject': c.subject,
            'message': c.message,
            'createdAt': c.created_at.isoformat()
        })
    return JsonResponse(result, safe=False)


def api_admin_users(request):
    if not is_admin(request):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    users = CustomerUser.objects.all().order_by('-created_at')
    result = []
    for u in users:
        result.append({
            'id': u.id,
            'fullName': u.full_name,
            'email': u.email,
            'createdAt': u.created_at.isoformat()
        })
    return JsonResponse(result, safe=False)


# ============================================================
# NEW FEATURE: ADMIN PACKAGE MANAGEMENT (CRUD)
# ============================================================

@csrf_exempt
def api_admin_packages(request):
    if not is_admin(request):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    if request.method in ('POST', 'PUT'):
        data = json_payload(request)
        pkg_id = data.get('id')
        title = (data.get('title') or '').strip()
        duration = (data.get('duration') or '').strip()
        location = (data.get('location') or '').strip()
        description = (data.get('description') or '').strip()
        price = data.get('price') or 0
        image_url = (data.get('imageUrl') or '').strip()
        itinerary = (data.get('itinerary') or '').strip()
        inclusions = (data.get('inclusions') or '').strip()

        if not title or not duration or not location or not price:
            return JsonResponse({'message': 'Title, duration, location, and price are required.'}, status=400)

        if pkg_id:
            try:
                pkg = Package.objects.get(id=pkg_id)
                pkg.title = title
                pkg.duration = duration
                pkg.location = location
                pkg.description = description
                pkg.price = price
                pkg.image_url = image_url
                pkg.itinerary = itinerary
                pkg.inclusions = inclusions
                pkg.save()
                return JsonResponse({'message': 'Package updated successfully!', 'id': pkg.id})
            except Package.DoesNotExist:
                return JsonResponse({'message': 'Package not found.'}, status=404)

        pkg = Package.objects.create(
            title=title,
            duration=duration,
            location=location,
            description=description,
            price=price,
            image_url=image_url,
            itinerary=itinerary,
            inclusions=inclusions
        )
        return JsonResponse({'message': 'Package created successfully!', 'id': pkg.id})

    elif request.method == 'DELETE':
        data = json_payload(request)
        pkg_id = data.get('id') or request.GET.get('id')
        if not pkg_id:
            return JsonResponse({'message': 'Package ID is required.'}, status=400)
        try:
            pkg = Package.objects.get(id=pkg_id)
            pkg.delete()
            return JsonResponse({'message': 'Package deleted successfully.'})
        except Package.DoesNotExist:
            return JsonResponse({'message': 'Package not found.'}, status=404)

    return JsonResponse({'message': 'Method not allowed'}, status=405)


# ============================================================
# NEW FEATURE: EXPORT BOOKINGS TO CSV
# ============================================================

def api_admin_export_bookings(request):
    if not is_admin(request):
        return JsonResponse({'message': 'Unauthorized'}, status=401)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f"delux_bookings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Write UTF-8 BOM so Excel opens with proper encoding
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow([
        'Booking ID', 'Booking Reference', 'Created At', 'Package Title', 'Package Price (INR)',
        'Total Amount (INR)', 'Amount Paid (INR)', 'Customer Name', 'Email', 'Phone', 'Travel Mode',
        'Travelers', 'Travel Date', 'Status', 'Payment Status',
        'UPI Reference / UTR', 'Verified By', 'Verified At', 'Rejection Reason', 'Notes'
    ])

    for b in Booking.objects.all().order_by('-created_at'):
        writer.writerow([
            b.id,
            b.booking_reference or f"DELUX-BK-{b.id:04d}",
            b.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            b.package_title,
            b.package_price,
            b.total_amount or b.amount_paid or b.package_price,
            b.amount_paid or 0,
            b.full_name,
            b.email,
            b.phone,
            b.travel_mode,
            b.travelers,
            b.travel_date.strftime('%Y-%m-%d') if b.travel_date else 'Flexible',
            b.status,
            b.payment_status,
            b.utr_number or '',
            b.verified_by or '',
            b.verified_at.strftime('%Y-%m-%d %H:%M:%S') if b.verified_at else '',
            b.rejection_reason or '',
            b.notes or ''
        ])

    return response
