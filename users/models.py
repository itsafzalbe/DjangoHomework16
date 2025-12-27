from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from shared.models import BaseModel
from datetime import datetime, timedelta
import random

ORDINARY_USER, MANAGER, ADMIN = ('ordinary_user', 'manager', 'admin')
NEW, CODE_VERIFIED, DONE, PHOTO_DONE = ('new', 'code_verified', 'done', 'photo_done')
VIA_EMAIL, VIA_PHONE = ('via_email', 'via_phone')

class User(AbstractUser, BaseModel):
    USER_ROLE = (
        (ORDINARY_USER, ORDINARY_USER),
        (MANAGER, MANAGER),
        (ADMIN, ADMIN)
    )
    AUTH_STATUS = (
        (NEW, NEW),
        (CODE_VERIFIED, CODE_VERIFIED),
        (DONE, DONE),
        (PHOTO_DONE, PHOTO_DONE)
    )
    AUTH_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE)
    )

    user_role = models.CharField(max_length=29, choices=USER_ROLE, default=ORDINARY_USER)
    auth_status = models.CharField(max_length=29, choices=AUTH_STATUS, default=NEW)
    auth_type = models.CharField(max_length=29, choices=AUTH_TYPE)
    phone_number = models.CharField(max_length=13, null=True, blank=True, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    photo = models.ImageField(upload_to='users_photo/', default = 'user_photo/default_user.png', null = True,\
                              blank = True, validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])])
    


    def __str__(self):
        return self.username
    
    def generate_code(self, verify_type):
        code = ''.join([str(random.randint(0, 100)%10) for _ in range(4)])
        UserConfirmation.objects.create(
            user_id = self.id,
            code = code,
            verify_type = verify_type,
        )
        return code

    
EXPIRATION_EMAIL = 3
EXPIRATION_PHONE = 2

class UserConfirmation(BaseModel):
    VERIFY_TYPE = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE)
    )

    code = models.CharField(max_length=4)
    verify_type = models.CharField(max_length=29, choices=VERIFY_TYPE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    expiration_time = models.DateTimeField()
    confirmed = models.BooleanField(default=False)


    def __str__(self):
        return str(self.user.__str__())
    
    def save(self, *args, **kwargs):
        if self.verify_type == VIA_EMAIL:
            self.expiration_time = datetime.now() + timedelta(minutes = EXPIRATION_EMAIL)
        else:
            self.expiration_time = datetime.now() = timedelta(minutes = EXPIRATION_PHONE)

        super(UserConfirmation, self).save(*args, **kwargs)





