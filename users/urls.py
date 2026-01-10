from django.urls import path
from .views import SignUpView, VerifyCode, ResendCode, UserChangeInfo, UploadPhoto



urlpatterns = [
    path('signup/', SignUpView.as_view(), name="signup"),
    path('code-verify/', VerifyCode.as_view(), name="code-verify"),
    path("resend-code/", ResendCode.as_view(), name="resend-code"),
    path("user-change-info/", UserChangeInfo.as_view(), name="user-change-info"),
    path('upload-photo/', UploadPhoto.as_view(), name="upload-photo"),
]