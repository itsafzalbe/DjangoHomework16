from django.shortcuts import render
from rest_framework.generics import CreateAPIView, UpdateAPIView
from .models import User, NEW, CODE_VERIFIED, VIA_EMAIL, VIA_PHONE
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import *
from rest_framework import permissions
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import ObjectDoesNotExist
from shared.utility import *


class SignUpView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = (permissions.AllowAny, )


class VerifyCode(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, *args, **kwargs):
        user = self.request.user
        code = self.request.data.get('code')

        self.check_verify_code(user, code)
        data = {
            'success': True,
            'auth_status': user.auth_status,
            'access_token': user.token()['access'],
            'refresh': user.token()['refresh']
        }
        return Response(data)
    
    @staticmethod
    def check_verify_code(user, code):

        verify = user.codes.filter(code=code, confirmed=False).first()
        if not verify:
            data = {
                'success':False,
                'message':"Kod noto'g'ri"
            }
            raise ValidationError(data)
        if verify.expiration_time < now():
            raise ValidationError ({
                'success': False,
                'message': 'Kod eskirgan'
            })
        # else:
        #     # verify.confirmed = True
        #     verify.update(confirmed=True)
        verify.confirmed = True
        verify.save()


        if user.auth_status == NEW:
            user.auth_status = CODE_VERIFIED
            user.save()

        return True

# class ResendCode(APIView):
#     permission_classes = (permissions.IsAuthenticated, )

#     def post(self, request):
#         user = request.user
        
#         if not user.can_resend_code():
#             raise ValidationError({
#                 'success': False,
#                 'message': 'Oxirgi kod hali amal qiladi. Iltimos kuting'
#             })
        
#         user.code.filter(confirmed = False).update(confirmed=True)
#         code = user.generate_code(user.auth_type)

#         if user.auth_type == VIA_EMAIL:
#             code = user.generate_code(VIA_EMAIL)
#             # send_email(user.email, code)

#         elif user.auth_type == VIA_PHONE:
#             code = user.generate_code(VIA_PHONE)
#             # send_phone_number_sms(user.phone_number, code)

#         return Response({
#             'success': True,
#             'message': 'Yangi kod yuborildi'
#         })


class ResendCode(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request):
        user = request.user

        # Check if resend is allowed
        if not user.can_resend_code():
            raise ValidationError({
                "success": False,
                "message": "Oxirgi kod hali amal qiladi. Iltimos kuting"
            })

        # Invalidate all old unconfirmed codes
        user.codes.filter(confirmed=False).update(confirmed=True)

        # Generate new code
        if user.auth_type == VIA_EMAIL:
            code = user.generate_code(VIA_EMAIL)
            # send_email(user.email, code)

        elif user.auth_type == VIA_PHONE:
            code = user.generate_code(VIA_PHONE)
            # send_phone_number_sms(user.phone_number, code)

        return Response({
            "success": True,
            "message": "Yangi kod yuborildi"
        })
    

class UserChangeInfo(UpdateAPIView):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = User.objects.all()
    serializer_class = UserChangeInfoSerializer


    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        data = {
            'success': True,
            'message': 'Malumotlaringiz yangilandi'
        }

        return Response(data)
    

    def partial_update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        data = {
            'success': True,
            'message': 'Malumotlaringiz qisman yangilandi'
        }

        return Response(data)
    
class UploadPhoto(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    parser_classes = (MultiPartParser, FormParser)

    def patch(self, request):
        user = request.user
        serializer = UserPhotoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.update(user, serializer.validated_data)

        return Response({
            'success':True,
            'auth_status':user.auth_status,
            'photo': user.photo.url if user.photo else None,
        })
    
class LoginView(TokenObtainPairView):
    serializer_class= LoginSerializer

class LogOutView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data = self.request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = self.request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            data = {
                'success': True,
                'message': 'You are logged out'
            }
            return Response(data, status=205)
        except TokenError:
            return Response({'message': "Xatolik", "status": 400}, status=400)
        except Exception as e:
            return Response({"message": "Xatolik"})

class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ForgotPasswordSerializer(data = self.request.data)
        serializer.is_valid(raise_exception=True)
        email_or_phone_ = serializer.validated_data.get('email_or_phone_')
        user = serializer.validated_data.get('user')
        if email_or_phone_number(email_or_phone_) == 'phone':
            code = user.verify_code(VIA_PHONE)
            # send_email(email_or_phone, code)
            print(code)
        elif email_or_phone_number(email_or_phone_) == 'email':
            code = user.verify_code(VIA_EMAIL)
            # send_sms(email_or_phone, code)
            print(code)
        
        return Response({
            'success': True,
            'message': "Tasdiqlash kodi muvoffaqiyatli yuborildi",
            "access": user.token()['access'],
            'refresh': user.token()['refresh_token'],
            "user_status": user.auth_status,
        }, status=200)
        

class ResetPasswordView(UpdateAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['patch', 'put']    

    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        response = super(ResetPasswordSerializer, self).update(request, *args, **kwargs)
        try:
            user = User.objects.get(id = response.data.get('id'))
        except ObjectDoesNotExist as e:
            raise NotFound(detail="User not found")
        return Response({
            'success': True,
            'message': "Password changed successfully",
            'access': user.token()['access'],
            'refresh': user.token()['refresh_token'],
        })
