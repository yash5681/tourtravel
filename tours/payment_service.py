"""
Delux Tour & Travel - Payment Service
Direct UPI Payment System (Razorpay removed).
Delegates core payment processing to upi_service.
"""
import logging
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

# Backward compatibility alias
PaymentGatewayError = UpiPaymentError
