from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # Frontend Pages (Clean URLs, with/without slashes, and .html support)
    path('', views.index_view, name='home'),
    path('index', views.index_view),
    path('index/', views.index_view),
    path('index.html', views.index_view, name='index'),

    path('about', views.about_view),
    path('about/', views.about_view),
    path('about.html', views.about_view, name='about'),

    path('packages', views.packages_view),
    path('packages/', views.packages_view),
    path('packages.html', views.packages_view, name='packages'),

    path('book', views.book_view),
    path('book/', views.book_view),
    path('book.html', views.book_view, name='book'),

    path('plan', views.plan_view),
    path('plan/', views.plan_view),
    path('plan.html', views.plan_view, name='plan'),

    path('gallery', views.gallery_view),
    path('gallery/', views.gallery_view),
    path('gallery.html', views.gallery_view, name='gallery'),

    path('contact', views.contact_view),
    path('contact/', views.contact_view),
    path('contact.html', views.contact_view, name='contact'),

    path('login', views.login_view),
    path('login/', views.login_view),
    path('login.html', views.login_view, name='login'),

    path('register', views.register_view),
    path('register/', views.register_view),
    path('register.html', views.register_view, name='register'),

    path('admin-login', views.admin_login_view),
    path('admin-login/', views.admin_login_view),
    path('admin-login.html', views.admin_login_view, name='admin_login'),

    path('admin', views.admin_dashboard_view),
    path('admin/', views.admin_dashboard_view),
    path('admin.html', views.admin_dashboard_view, name='admin_dashboard'),

    path('profile', views.profile_view),
    path('profile/', views.profile_view),
    path('profile.html', views.profile_view, name='profile'),

    # Customer Auth APIs (with and without trailing slash)
    path('api/auth/register', api_views.api_register, name='api_register'),
    path('api/auth/register/', api_views.api_register),
    path('api/auth/login', api_views.api_login, name='api_login'),
    path('api/auth/login/', api_views.api_login),
    path('api/auth/logout', api_views.api_logout, name='api_logout'),
    path('api/auth/logout/', api_views.api_logout),
    path('api/auth/me', api_views.api_me, name='api_me'),
    path('api/auth/me/', api_views.api_me),
    path('api/profile', api_views.api_profile, name='api_profile'),
    path('api/profile/', api_views.api_profile),
    path('api/profile/update', api_views.api_profile_update, name='api_profile_update'),
    path('api/profile/update/', api_views.api_profile_update),

    # Public APIs (with and without trailing slash)
    path('api/contact', api_views.api_contact, name='api_contact'),
    path('api/contact/', api_views.api_contact),
    path('api/plan', api_views.api_plan, name='api_plan'),
    path('api/plan/', api_views.api_plan),
    path('api/packages', api_views.api_packages, name='api_packages'),
    path('api/packages/', api_views.api_packages),
    path('api/bookings', api_views.api_bookings, name='api_bookings'),
    path('api/bookings/', api_views.api_bookings),

    # Dedicated Payment Status & UPI Pages
    path('payment/upi/<int:booking_id>', views.payment_upi_view, name='payment_upi'),
    path('payment/upi/<int:booking_id>/', views.payment_upi_view),
    path('payment/success/<int:booking_id>', views.payment_success_view, name='payment_success'),
    path('payment/success/<int:booking_id>/', views.payment_success_view),
    path('payment/failed/<int:booking_id>', views.payment_failed_view, name='payment_failed'),
    path('payment/failed/<int:booking_id>/', views.payment_failed_view),
    path('payment/pending/<int:booking_id>', views.payment_pending_view, name='payment_pending'),
    path('payment/pending/<int:booking_id>/', views.payment_pending_view),
    path('payment/retry/<int:booking_id>', views.payment_retry_view, name='payment_retry'),
    path('payment/retry/<int:booking_id>/', views.payment_retry_view),

    # Direct UPI Payment System APIs
    path('api/upi/create-booking', api_views.api_upi_create_booking, name='api_upi_create_booking'),
    path('api/upi/create-booking/', api_views.api_upi_create_booking),
    path('api/upi/submit-utr', api_views.api_upi_submit_utr, name='api_upi_submit_utr'),
    path('api/upi/submit-utr/', api_views.api_upi_submit_utr),
    path('api/payment/retry/<int:booking_id>', api_views.api_payment_retry, name='api_payment_retry'),
    path('api/payment/retry/<int:booking_id>/', api_views.api_payment_retry),
    path('api/payment/status/<int:booking_id>', api_views.api_payment_status, name='api_payment_status'),
    path('api/payment/status/<int:booking_id>/', api_views.api_payment_status),
    path('api/upi/demo-verify/<int:booking_id>', api_views.api_upi_demo_verify, name='api_upi_demo_verify'),
    path('api/upi/demo-verify/<int:booking_id>/', api_views.api_upi_demo_verify),

    # Customer My Bookings Feature
    path('api/my-bookings', api_views.api_my_bookings, name='api_my_bookings'),
    path('api/my-bookings/', api_views.api_my_bookings),

    # Admin APIs (with and without trailing slash)
    path('api/admin/login', api_views.api_admin_login, name='api_admin_login'),
    path('api/admin/login/', api_views.api_admin_login),
    path('api/admin/logout', api_views.api_admin_logout, name='api_admin_logout'),
    path('api/admin/logout/', api_views.api_admin_logout),
    path('api/admin/me', api_views.api_admin_me, name='api_admin_me'),
    path('api/admin/me/', api_views.api_admin_me),
    path('api/admin/summary', api_views.api_admin_summary, name='api_admin_summary'),
    path('api/admin/summary/', api_views.api_admin_summary),
    path('api/admin/bookings', api_views.api_admin_bookings, name='api_admin_bookings'),
    path('api/admin/bookings/', api_views.api_admin_bookings),
    path('api/admin/bookings/<int:booking_id>/status', api_views.api_admin_booking_status, name='api_admin_booking_status'),
    path('api/admin/bookings/<int:booking_id>/status/', api_views.api_admin_booking_status),
    path('api/admin/bookings/<int:booking_id>/approve-upi', api_views.api_admin_booking_approve_upi, name='api_admin_booking_approve_upi'),
    path('api/admin/bookings/<int:booking_id>/approve-upi/', api_views.api_admin_booking_approve_upi),
    path('api/admin/bookings/<int:booking_id>/reject-upi', api_views.api_admin_booking_reject_upi, name='api_admin_booking_reject_upi'),
    path('api/admin/bookings/<int:booking_id>/reject-upi/', api_views.api_admin_booking_reject_upi),
    path('api/admin/plans', api_views.api_admin_plans, name='api_admin_plans'),
    path('api/admin/plans/', api_views.api_admin_plans),
    path('api/admin/contacts', api_views.api_admin_contacts, name='api_admin_contacts'),
    path('api/admin/contacts/', api_views.api_admin_contacts),
    path('api/admin/users', api_views.api_admin_users, name='api_admin_users'),
    path('api/admin/users/', api_views.api_admin_users),

    # Admin Package CRUD & CSV Export
    path('api/admin/packages', api_views.api_admin_packages, name='api_admin_packages'),
    path('api/admin/packages/', api_views.api_admin_packages),
    path('api/admin/export/bookings', api_views.api_admin_export_bookings, name='api_admin_export_bookings'),
    path('api/admin/export/bookings/', api_views.api_admin_export_bookings),
]
