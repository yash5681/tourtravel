from django.db import models
from django.utils import timezone


class Package(models.Model):
    title = models.CharField(max_length=150)
    duration = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    description = models.TextField(max_length=1000, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.CharField(max_length=500, blank=True)
    featured = models.BooleanField(default=False)
    itinerary = models.TextField(blank=True, default='')
    inclusions = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.title} - ₹{self.price}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        # Backward compatibility aliases
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Payment Failed', 'Payment Failed'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PENDING_VERIFICATION', 'Pending Verification'),
        ('PAID', 'Paid / Confirmed'),
        ('FAILED', 'Failed'),
        ('REJECTED', 'Rejected'),
        ('REFUNDED', 'Refunded'),
        # Backward compatibility aliases
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]
    TRAVEL_MODE_CHOICES = [
        ('Flight', 'Flight'),
        ('Train', 'Train'),
    ]

    booking_reference = models.CharField(max_length=50, unique=True, blank=True, null=True, db_index=True)
    user = models.ForeignKey('CustomerUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    package_title = models.CharField(max_length=150)
    package_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='INR')
    full_name = models.CharField(max_length=100)
    email = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    travel_mode = models.CharField(max_length=20, choices=TRAVEL_MODE_CHOICES, default='Flight')
    travelers = models.CharField(max_length=20, default='1')
    travel_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    
    # UPI Direct Payment fields
    utr_number = models.CharField(max_length=100, blank=True, default='', db_index=True)
    payment_submitted_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.CharField(max_length=100, blank=True, default='')
    rejection_reason = models.TextField(blank=True, default='')

    # Legacy fields preserved for DB compatibility
    razorpay_order_id = models.CharField(max_length=100, blank=True, default='')
    razorpay_payment_id = models.CharField(max_length=100, blank=True, default='')
    razorpay_signature = models.CharField(max_length=255, blank=True, default='')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    confirmation_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            import uuid
            self.booking_reference = f"BK-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
        if self.id and (self.booking_reference.startswith('BK-') or not self.booking_reference):
            target_ref = f"DELUX-BK-{self.id:04d}"
            if not Booking.objects.filter(booking_reference=target_ref).exclude(id=self.id).exists():
                self.booking_reference = target_ref
                super().save(update_fields=['booking_reference'])

    def __str__(self):
        return f"Booking #{self.id} ({self.booking_reference or 'Pending'}) - {self.full_name} ({self.package_title})"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PENDING_VERIFICATION', 'Pending Verification'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REJECTED', 'Rejected'),
        ('REFUNDED', 'Refunded'),
        # Backward compatibility aliases
        ('Created', 'Created'),
        ('Pending', 'Pending'),
        ('Authorized', 'Authorized'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
        ('Refunded', 'Refunded'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    user = models.ForeignKey('CustomerUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    gateway = models.CharField(max_length=50, default='UPI')
    utr_number = models.CharField(max_length=100, blank=True, default='', db_index=True)
    gateway_order_id = models.CharField(max_length=100, blank=True, default='', db_index=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True, default='', db_index=True)
    gateway_signature = models.CharField(max_length=255, blank=True, default='')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    payment_method = models.CharField(max_length=50, blank=True, default='UPI')
    error_code = models.CharField(max_length=100, blank=True, default='')
    error_description = models.TextField(blank=True, default='')
    refund_id = models.CharField(max_length=100, blank=True, default='')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_status = models.CharField(max_length=30, blank=True, default='')
    refund_reason = models.TextField(blank=True, default='')
    raw_response = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.CharField(max_length=100, blank=True, default='')

    @property
    def response_data(self):
        import json
        try:
            return json.loads(self.raw_response) if self.raw_response else {}
        except Exception:
            return {}

    def set_response_data(self, data):
        import json
        try:
            self.raw_response = json.dumps(data)
        except Exception:
            self.raw_response = str(data)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.transaction_id} - ₹{self.amount} ({self.status})"


class TripPlan(models.Model):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=150)
    destination = models.CharField(max_length=150)
    travel_date = models.DateField(null=True, blank=True)
    travelers = models.CharField(max_length=20, blank=True)
    budget = models.CharField(max_length=50, blank=True)
    travel_mode = models.CharField(max_length=20, default='Flight')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TripPlan: {self.name} -> {self.destination}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=150)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name}: {self.subject}"


class CustomerUser(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=255)
    password_salt = models.CharField(max_length=255, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    bio = models.CharField(max_length=250, blank=True, default='Passionate traveler exploring the world')
    avatar_url = models.CharField(max_length=500, blank=True, default='https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80')
    city = models.CharField(max_length=100, blank=True, default='India')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.email})"

