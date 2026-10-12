import logging
import urllib.parse
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import Booking, Payment
from .emails import send_customer_booking_confirmation, send_admin_notification

logger = logging.getLogger(__name__)


class UpiPaymentError(Exception):
    """Custom exception for UPI payment operations."""
    pass


def get_upi_config():
    """Retrieve configured UPI payee details from Django settings."""
    upi_id = getattr(settings, 'TOUR_UPI_ID', '').strip() or 'deluxtour@upi'
    payee_name = getattr(settings, 'TOUR_UPI_PAYEE_NAME', '').strip() or 'Delux Tour and Travel'
    note_prefix = getattr(settings, 'TOUR_UPI_NOTE_PREFIX', '').strip() or 'DeluxTour'
    return {
        'upi_id': upi_id,
        'payee_name': payee_name,
        'note_prefix': note_prefix,
        'currency': 'INR'
    }


def generate_upi_payment_link(upi_id, payee_name, amount, booking_reference):
    """
    Constructs a standard NPCI UPI payment deep link.
    Compatible with Google Pay, PhonePe, Paytm, BHIM, Cred, and all UPI mobile apps.
    """
    dec_amount = Decimal(str(amount))
    formatted_amount = f"{dec_amount:.2f}"
    ref_note = f"Booking {booking_reference or ''}".strip()

    params = {
        'pa': upi_id,
        'pn': payee_name,
        'am': formatted_amount,
        'cu': 'INR',
        'tn': ref_note
    }
    query_string = urllib.parse.urlencode(params)
    return f"upi://pay?{query_string}"


def generate_upi_qr_code_url(upi_payment_link):
    """Generates an image URL for scanning the UPI dynamic QR code."""
    encoded_uri = urllib.parse.quote(upi_payment_link, safe='')
    return f"https://api.qrserver.com/v1/create-qr-code/?size=260x260&margin=4&data={encoded_uri}"


def validate_utr_reference(utr_number, current_booking_id=None):
    """
    Validates the customer-provided UPI UTR/transaction reference.
    Prevents duplicates, empty strings, and malformed inputs.
    """
    cleaned = str(utr_number or '').strip().upper().replace(' ', '').replace('-', '')
    if not cleaned:
        raise UpiPaymentError("Please provide a valid UPI Transaction Reference / UTR Number.")

    if len(cleaned) < 6:
        raise UpiPaymentError("The UPI Reference / UTR number must be at least 6 characters.")

    if len(cleaned) > 50:
        raise UpiPaymentError("The UPI Reference / UTR number is too long.")

    # Check for duplicate UTR submissions across other bookings (excluding current booking)
    duplicate_qs = Booking.objects.filter(utr_number=cleaned)
    if current_booking_id:
        duplicate_qs = duplicate_qs.exclude(id=current_booking_id)

    # If already verified or currently pending verification on another booking
    if duplicate_qs.filter(payment_status__in=['PAID', 'PENDING_VERIFICATION', 'Paid']).exists():
        raise UpiPaymentError(
            f"The transaction reference '{cleaned}' has already been submitted for another booking. "
            "Please check your bank/UPI payment receipt."
        )

    return cleaned


