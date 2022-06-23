import datetime
import random
import string

from django.core.mail import send_mail
from rest_framework import exceptions, status
from rest_framework.views import APIView
from rest_framework.views import Response

from .authentication import create_access_token, JWTAuthentication, create_refresh_token, decode_refresh_token
from .models import User, UserToken, Reset
from .serializers import UserSerializers


# For Registration
class RegisterAPIView(APIView):
    def get(self, request):
        xy = UserSerializers(User.objects.all(), many=True).data
        return Response(xy, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data

        if data['password'] != data['password_confirm']:
            raise exceptions.APIException('Password do not match!')

        serializer = UserSerializers(data=data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(serializer.data)


# For Login
class LoginAPIView(APIView):
    def get(self, request):
        xy = UserSerializers(User.objects.all(), many=True).data
        return Response(xy, status=status.HTTP_200_OK)

    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()

        if user is None:
            raise exceptions.AuthenticationFailed('Invalid credential User invalid')

        if not user.check_password(password):
            raise exceptions.AuthenticationFailed('Invalid credential')

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        UserToken.objects.create(
            user_id=user.id,
            token=refresh_token,
            expired_at=datetime.datetime.utcnow() + datetime.timedelta(days=7)
        )

        response = Response()
        response.set_cookie(key='refresh_token', value=refresh_token, httponly=True)
        response.data = {
            'token': access_token
        }
        return response


# For User
class UserAPIView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        return Response(UserSerializers(request.user).data)


# For Refresh
class RefreshAPIView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        id = decode_refresh_token(refresh_token)

        if not UserToken.objects.filter(
            user_id=id,
            token=refresh_token,
            expired_at__gt=datetime.datetime.now(tz=datetime.datetime.utc)
        ).exists():
            raise exceptions.AuthenticationFailed('Unauthenticated')

        access_token = create_access_token(id)

        return Response({
            'token': access_token
        })


# For Logout
class LogoutAPIView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        UserToken.objects.filter(token=refresh_token).delete()

        response = Response()
        response.delete_cookie(key='refresh_token')
        response.data = {
            'message': 'success'
        }
        return response


# For Forgot
class ForgotAPIView(APIView):
    def post(self, request):
        email = request.data['email']
        token = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))

        Reset.objects.create(
            email=email,
            token=token
        )

        url = 'http://localhost:3000/reset/' + token

        send_mail(
            subject='Reset your Password!',
            message='Click <a href="%s"> here </a> to reset your password!' % url,
            from_email='from@example.com',
            recipient_list=[email]
        )

        return Response({
            'message': 'success'
        })


# For Reset
class ResetAPIView(APIView):
    def post(self, request):
        data = request.data

        if data['password'] != data['password_confirm']:
            raise exceptions.APIException('Password do not match!')

        reset_password = Reset.objects.filter(token=data['token']).first()

        if not reset_password:
            raise exceptions.AuthenticationFailed('Invalid link!')

        user = User.objects.filter(email=reset_password.email).first()

        if not user:
            raise exceptions.AuthenticationFailed('User not found!')

        user.set_password(data['password'])
        user.save()

        return Response({
            'message': 'success'
        })

