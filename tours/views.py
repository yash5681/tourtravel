from django.shortcuts import render, redirect


def index_view(request):
    return render(request, 'index.html')


def about_view(request):
    return render(request, 'about.html')


def packages_view(request):
    return render(request, 'packages.html')


def book_view(request):
    if not request.session.get('customer_id'):
        package_id = request.GET.get('packageId', '')
        if package_id:
            return redirect(f'/login.html?next=book.html%3FpackageId%3D{package_id}')
        return redirect('/login.html?next=book.html')
    return render(request, 'book.html')


def plan_view(request):
    return render(request, 'plan.html')


def gallery_view(request):
    return render(request, 'gallery.html')


def contact_view(request):
    return render(request, 'contact.html')


def login_view(request):
    return render(request, 'login.html')


def register_view(request):
    return render(request, 'register.html')


def admin_login_view(request):
    return render(request, 'admin-login.html')


def admin_dashboard_view(request):
    if not request.session.get('admin_logged_in') and not request.session.get('admin_id') and not request.session.get('is_admin'):
        return redirect('/admin-login.html')
    return render(request, 'admin.html')


def profile_view(request):
    if not request.session.get('customer_id'):
        return redirect('/login.html?next=profile.html')
    return render(request, 'profile.html')


def payment_success_view(request, booking_id):
    from .models import Booking
    from django.shortcuts import get_object_or_404
    booking = get_object_or_404(Booking, id=booking_id)
    latest_payment = booking.payments.filter(status='Paid').first() or booking.payments.first()
    context = {
        'booking': booking,
        'payment': latest_payment,
        'invoice_no': f"INV-{booking.booking_reference}" if booking.booking_reference else f"INV-2026-DELUX-{booking.id:04d}",
    }
    return render(request, 'payment_success.html', context)


def payment_failed_view(request, booking_id):
    from .models import Booking
    from django.shortcuts import get_object_or_404
    booking = get_object_or_404(Booking, id=booking_id)
    latest_payment = booking.payments.filter(status='Failed').first() or booking.payments.first()
    context = {
        'booking': booking,
        'payment': latest_payment,
    }
    return render(request, 'payment_failed.html', context)


def payment_pending_view(request, booking_id):
    from .models import Booking
    from django.shortcuts import get_object_or_404
    booking = get_object_or_404(Booking, id=booking_id)
    latest_payment = booking.payments.first()
    context = {
        'booking': booking,
        'payment': latest_payment,
    }
    return render(request, 'payment_pending.html', context)


def payment_retry_view(request, booking_id):
    from .models import Booking
    from django.shortcuts import get_object_or_404
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.status in ('Confirmed', 'CONFIRMED') and booking.payment_status in ('Paid', 'PAID'):
        return redirect(f'/payment/success/{booking.id}/')
    return redirect(f'/payment/upi/{booking.id}/')


def payment_upi_view(request, booking_id):
    from .models import Booking
    from django.shortcuts import get_object_or_404
    from .upi_service import get_upi_config, generate_upi_payment_link, generate_upi_qr_code_url

    booking = get_object_or_404(Booking, id=booking_id)

    # Ownership check: if logged in customer, verify ownership unless admin
    customer_id = request.session.get('customer_id')
    is_admin_user = request.session.get('admin_logged_in') or request.session.get('is_admin')
    if customer_id and booking.user_id and booking.user_id != customer_id and not is_admin_user:
        return redirect('/profile.html')

    # If already confirmed and paid, redirect to success
    if booking.status in ('Confirmed', 'CONFIRMED') and booking.payment_status in ('Paid', 'PAID'):
        return redirect(f'/payment/success/{booking.id}/')

    upi_config = get_upi_config()
    upi_id = upi_config['upi_id']
    payee_name = upi_config['payee_name']
    amount = booking.total_amount or booking.package_price

    upi_link = generate_upi_payment_link(
        upi_id=upi_id,
        payee_name=payee_name,
        amount=amount,
        booking_reference=booking.booking_reference
    )
    qr_url = generate_upi_qr_code_url(upi_link)

    context = {
        'booking': booking,
        'booking_reference': booking.booking_reference or f"DELUX-BK-{booking.id:04d}",
        'amount': amount,
        'upi_id': upi_id,
        'payee_name': payee_name,
        'upi_link': upi_link,
        'qr_url': qr_url,
    }
    return render(request, 'payment_upi.html', context)