def submit_upi_payment_verification(booking, utr_number, user=None, notes=None):
    """
    Marks the payment as PENDING_VERIFICATION upon customer submission.
    Does NOT mark the booking as paid automatically.
    """
    cleaned_utr = validate_utr_reference(utr_number, current_booking_id=booking.id)

    if booking.payment_status in ('PAID', 'Paid') and booking.status in ('CONFIRMED', 'Confirmed'):
        raise UpiPaymentError("This booking has already been verified and confirmed.")

    now = timezone.now()
    booking.utr_number = cleaned_utr
    booking.payment_status = 'PENDING_VERIFICATION'
    booking.status = 'PENDING'
    booking.payment_submitted_at = now
    if notes:
        existing_notes = booking.notes or ''
        booking.notes = f"{existing_notes}\n[UPI Note: {notes}]".strip()
    booking.save(update_fields=['utr_number', 'payment_status', 'status', 'payment_submitted_at', 'notes'])

    # Record or update Payment row
    payment = booking.payments.first()
    if not payment:
        payment = Payment.objects.create(
            booking=booking,
            user=user or booking.user,
            transaction_id=f"UPI-{cleaned_utr}-{booking.id}",
            utr_number=cleaned_utr,
            gateway='UPI',
            payment_method='UPI',
            amount=booking.total_amount or booking.package_price,
            currency=booking.currency or 'INR',
            status='PENDING_VERIFICATION'
        )
    else:
        payment.utr_number = cleaned_utr
        payment.status = 'PENDING_VERIFICATION'
        payment.payment_method = 'UPI'
        payment.save(update_fields=['utr_number', 'status', 'payment_method'])

    # Send notification email to admin for prompt verification
    html_body = f"""
    <h2>New UPI Payment Awaiting Verification</h2>
    <p><strong>Booking Ref:</strong> {booking.booking_reference}</p>
    <p><strong>Customer:</strong> {booking.full_name} ({booking.email})</p>
    <p><strong>Tour Package:</strong> {booking.package_title}</p>
    <p><strong>Payable Amount:</strong> ₹{booking.total_amount:,.2f}</p>
    <p><strong>Customer Submitted UTR:</strong> <code style="font-size:16px;background:#f3f4f6;padding:4px 8px;">{cleaned_utr}</code></p>
    <p><strong>Submitted At:</strong> {now.strftime('%d %B %Y, %I:%M %p')}</p>
    <p>Please cross-reference this UTR with your UPI/Bank statement before approving.</p>
    """
    send_admin_notification(
        f"Verify UPI Payment: {booking.booking_reference} (UTR: {cleaned_utr})",
        html_body
    )

    logger.info(f"Booking #{booking.id} ({booking.booking_reference}) marked PENDING_VERIFICATION with UTR: {cleaned_utr}")
    return booking, payment


def approve_upi_payment(booking, verified_by='admin'):
    """
    Authorized staff approval workflow:
    Confirms booking ONLY after staff verifies bank/UPI credit.
    """
    now = timezone.now()
    booking.payment_status = 'PAID'
    booking.status = 'CONFIRMED'
    booking.amount_paid = booking.total_amount or booking.package_price
    booking.verified_at = now
    booking.verified_by = verified_by or 'admin'
    booking.save(update_fields=['payment_status', 'status', 'amount_paid', 'verified_at', 'verified_by'])

    payment = booking.payments.first()
    if payment:
        payment.status = 'PAID'
        payment.verified_at = now
        payment.verified_by = verified_by or 'admin'
        payment.save(update_fields=['status', 'verified_at', 'verified_by'])

    # Send formal confirmation and GST Tax Invoice to the customer
    if not booking.confirmation_email_sent:
        send_customer_booking_confirmation(booking)
        booking.confirmation_email_sent = True
        booking.save(update_fields=['confirmation_email_sent'])

    logger.info(f"Booking #{booking.id} ({booking.booking_reference}) APPROVED by {verified_by}")
    return booking


def reject_upi_payment(booking, reason='', verified_by='admin'):
    """
    Authorized staff rejection workflow:
    Marks payment as REJECTED if no matching credit found or fake UTR submitted.
    """
    booking.payment_status = 'REJECTED'
    booking.status = 'REJECTED'
    booking.rejection_reason = reason or 'Transaction could not be matched with bank records.'
    booking.verified_by = verified_by or 'admin'
    booking.save(update_fields=['payment_status', 'status', 'rejection_reason', 'verified_by'])

    payment = booking.payments.first()
    if payment:
        payment.status = 'REJECTED'
        payment.error_description = booking.rejection_reason
        payment.verified_by = verified_by or 'admin'
        payment.save(update_fields=['status', 'error_description', 'verified_by'])

    logger.info(f"Booking #{booking.id} ({booking.booking_reference}) REJECTED by {verified_by}. Reason: {reason}")
    return booking
