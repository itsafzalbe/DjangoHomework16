from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import User, VIA_EMAIL, VIA_PHONE, CODE_VERIFIED, DONE, PHOTO_DONE
from shared.utility import email_or_phone_number
from shared.utility import send_email # send_phone_number_sms
from django.contrib.auth.password_validation import validate_password


#auth_validate --> phone_number or email
#create  ---> send_mail or sendPhone
#validate_email_phone_number= --> email or phone_number exists

class SignUpSerializer(serializers.ModelSerializer):
    # This field accepts either email or phone number from the user
    # It is NOT stored in the database — it is only used for signup logic
    email_phone_number = serializers.CharField(write_only=True)

    # These fields are returned to the client but cannot be modified
    id = serializers.UUIDField(read_only=True)
    auth_type = serializers.CharField(read_only=True)
    auth_status = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email_phone_number",
            "email",
            "phone_number",
            "auth_type",
            "auth_status",
            "password",
        )
        extra_kwargs = {
            "password": {"write_only": True}
        }

    # This function runs after all field validations.
    # It decides whether the user signed up using email or phone
    # and fills the correct database fields.
    def validate(self, data):
        user_input = data.get("email_phone_number")
        user_input_type = email_or_phone_number(user_input)

        if user_input_type == "email":
            data["email"] = user_input.lower()
            data["auth_type"] = VIA_EMAIL

        elif user_input_type == "phone":
            data["phone_number"] = user_input
            data["auth_type"] = VIA_PHONE

        else:
            raise ValidationError({
                "success": False,
                "message": "Telefon raqam yoki email kiriting"
            })

        return data

    # This function checks if the email or phone number
    # is already registered in the database
    def validate_email_phone_number(self, value):
        if User.objects.filter(email=value).exists():
            raise ValidationError({
                "success": False,
                "message": "Bu email oldin ro'yxatdan o'tgan"
            })

        if User.objects.filter(phone_number=value).exists():
            raise ValidationError({
                "success": False,
                "message": "Bu telefon raqam oldin ro'yxatdan o'tgan"
            })

        return value

    # This function creates the user and sends the OTP code
    # to either email or phone after successful signup
    def create(self, validated_data):
        validated_data.pop("email_phone_number")

        # user = User.objects.create_user(**validated_data)
        user = User.objects.create_user(username="temp", **validated_data )

        if user.auth_type == VIA_EMAIL:
            code = user.generate_code(VIA_EMAIL)
            send_email(user.email, code)

        elif user.auth_type == VIA_PHONE:
            code = user.generate_code(VIA_PHONE)
            # send_phone_number_sms(user.phone_number, code)

        return user

    # This function customizes the API response
    # It attaches JWT access & refresh tokens to the output
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(instance.token())
        return data
    
# class SignUpSerializer(serializers.ModelSerializer):
#     id = serializers.UUIDField(read_only=True)
#     auth_type = serializers.CharField(read_only=True, required=False)
#     auth_status = serializers.CharField(read_only=True, required=False)

#     def __init__(self, *args, **kwargs):
#         super(SignUpSerializer, self).__init__(*args, **kwargs)
#         self.fields['email_phone_number'] = serializers.CharField(write_only=True, required=False)

#     class Meta:
#         model = User
#         fields = (
#             "id",
#             "email",
#             "phone_number",
#             "auth_type",
#             "auth_status",
#             "password",
#         )
#         extra_kwargs = {
#             "password": {"write_only": True}
#         }
        
#     def create(self, validated_data):
#         # Remove non-model field
#         validated_data.pop('email_phone_number', None)

#         user = User.objects.create_user(**validated_data)

#         if user.auth_type == VIA_EMAIL:
#             code = user.generate_code(VIA_EMAIL)
#             send_email(user.email, code)

#         elif user.auth_type == VIA_PHONE:
#             code = user.generate_code(VIA_PHONE)
#             send_phone_number_sms(user.phone_number, code)

