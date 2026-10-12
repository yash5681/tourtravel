import logging
import threading
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _send_in_background(msg, log_success, log_fail):
    """Dispatches email sending in a background thread so views return instantly."""
    def worker():
        try:
            msg.send(fail_silently=False)
            logger.info(log_success)
        except Exception as e:
            logger.warning(f"{log_fail}: {e}")

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


def send_admin_notification(subject, html_content):
    """
    Sends an HTML notification email to the admin asynchronously.
    Fails silently in background so user actions are never delayed or blocked.
    """
    try:
        to_email = getattr(settings, 'ADMIN_NOTIFY_EMAIL', 'yashprajapati5681@gmail.com')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'pyash7571@gmail.com')
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(
            subject=f"[Delux Tour & Travel] {subject}",
            body=text_content,
            from_email=from_email,
            to=[to_email]
        )
        msg.attach_alternative(html_content, "text/html")
        _send_in_background(
            msg,
            f"Admin notification email successfully sent to {to_email}: {subject}",
            "Failed to send admin email notification"
        )
        return True
    except Exception as e:
        logger.warning(f"Failed to queue admin email notification: {e}")
        return False


def send_customer_booking_confirmation(booking):
    """
    Sends a confirmation email directly to the customer when they book a package.
    """
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'pyash7571@gmail.com')
        to_email = booking.email
        subject = f"🧾 Tax Invoice & Booking Confirmation #{booking.id}: {booking.package_title} [PAID]"

        date_str = booking.travel_date.strftime('%d %B %Y') if booking.travel_date else 'Flexible / To be confirmed'
        created_str = booking.created_at.strftime('%d %B %Y, %I:%M %p')
        total_paid = float(booking.amount_paid or booking.package_price)
        base_fare = total_paid * 0.95
        gst_amount = total_paid * 0.05
        invoice_no = f"INV-{booking.booking_reference}" if booking.booking_reference else f"INV-2026-DELUX-{booking.id:04d}"

        html_content = f"""
        <div style="font-family: Montserrat, Arial, sans-serif; max-width: 660px; margin: 0 auto; background: #ffffff; border: 1px solid #dcd7cb; border-radius: 10px; overflow: hidden; color: #17201d; box-shadow: 0 4px 20px rgba(0,0,0,0.06);">
            <!-- Invoice Header -->
            <div style="background: #0c2340; padding: 26px 32px; color: #ffffff; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1 style="margin: 0; font-size: 22px; letter-spacing: 1.5px; color: #fce6a4; font-family: 'Playfair Display', Georgia, serif;">✦ DELUX TOUR &amp; TRAVEL</h1>
                    <p style="margin: 4px 0 0; font-size: 11px; color: #8da4be; letter-spacing: 1px;">OFFICIAL GST TAX INVOICE &amp; TRAVEL VOUCHER</p>
                </div>
                <div style="text-align: right;">
                    <span style="background: #16a34a; color: #fff; font-size: 11px; font-weight: bold; padding: 4px 10px; border-radius: 12px; display: inline-block;">✓ PAID ONLINE</span>
                </div>
            </div>

            <!-- Invoice Meta Info Grid -->
            <div style="padding: 24px 32px; background: #fbfaf7; border-bottom: 1px solid #eee8dc;">
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <tr>
                        <td style="width: 50%; vertical-align: top;">
                            <strong style="color: #666; font-size: 11px; text-transform: uppercase;">Billed To (Customer Details):</strong>
                            <p style="margin: 4px 0; font-size: 15px; font-weight: bold; color: #17201d;">{booking.full_name}</p>
                            <p style="margin: 2px 0; color: #555;">Email: <u>{booking.email}</u></p>
                            <p style="margin: 2px 0; color: #555;">Mobile: {booking.phone}</p>
                        </td>
                        <td style="width: 50%; vertical-align: top; text-align: right;">
                            <strong style="color: #666; font-size: 11px; text-transform: uppercase;">Invoice Details:</strong>
                            <p style="margin: 4px 0; font-size: 14px; font-weight: bold; color: #b48738;">Invoice No: {invoice_no}</p>
                            <p style="margin: 2px 0; color: #555;">Date: {created_str}</p>
                            <p style="margin: 2px 0; color: #555;">Booking ID: <strong>#{booking.id}</strong></p>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- Payment Authorization Details -->
            <div style="padding: 18px 32px; background: #f0fdf4; border-bottom: 1px solid #bbf7d0;">
                <table style="width: 100%; border-collapse: collapse; font-size: 12px; color: #166534;">
                    <tr>
                        <td><strong>Payment Mode:</strong> Verified Direct UPI Payment</td>
                        <td style="text-align: right;"><strong>UPI Ref / UTR:</strong> <code style="background:#dcfce7;padding:2px 6px;border-radius:4px;font-family:monospace">{booking.utr_number or booking.razorpay_payment_id or 'Verified by Accounts'}</code></td>
                    </tr>
                </table>
            </div>

            <!-- Itemized Fare & Services Table -->
            <div style="padding: 24px 32px;">
                <h3 style="margin: 0 0 14px; font-size: 15px; color: #17201d; text-transform: uppercase; letter-spacing: 0.5px;">Booked Tour Package Details</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <thead>
                        <tr style="background: #f4f0e6; color: #17201d; text-align: left;">
                            <th style="padding: 10px 12px; border: 1px solid #e0dacf;">Item Description</th>
                            <th style="padding: 10px 12px; border: 1px solid #e0dacf;">Travel Mode</th>
                            <th style="padding: 10px 12px; border: 1px solid #e0dacf; text-align: center;">Travelers</th>
                            <th style="padding: 10px 12px; border: 1px solid #e0dacf; text-align: right;">Rate / Person</th>
                            <th style="padding: 10px 12px; border: 1px solid #e0dacf; text-align: right;">Amount (INR)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 12px; border: 1px solid #e0dacf;">
                                <strong>{booking.package_title}</strong><br>
                                <small style="color: #666;">Travel Date: {date_str}</small>
                            </td>
                            <td style="padding: 12px; border: 1px solid #e0dacf;">{booking.travel_mode}</td>
                            <td style="padding: 12px; border: 1px solid #e0dacf; text-align: center;">{booking.travelers}</td>
                            <td style="padding: 12px; border: 1px solid #e0dacf; text-align: right;">₹{float(booking.package_price):,.2f}</td>
                            <td style="padding: 12px; border: 1px solid #e0dacf; text-align: right; font-weight: bold;">₹{total_paid:,.2f}</td>
                        </tr>
                    </tbody>
                </table>

                <!-- Summary & Tax Calculation -->
                <div style="margin-top: 18px; display: flex; justify-content: flex-end;">
                    <table style="width: 280px; border-collapse: collapse; font-size: 13px; margin-left: auto;">
                        <tr>
                            <td style="padding: 6px 0; color: #666;">Taxable Base Fare:</td>
                            <td style="padding: 6px 0; text-align: right; font-weight: bold;">₹{base_fare:,.2f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #666;">GST &amp; Tourism Taxes (5%):</td>
                            <td style="padding: 6px 0; text-align: right; font-weight: bold; color: #27ae60;">₹{gst_amount:,.2f}</td>
                        </tr>
                        <tr style="border-top: 2px solid #0c2340; border-bottom: 2px solid #0c2340;">
                            <td style="padding: 10px 0; font-size: 15px; font-weight: bold; color: #0c2340;">Total Paid:</td>
                            <td style="padding: 10px 0; text-align: right; font-size: 16px; font-weight: bold; color: #b48738;">₹{total_paid:,.2f}</td>
                        </tr>
                    </table>
                </div>

                <!-- Next Steps / Customer Notice -->
                <div style="margin-top: 24px; background: #fdfaf3; border-left: 4px solid #b48738; padding: 14px 18px; border-radius: 4px;">
                    <p style="margin: 0; font-size: 13px; color: #66522b; line-height: 1.5;">
                        <strong>Travel Itinerary Voucher:</strong> Our travel concierge will reach out to you directly on <strong>{booking.phone}</strong> or WhatsApp to confirm your hotel voucher, flight/train tickets, and pickup schedule.
                    </p>
                </div>
            </div>

            <!-- Invoice Footer -->
            <div style="background: #0c2340; color: #8da4be; padding: 18px 32px; text-align: center; font-size: 11px; line-height: 1.5;">
                <p style="margin: 0; color: #ffffff; font-weight: bold;">Delux Tour &amp; Travel Pvt. Ltd. · GSTIN: 24AAACD9876K1Z9</p>
                <p style="margin: 4px 0 0;">This is a computer-generated tax invoice and booking receipt. No physical signature required.</p>
            </div>
        </div>
        """
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        _send_in_background(
            msg,
            f"Customer booking confirmation email successfully sent to {to_email}",
            f"Failed to send customer booking confirmation email to {booking.email}"
        )
        return True
    except Exception as e:
        logger.warning(f"Failed to queue customer booking confirmation email: {e}")
        return False


