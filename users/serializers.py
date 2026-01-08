from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import User, VIA_EMAIL, VIA_PHONE
from shared.utility import email_or_phone_number
from shared.utility import send_email


#auth_validate --> phone_number or email
#create  ---> send_mail or sendPhone
#validate_email_phone_number= --> email or phone_number exists


class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    auth_type = serializers.CharField(read_only=True, required=False)
    auth_status = serializers.CharField(read_only=True, required=False)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id',
            'auth_type',
            'auth_status',
        ] 
    def create(self, validated_data):
        # Remove non-model field
        validated_data.pop('email_phone_number', None)

        user = User.objects.create(**validated_data)

        if user.auth_type == VIA_EMAIL:
            code = user.generate_code(VIA_EMAIL)
            send_email(user.email, code)

        elif user.auth_type == VIA_PHONE:
            code = user.generate_code(VIA_PHONE)
            # send_phone_number_sms(user.phone_number, code)

        user.save()
        return user


    def validate(self, data):
        data = super().validate(data)
        data = self.auth_validate(data)
        return data 
    

    @staticmethod
    def auth_validate(data):
        user_input = str(data.get('email_phone_number'))
        user_input_type = email_or_phone_number(user_input)
        if user_input_type =='email':
            data['email'] = user_input
            data['auth_type'] = VIA_EMAIL
        elif user_input_type =='phone':
            data['phone_number'] = user_input
            data['auth_type'] = VIA_PHONE
        else:
            data = {
                'success':'False',
                'message': 'Telefon raqam yoki email kiriting'
            }
            raise ValidationError(data)
        return data
    
    def validate_email_phone_number(self, value):
        if value and User.objects.filter(email=value).exists():
            data = {
                'success':'False',
                'message':'Bu email oldin royxatdan otgan'
            }
            raise ValidationError(data)
        elif value and User.objects.filter(phone_number=value).exists():
            data = {
                'success':'False',
                'message':'Bu telefon raqam oldin royxatdan otgan'
            }
            raise ValidationError(data)
        return value

