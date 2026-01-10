from django.shortcuts import render
from rest_framework.generics import CreateAPIView, UpdateAPIView
from .models import User, NEW, CODE_VERIFIED, VIA_EMAIL, VIA_PHONE
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import SignUpSerializer, UserChangeInfoSerializer, UserPhotoSerializer
from rest_framework import permissions
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError


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


        