#         user.save()
#         return user


#     def validate(self, data):
#         data = super().validate(data)
#         data = self.auth_validate(data)
#         return data 
    

#     @staticmethod
#     def auth_validate(data):
#         user_input = str(data.get('email_phone_number'))
#         user_input_type = email_or_phone_number(user_input)
#         if user_input_type =='email':
#             data['email'] = user_input
#             data['auth_type'] = VIA_EMAIL
#         elif user_input_type =='phone':
#             data['phone_number'] = user_input
#             data['auth_type'] = VIA_PHONE
#         else:
#             data = {
#                 'success':'False',
#                 'message': 'Telefon raqam yoki email kiriting'
#             }
#             raise ValidationError(data)
#         return data
    
#     def validate_email_phone_number(self, value):
#         if value and User.objects.filter(email=value).exists():
#             data = {
#                 'success':'False',
#                 'message':'Bu email oldin royxatdan otgan'
#             }
#             raise ValidationError(data)
#         elif value and User.objects.filter(phone_number=value).exists():
#             data = {
#                 'success':'False',
#                 'message':'Bu telefon raqam oldin royxatdan otgan'
#             }
#             raise ValidationError(data)
#         return value
    
#     def to_representation(self, instance):
#         data = super(SignUpSerializer, self).to_representation(instance)
#         data.update(instance.token())
#         return data
    
class UserChangeInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    confirm_password = serializers.CharField(required=False)

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)

        if password and confirm_password and password != confirm_password:
            data = {
                'success': False,
                'message': 'Parollar bir biriga mos kelmadi.'
            }
            raise ValidationError(data)
        
        if password:
            validate_password(password)
            validate_password(confirm_password)

        return data
    
    def validate_username(self, username):  
        # length
        if len(username) < 5 or len(username) > 30:
            raise serializers.ValidationError("Username must be between 5 and 30 characters") 
        
        # allowed characters
        for char in username:
            if not (char.isalnum() or char=="_"):
                raise serializers.ValidationError("Invalid Username")
        
        # no leadin/trailing underscore
        if username.startswith('_') or username.endswith("_"):
            raise serializers.ValidationError("Invalid Username")
        
        # no double underscore
        if "__" in username:
            raise serializers.ValidationError("Invalid Username")
        
        # uniqueness
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("This username exists")
        
        return username
    
    def validate_first_name(self, f_name):
        #length
        if len(f_name) < 2:
            raise serializers.ValidationError("First Name should be at least 3 letters")
        if len(f_name) > 30:
            raise serializers.ValidationError("First Name should not exceed 30 characters")
        
        if "  " in f_name:
            raise serializers.ValidationError("Invalid first name")
        
        for char in f_name:
            if not (char.isalpha() or char == " "):
                raise serializers.ValidationError("First name should be letters only")
        
        return f_name
    
    def validate_last_name(self, l_name):
        if len(l_name) < 2:
            raise serializers.ValidationError("Last Name should be at least 3 letters")
        if len(l_name) > 30:
            raise serializers.ValidationError("Last Name should not exceed 30 characters")
        
        if "  " in l_name:
            raise serializers.ValidationError("Invalid last name")
        
        for char in l_name:
            if not (char.isalpha() or char == " "):
                raise serializers.ValidationError("Last name should be letters only")
        
        return l_name
    
    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.first_name)

        if validated_data.get('password'):
            instance.set_password(validated_data['password'])
        if instance.auth_status == CODE_VERIFIED:
            instance.auth_status = DONE
        instance.save()
        return instance
    
class UserPhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField(required=True)

    class Meta:
        model = User
        fields = ('photo',)

    def update(self, instance, validated_data):
        photo = validated_data.get('photo')

        if photo:
            instance.photo =photo
            instance.auth_status = PHOTO_DONE
            instance.save()
        return instance

        



            
