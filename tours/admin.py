from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Package, Booking, Payment, TripPlan, ContactMessage, CustomerUser


from .upi_service import approve_upi_payment, reject_upi_payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    can_delete = False
    readonly_fields = (
        'transaction_id', 'gateway', 'utr_number', 'amount', 'currency',
        'status', 'payment_method', 'verified_by', 'verified_at', 'created_at'
    )
    fields = (
        'transaction_id', 'gateway', 'utr_number', 'amount', 'currency',
        'status', 'payment_method', 'verified_by', 'verified_at', 'created_at'
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'location', 'duration', 'price', 'featured')
    list_filter = ('featured', 'location')
    search_fields = ('title', 'location', 'description')
    ordering = ('id',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'booking_ref_display', 'package_title', 'full_name', 'email',
        'travelers', 'total_amount_display', 'utr_display',
        'payment_status_badge', 'booking_status_badge', 'verified_by', 'created_at'
    )
    list_filter = ('status', 'payment_status', 'travel_mode', 'created_at')
    search_fields = (
        'id', 'booking_reference', 'full_name', 'email', 'phone',
        'package_title', 'utr_number'
    )
    ordering = ('-created_at',)
    inlines = [PaymentInline]
    actions = ['approve_selected_upi_payments', 'reject_selected_upi_payments']
    readonly_fields = (
        'booking_reference', 'package_price', 'total_amount', 'amount_paid',
        'currency', 'utr_number', 'payment_submitted_at', 'verified_at', 'verified_by',
        'confirmation_email_sent', 'created_at', 'updated_at'
    )

    fieldsets = (
        ('Booking Reference & Customer', {
            'fields': ('booking_reference', 'user', 'full_name', 'email', 'phone')
        }),
        ('Tour Package Details', {
            'fields': ('package', 'package_title', 'travel_mode', 'travelers', 'travel_date', 'notes')
        }),
        ('Direct UPI Payment & Verification', {
            'fields': (
                'package_price', 'total_amount', 'amount_paid', 'currency',
                'status', 'payment_status', 'utr_number', 'payment_submitted_at',
                'verified_at', 'verified_by', 'rejection_reason',
                'confirmation_email_sent'
            )
        }),
        ('System Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.action(description="✓ Verify & Approve UPI Payment (Confirm Booking)")
    def approve_selected_upi_payments(self, request, queryset):
        count = 0
        for b in queryset:
            approve_upi_payment(b, verified_by=request.user.username or 'admin')
            count += 1
        self.message_user(request, f"Successfully verified and confirmed {count} booking(s). Tax invoice & voucher sent to customers.")

    @admin.action(description="✕ Reject UPI Payment")
    def reject_selected_upi_payments(self, request, queryset):
        count = 0
        for b in queryset:
            reject_upi_payment(b, reason="Payment could not be verified with bank records", verified_by=request.user.username or 'admin')
            count += 1
        self.message_user(request, f"Marked {count} booking(s) as REJECTED.")

    def booking_ref_display(self, obj):
        ref = obj.booking_reference or f"DELUX-BK-{obj.id:04d}"
        return format_html('<strong><code style="color:#0c2340">{}</code></strong>', ref)
    booking_ref_display.short_description = 'Booking Ref'

    def total_amount_display(self, obj):
        amt = obj.total_amount or obj.package_price
        return format_html('₹{:,.2f}', amt)
    total_amount_display.short_description = 'Total Payable'

    def utr_display(self, obj):
        if obj.utr_number:
            return format_html('<code style="background:#e0f2fe;color:#0369a1;padding:2px 6px;border-radius:4px;font-weight:bold;">{}</code>', obj.utr_number)
        return format_html('<span style="color:#9ca3af;">—</span>')
    utr_display.short_description = 'UPI UTR / Ref'

    def payment_status_badge(self, obj):
        colors = {
            'PAID': '#16a34a',
            'Paid': '#16a34a',
            'PENDING_VERIFICATION': '#0284c7',
            'PENDING': '#d97706',
            'Pending': '#d97706',
            'FAILED': '#dc2626',
            'Failed': '#dc2626',
            'REJECTED': '#991b1b',
            'REFUNDED': '#7c3aed',
        }
        color = colors.get(obj.payment_status, '#4b5563')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:bold;">{}</span>',
            color, obj.payment_status
        )
    payment_status_badge.short_description = 'Payment Status'

    def booking_status_badge(self, obj):
        colors = {
            'CONFIRMED': '#16a34a',
            'Confirmed': '#16a34a',
            'PENDING': '#d97706',
            'Pending': '#d97706',
            'REJECTED': '#991b1b',
            'CANCELLED': '#6b7280',
            'Cancelled': '#6b7280',
        }
        color = colors.get(obj.status, '#4b5563')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:bold;">{}</span>',
            color, obj.status
        )
    booking_status_badge.short_description = 'Booking Status'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'booking_link', 'amount_display', 'utr_number',
        'status_badge', 'payment_method', 'verified_by', 'created_at', 'verified_at'
    )
    list_filter = ('status', 'gateway', 'currency', 'created_at')
    search_fields = (
        'transaction_id', 'utr_number',
        'booking__booking_reference', 'booking__full_name', 'booking__email'
    )
    ordering = ('-created_at',)
    readonly_fields = (
        'booking', 'user', 'transaction_id', 'gateway', 'utr_number',
        'amount', 'currency', 'status', 'payment_method', 'error_code', 'error_description',
        'refund_id', 'refund_amount', 'refund_status', 'refund_reason',
        'raw_response', 'created_at', 'updated_at', 'verified_at', 'verified_by'
    )

    def has_add_permission(self, request):
        return False

    def booking_link(self, obj):
        url = reverse('admin:tours_booking_change', args=[obj.booking.id])
        return format_html('<a href="{}">Booking #{} ({})</a>', url, obj.booking.id, obj.booking.full_name)
    booking_link.short_description = 'Booking'

    def amount_display(self, obj):
        return format_html('<strong>₹{:,.2f} {}</strong>', obj.amount, obj.currency)
    amount_display.short_description = 'Amount'

    def status_badge(self, obj):
        colors = {
            'PAID': '#16a34a',
            'Paid': '#16a34a',
            'PENDING_VERIFICATION': '#0284c7',
            'PENDING': '#d97706',
            'Pending': '#d97706',
            'FAILED': '#dc2626',
            'Failed': '#dc2626',
            'REJECTED': '#991b1b',
            'REFUNDED': '#7c3aed',
        }
        color = colors.get(obj.status, '#4b5563')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:bold;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = 'Payment Status'


@admin.register(TripPlan)
class TripPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'destination', 'travel_mode', 'travelers', 'budget', 'travel_date', 'created_at')
    list_filter = ('travel_mode', 'created_at')
    search_fields = ('name', 'email', 'destination')
    ordering = ('-created_at',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_editable = ('is_read',)
    ordering = ('-created_at',)


@admin.register(CustomerUser)
class CustomerUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'created_at')
    search_fields = ('full_name', 'email')
    ordering = ('-created_at',)
