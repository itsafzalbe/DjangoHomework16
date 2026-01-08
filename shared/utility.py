import re
from django.core.mail import send_mail
from django.conf import settings

from rest_framework.exceptions import ValidationError
email_regex = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
phone_regex = re.compile(r"^(\+998|998)?[0-9]{9}$")


def email_or_phone_number(email_phone_number):
    if re.fullmatch(email_regex, email_phone_number):
        email_or_phone = 'email'
    elif re.fullmatch(phone_regex, email_phone_number):
        email_or_phone = 'phone'
    else:
        data = {
            'success': 'False',
            'message': 'Telefon raqam yoki email xato kiritildi'
        }

        raise ValidationError(data)
    return email_or_phone

def send_email(email, code):
    subject = "Your Verification Code: "
    message = (
        f"Your verification code is: {code}\n\n"
        "This code will expire in 5 minutes.\n"
        "If you did not request this, please ignore this email."
    )
    send_mail(
        subject, 
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently = False,

    )