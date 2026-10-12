import json
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase, Client
from django.utils import timezone
from .models import Package, Booking, Payment, ContactMessage, TripPlan, CustomerUser
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


class DeluxTourTravelUpiPaymentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.package = Package.objects.create(
            title="Luxury Maldives Getaway",
            duration="5 Days / 4 Nights",
            location="Maldives",
            description="Crystal waters and private water villas",
            price=Decimal('75000.00'),
            image_url="https://images.unsplash.com/photo-1514282401047-d79a71a590e8",
            featured=True
        )
        self.user = CustomerUser.objects.create(
            full_name="Aarav Patel",
            email="aarav@example.com",
            phone="+91 9876543210",
            password_hash="testhash"
        )

    def _login_user(self):
        session = self.client.session
        session['customer_id'] = self.user.id
        session['customer_name'] = self.user.full_name
        session['customer_email'] = self.user.email
        session.save()

    def _login_admin(self):
        session = self.client.session
        session['admin_logged_in'] = True
        session['admin_email'] = 'admin@deluxtour.com'
        session.save()

    def test_pages_render_and_brand_assets(self):
        """All public pages load 200 OK and have luxury branding icons."""
        public_pages = [
            '/', '/index.html', '/about.html', '/contact.html',
            '/packages.html', '/plan.html',
            '/gallery.html', '/login.html', '/register.html',
            '/admin-login.html'
        ]
        for url in public_pages:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Page {url} failed with {response.status_code}")
            content = response.content.decode('utf-8')
            self.assertIn("logo-icon.svg", content, f"Page {url} missing logo-icon.svg")
            self.assertIn("favicon.svg", content, f"Page {url} missing favicon.svg")

    def test_book_page_requires_login(self):
        """Unauthenticated user visiting booking page is redirected to login."""
        response = self.client.get(f'/book.html?packageId={self.package.id}')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login.html?next=', response.url)

        self._login_user()
        auth_response = self.client.get(f'/book.html?packageId={self.package.id}')
        self.assertEqual(auth_response.status_code, 200)

    def test_packages_catalog_api(self):
        """Catalog API returns list of packages with correct price."""
        response = self.client.get('/api/packages')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(any(p['title'] == "Luxury Maldives Getaway" for p in data))

    def test_upi_config_retrieval(self):
        """get_upi_config returns valid configured UPI ID and payee details."""
        cfg = get_upi_config()
        self.assertTrue(cfg.get('upi_id'))
        self.assertTrue(cfg.get('payee_name'))
        self.assertEqual(cfg.get('currency'), 'INR')

    def test_upi_payment_link_generation(self):
        """NPCI UPI payment deep link has correct scheme, parameters, and formatted amount."""
        link = generate_upi_payment_link(
            upi_id="deluxtour@upi",
            payee_name="Delux Tour and Travel",
            amount=Decimal('150000.00'),
            booking_reference="DELUX-BK-1001"
        )
        self.assertTrue(link.startswith("upi://pay?"))
        self.assertIn("pa=deluxtour%40upi", link)
        self.assertIn("am=150000.00", link)
        self.assertIn("cu=INR", link)
        self.assertIn("DELUX-BK-1001", link)

    def test_upi_qr_code_url_generation(self):
        """QR code generation URL formats properly."""
        link = "upi://pay?pa=test@upi&pn=Test&am=500.00&cu=INR"
        qr_url = generate_upi_qr_code_url(link)
        self.assertIn("https://api.qrserver.com/v1/create-qr-code/", qr_url)
        self.assertIn("size=260x260", qr_url)

    def test_upi_create_booking_unauthenticated_blocked(self):
        """Unauthenticated user cannot create bookings."""
        payload = {
            'packageId': self.package.id,
            'fullName': 'Aarav Patel',
            'email': 'aarav@example.com',
            'phone': '+91 9876543210',
            'travelers': '2',
            'travelDate': '2026-11-20'
        }
        response = self.client.post(
            '/api/upi/create-booking',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.json().get('requireLogin'))

    def test_upi_create_booking_authenticated_success(self):
        """Authenticated user creates pending booking with strictly server-side Decimal price calculation."""
        self._login_user()
        payload = {
            'packageId': self.package.id,
            'fullName': 'Aarav Patel',
            'email': 'aarav@example.com',
            'phone': '+91 9876543210',
            'travelers': '2',
            'travelDate': '2026-11-20',
            'travelMode': 'Flight',
            'notes': 'Beach villa preference'
        }
        response = self.client.post(
            '/api/upi/create-booking',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('totalAmount'), 150000.00)
        self.assertEqual(data.get('redirectUrl'), f"/payment/upi/{data['bookingId']}/")
        self.assertTrue(data.get('upiLink').startswith('upi://pay?'))
        self.assertTrue(data.get('qrCodeUrl'))

        # Verify database state
        booking = Booking.objects.get(id=data['bookingId'])
        self.assertEqual(booking.status, 'PENDING')
        self.assertEqual(booking.payment_status, 'PENDING')
        self.assertEqual(booking.total_amount, Decimal('150000.00'))
        self.assertEqual(booking.user, self.user)

        # Verify initial Payment record created
        payment = Payment.objects.filter(booking=booking).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'PENDING')
        self.assertEqual(payment.gateway, 'UPI')
        self.assertEqual(payment.amount, Decimal('150000.00'))

    def test_upi_payment_page_renders_with_details_and_qr(self):
        """Dedicated UPI payment page renders dynamic QR code and copyable UPI ID."""
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            package_title=self.package.title,
            package_price=Decimal('75000.00'),
            total_amount=Decimal('75000.00'),
            full_name="Aarav Patel",
            email="aarav@example.com",
            phone="+91 9876543210",
            travelers="1",
            status="PENDING",
            payment_status="PENDING"
        )
        self._login_user()
        response = self.client.get(f'/payment/upi/{booking.id}/')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn("Direct UPI Payment", content)
        self.assertIn(booking.booking_reference, content)
        self.assertIn("75000", content)
        self.assertIn("Submit Transaction Reference (UTR)", content)

    @patch('tours.upi_service.send_admin_notification')
    def test_upi_submit_utr_sets_pending_verification(self, mock_notify):
        """Customer submits UTR -> marks PENDING_VERIFICATION. Never automatically confirms as paid."""
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            package_title=self.package.title,
            package_price=Decimal('75000.00'),
            total_amount=Decimal('75000.00'),
            full_name="Aarav Patel",
            email="aarav@example.com",
            phone="+91 9876543210",
            travelers="1",
            status="PENDING",
            payment_status="PENDING"
        )
        self._login_user()

        payload = {
            'bookingId': booking.id,
            'utrNumber': '428412345678',
            'notes': 'Paid from Aarav HDFC UPI'
        }
        response = self.client.post(
            '/api/upi/submit-utr',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('paymentStatus'), 'PENDING_VERIFICATION')
        self.assertEqual(data.get('utrNumber'), '428412345678')

        # Critical requirement: Booking must remain PENDING / PENDING_VERIFICATION until staff approval
        booking.refresh_from_db()
        self.assertEqual(booking.payment_status, 'PENDING_VERIFICATION')
        self.assertNotEqual(booking.payment_status, 'PAID')
        self.assertEqual(booking.status, 'PENDING')
        self.assertNotEqual(booking.status, 'CONFIRMED')
        self.assertEqual(booking.utr_number, '428412345678')
        self.assertIsNotNone(booking.payment_submitted_at)

        # Payment table row updated
        payment = Payment.objects.filter(booking=booking).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'PENDING_VERIFICATION')
        self.assertEqual(payment.utr_number, '428412345678')

        # Admin notified for verification
        mock_notify.assert_called()

    def test_upi_submit_invalid_utr_rejected(self):
        """Submitting an empty or too short UTR is rejected with 400 Bad Request."""
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            package_title=self.package.title,
            package_price=Decimal('75000.00'),
            total_amount=Decimal('75000.00'),
            full_name="Aarav Patel",
            email="aarav@example.com",
            phone="+91 9876543210",
            travelers="1",
            status="PENDING",
            payment_status="PENDING"
        )
        self._login_user()

        # Less than 6 characters
        payload = {
            'bookingId': booking.id,
            'utrNumber': '123'
        }
        response = self.client.post(
            '/api/upi/submit-utr',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json().get('ok'))
        self.assertIn("at least 6 characters", response.json().get('message'))

    def test_duplicate_utr_submission_prevented(self):
        """Fraud prevention: Customers cannot recycle an already used UTR across different bookings."""
        # Booking 1 already verified with UTR
        Booking.objects.create(
            package_title="Goa Trip",
            package_price=Decimal('20000.00'),
            total_amount=Decimal('20000.00'),
            full_name="Priya Sharma",
            email="priya@example.com",
            phone="+91 9999999999",
            utr_number="428412345678",
            payment_status="PAID",
            status="CONFIRMED"
        )

        # Booking 2 tries to reuse same UTR
        booking2 = Booking.objects.create(
            user=self.user,
            package=self.package,
            package_title=self.package.title,
            package_price=Decimal('75000.00'),
            total_amount=Decimal('75000.00'),
            full_name="Aarav Patel",
            email="aarav@example.com",
            phone="+91 9876543210",
            status="PENDING",
            payment_status="PENDING"
        )
        self._login_user()

        payload = {
            'bookingId': booking2.id,
            'utrNumber': '428412345678'
        }
        response = self.client.post(
            '/api/upi/submit-utr',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get('ok'))
        self.assertIn("already been submitted for another booking", data.get('message'))

    def test_admin_authorization_required_for_approval(self):
        """Unauthorized non-admin callers cannot approve or reject UPI payments."""
        booking = Booking.objects.create(
            package_title="Kashmir Tour",
            package_price=Decimal('45000.00'),
            total_amount=Decimal('45000.00'),
            full_name="Test User",
            email="test@example.com",
            phone="+91 9876543210",
            utr_number="UTR123456789",
            status="PENDING",
            payment_status="PENDING_VERIFICATION"
        )

        # Unauthenticated
        res = self.client.post(f'/api/admin/bookings/{booking.id}/approve-upi')
        self.assertEqual(res.status_code, 401)

        res_rej = self.client.post(f'/api/admin/bookings/{booking.id}/reject-upi')
        self.assertEqual(res_rej.status_code, 401)

    @patch('tours.upi_service.send_customer_booking_confirmation')
    def test_admin_approve_upi_workflow(self, mock_send_email):
        """Staff approves UPI payment: booking marks CONFIRMED/PAID, tax invoice is sent."""
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            package_title=self.package.title,
            package_price=Decimal('75000.00'),
            total_amount=Decimal('75000.00'),
            full_name="Aarav Patel",
            email="aarav@example.com",
            phone="+91 9876543210",
            utr_number="UTR987654321",
            status="PENDING",
            payment_status="PENDING_VERIFICATION"
        )
        Payment.objects.create(
            booking=booking,
            transaction_id="TXN-1",
            utr_number="UTR987654321",
            amount=Decimal('75000.00'),
            status="PENDING_VERIFICATION"
        )

        self._login_admin()
        response = self.client.post(f'/api/admin/bookings/{booking.id}/approve-upi')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('status'), 'CONFIRMED')
        self.assertEqual(data.get('paymentStatus'), 'PAID')

        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CONFIRMED')
        self.assertEqual(booking.payment_status, 'PAID')
        self.assertEqual(booking.amount_paid, Decimal('75000.00'))
        self.assertEqual(booking.verified_by, 'admin@deluxtour.com')
        self.assertIsNotNone(booking.verified_at)
        self.assertTrue(booking.confirmation_email_sent)

        # Tax invoice email triggered
        mock_send_email.assert_called_once_with(booking)

    def test_admin_reject_upi_workflow(self):
        """Staff rejects UPI payment with custom reason."""
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            package_title=self.package.title,
            package_price=Decimal('75000.00'),
            total_amount=Decimal('75000.00'),
            full_name="Aarav Patel",
            email="aarav@example.com",
            phone="+91 9876543210",
            utr_number="FAKEUTR999",
            status="PENDING",
            payment_status="PENDING_VERIFICATION"
        )
        Payment.objects.create(
            booking=booking,
            transaction_id="TXN-2",
            utr_number="FAKEUTR999",
            amount=Decimal('75000.00'),
            status="PENDING_VERIFICATION"
        )

        self._login_admin()
        payload = {'reason': 'Bank credit statement does not show matching entry.'}
        response = self.client.post(
            f'/api/admin/bookings/{booking.id}/reject-upi',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('status'), 'REJECTED')
        self.assertEqual(data.get('paymentStatus'), 'REJECTED')

        booking.refresh_from_db()
        self.assertEqual(booking.status, 'REJECTED')
        self.assertEqual(booking.payment_status, 'REJECTED')
        self.assertEqual(booking.rejection_reason, 'Bank credit statement does not show matching entry.')
        self.assertEqual(booking.verified_by, 'admin@deluxtour.com')

    def test_payment_status_api(self):
        """Live payment status API returns current status, amount, and UTR."""
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            package_title=self.package.title,
            package_price=Decimal('75000.00'),
            total_amount=Decimal('75000.00'),
            full_name="Aarav Patel",
            email="aarav@example.com",
            phone="+91 9876543210",
            utr_number="UTR11223344",
            status="PENDING",
            payment_status="PENDING_VERIFICATION"
        )
        self._login_user()
        response = self.client.get(f'/api/payment/status/{booking.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('utrNumber'), 'UTR11223344')
        self.assertEqual(data.get('paymentStatus'), 'PENDING_VERIFICATION')
        self.assertEqual(data.get('totalAmount'), 75000.00)

    def test_admin_export_bookings_csv_includes_utr(self):
        """Admin export bookings CSV includes UPI UTR Number and verification headers."""
        Booking.objects.create(
            package_title="Kerala Backwaters",
            package_price=Decimal('35000.00'),
            total_amount=Decimal('35000.00'),
            amount_paid=Decimal('35000.00'),
            full_name="Rohan Verma",
            email="rohan@example.com",
            phone="+91 9876500000",
            utr_number="UTR9988776655",
            verified_by="admin@deluxtour.com",
            status="CONFIRMED",
            payment_status="PAID"
        )
        self._login_admin()
        response = self.client.get('/api/admin/export/bookings')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        csv_text = response.content.decode('utf-8')
        self.assertIn("UPI Reference / UTR", csv_text)
        self.assertIn("Verified By", csv_text)
        self.assertIn("UTR9988776655", csv_text)
        self.assertIn("Rohan Verma", csv_text)

    @patch('tours.upi_service.send_customer_booking_confirmation')
    def test_upi_demo_presentation_verify(self, mock_send_email):
        """College presentation demo endpoint verifies payment and sends Tax Invoice email."""
        booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            package_title=self.package.title,
            package_price=Decimal('75000.00'),
            total_amount=Decimal('75000.00'),
            full_name="Aarav Patel",
            email="aarav@example.com",
            phone="+91 9876543210",
            travelers="1",
            status="PENDING",
            payment_status="PENDING"
        )
        self._login_user()

        response = self.client.post(f'/api/upi/demo-verify/{booking.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('status'), 'CONFIRMED')
        self.assertEqual(data.get('paymentStatus'), 'PAID')
        self.assertIn("Official Tax Invoice email dispatched", data.get('message'))

        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CONFIRMED')
        self.assertEqual(booking.payment_status, 'PAID')
        self.assertTrue(booking.utr_number.startswith("DEMO-CLG-"))
        self.assertEqual(booking.verified_by, 'College Presentation Demo')
        self.assertTrue(booking.confirmation_email_sent)
        mock_send_email.assert_called_once_with(booking)