def send_customer_plan_confirmation(plan):
    """
    Sends an acknowledgment email to the customer when they submit a custom trip plan.
    """
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'pyash7571@gmail.com')
        to_email = plan.email
        subject = f"✦ We have received your trip inquiry for {plan.destination} - Delux Tour & Travel"

        date_str = plan.travel_date.strftime('%d %B %Y') if plan.travel_date else 'Flexible'

        html_content = f"""
        <div style="font-family: Montserrat, Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #fbfaf7; border: 1px solid #e6e0d5; border-radius: 8px; overflow: hidden; color: #17201d;">
            <div style="background: #17201d; padding: 25px 30px; text-align: center; color: #fff;">
                <h1 style="margin: 0; font-size: 24px; letter-spacing: 2px; color: #d4ad66;">✦ DELUX TOUR & TRAVEL</h1>
                <p style="margin: 5px 0 0; font-size: 11px; letter-spacing: 1px; color: #b48738;">CUSTOM TRIP INQUIRY RECEIVED</p>
            </div>
            <div style="padding: 30px;">
                <p style="font-size: 16px; margin-top: 0;">Dear <strong>{plan.name}</strong>,</p>
                <p style="color: #555; line-height: 1.6; font-size: 14px;">
                    Thank you for reaching out to plan your bespoke journey to <strong>{plan.destination}</strong>! Our itinerary designers are reviewing your preferences to craft the ideal travel schedule for you.
                </p>

                <div style="background: #ffffff; border: 1px solid #e6e0d5; border-radius: 6px; padding: 18px; margin: 20px 0;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <tr><td style="padding: 6px 0; color: #777;">Destination:</td><td style="padding: 6px 0; font-weight: bold;">{plan.destination}</td></tr>
                        <tr><td style="padding: 6px 0; color: #777;">Travel Mode:</td><td style="padding: 6px 0; font-weight: bold;">{plan.travel_mode}</td></tr>
                        <tr><td style="padding: 6px 0; color: #777;">Travelers:</td><td style="padding: 6px 0; font-weight: bold;">{plan.travelers or 'Not specified'}</td></tr>
                        <tr><td style="padding: 6px 0; color: #777;">Estimated Budget:</td><td style="padding: 6px 0; font-weight: bold;">{plan.budget or 'Flexible'}</td></tr>
                        <tr><td style="padding: 6px 0; color: #777;">Preferred Date:</td><td style="padding: 6px 0; font-weight: bold;">{date_str}</td></tr>
                    </table>
                </div>

                <p style="color: #555; font-size: 13px; line-height: 1.5;">We will send your customized itinerary with hotels and flight/train schedules to your email shortly.</p>
            </div>
            <div style="background: #111816; color: #7b817d; padding: 14px 20px; text-align: center; font-size: 11px;">
                © 2026 Delux Tour & Travel. All rights reserved.
            </div>
        </div>
        """
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        _send_in_background(
            msg,
            f"Customer trip plan confirmation email sent to {to_email}",
            f"Failed to send customer plan confirmation email to {plan.email}"
        )
        return True
    except Exception as e:
        logger.warning(f"Failed to queue customer plan confirmation email: {e}")
        return False
