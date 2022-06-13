from rest_framework import exceptions, status
from rest_framework.views import APIView
from rest_framework.views import Response

from .authentication import create_access_token
from .models import User
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
        refresh_token = create_access_token(user.id)

        response = Response()
        response.set_cookie(key='refresh_token', value=refresh_token, httponly=True)
        response.data = {
            'token': access_token
        }
        return response







