from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status, serializers

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.db.models import Count, Q

import random

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Event, EmailOTP, Enrollment
from .serializers import EventSerializer, SignupSerializer
from .permissions import IsFacilitator, IsSeeker

User = get_user_model()

OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3


# 🔐 Custom JWT to block unverified users
class CustomTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_active:
            raise serializers.ValidationError("Email not verified.")
        return data


class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer


# 📝 Signup + send OTP
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save(is_active=False)

        otp = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

        EmailOTP.objects.update_or_create(
            user=user,
            defaults={
                "otp": otp,
                "expires_at": expires_at,
                "attempts": 0,
                "is_verified": False
            }
        )

        send_mail(
            subject="Your OTP Verification Code",
            message=f"Your OTP is {otp}. It expires in {OTP_EXPIRY_MINUTES} minutes.",
            from_email="noreply@example.com",
            recipient_list=[user.email],
            fail_silently=True,
        )

        return Response(
            {"message": "User created. OTP sent to email."},
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Verify OTP
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    email = request.data.get("email")
    otp = request.data.get("otp")

    if not email or not otp:
        return Response(
            {"detail": "Email and OTP are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = get_object_or_404(User, email=email)
    otp_obj = get_object_or_404(EmailOTP, user=user, is_verified=False)

    if otp_obj.expires_at < timezone.now():
        return Response({"detail": "OTP expired."}, status=400)

    if otp_obj.attempts >= MAX_OTP_ATTEMPTS:
        return Response({"detail": "Maximum OTP attempts exceeded."}, status=400)

    if otp_obj.otp != otp:
        otp_obj.attempts += 1
        otp_obj.save()
        return Response({"detail": "Invalid OTP."}, status=400)

    otp_obj.is_verified = True
    otp_obj.save()

    user.is_active = True
    user.save()

    return Response(
        {"message": "Email verified. You can login now."},
        status=status.HTTP_200_OK
    )


# 👨‍🏫 Facilitator: my events with stats
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsFacilitator])
def my_events(request):
    events = Event.objects.filter(created_by=request.user).annotate(
        total_enrollments=Count('enrollments', filter=Q(enrollments__status='enrolled'))
    )

    data = []
    for e in events:
        available = None
        if e.capacity is not None:
            available = max(e.capacity - e.total_enrollments, 0)

        data.append({
            "id": e.id,
            "title": e.title,
            "starts_at": e.starts_at,
            "capacity": e.capacity,
            "total_enrollments": e.total_enrollments,
            "available_seats": available
        })

    return Response(data)


# 📄 List events
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_events(request):
    events = Event.objects.all()
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)


# 🔎 Search & filter events
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_events(request):
    qs = Event.objects.all()

    location = request.GET.get('location')
    language = request.GET.get('language')
    starts_after = request.GET.get('starts_after')
    starts_before = request.GET.get('starts_before')
    q = request.GET.get('q')

    if location:
        qs = qs.filter(location__icontains=location)
    if language:
        qs = qs.filter(language__icontains=language)
    if starts_after:
        qs = qs.filter(starts_at__gte=starts_after)
    if starts_before:
        qs = qs.filter(starts_at__lte=starts_before)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    qs = qs.order_by('starts_at')
    serializer = EventSerializer(qs, many=True)
    return Response(serializer.data)


# ➕ Create event
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsFacilitator])
def create_event(request):
    serializer = EventSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✏️ Update event
@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsFacilitator])
def update_event(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if event.created_by != request.user:
        return Response(
            {"detail": "You can only update your own events."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = EventSerializer(event, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 🗑️ Delete event
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsFacilitator])
def delete_event(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if event.created_by != request.user:
        return Response(
            {"detail": "You can only delete your own events."},
            status=status.HTTP_403_FORBIDDEN
        )

    event.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# 🔍 Event detail
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    serializer = EventSerializer(event)
    return Response(serializer.data)


# 🎟️ Seeker: enroll in event
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSeeker])
def enroll_event(request, pk):
    event = get_object_or_404(Event, pk=pk)

    active_count = Enrollment.objects.filter(
        event=event, status='enrolled'
    ).count()

    if event.capacity and active_count >= event.capacity:
        return Response({"detail": "Event is full."}, status=400)

    enrollment, created = Enrollment.objects.get_or_create(
        event=event,
        seeker=request.user,
        defaults={"status": "enrolled"}
    )

    if not created and enrollment.status == 'enrolled':
        return Response({"detail": "Already enrolled."}, status=400)

    enrollment.status = 'enrolled'
    enrollment.save()
    return Response({"message": "Enrolled successfully."}, status=200)


# ❌ Seeker: cancel enrollment
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSeeker])
def cancel_enrollment(request, pk):
    enrollment = get_object_or_404(
        Enrollment,
        event_id=pk,
        seeker=request.user,
        status='enrolled'
    )
    enrollment.status = 'canceled'
    enrollment.save()
    return Response({"message": "Enrollment canceled."}, status=200)


# 📋 Seeker: upcoming enrollments
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSeeker])
def my_upcoming_enrollments(request):
    qs = Enrollment.objects.filter(
        seeker=request.user,
        status='enrolled',
        event__starts_at__gte=timezone.now()
    ).select_related('event')

    data = [{
        "event_id": e.event.id,
        "title": e.event.title,
        "starts_at": e.event.starts_at,
        "location": e.event.location,
    } for e in qs]

    return Response(data)


# 🕒 Seeker: past enrollments
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSeeker])
def my_past_enrollments(request):
    qs = Enrollment.objects.filter(
        seeker=request.user,
        status='enrolled',
        event__ends_at__lt=timezone.now()
    ).select_related('event')

    data = [{
        "event_id": e.event.id,
        "title": e.event.title,
        "ended_at": e.event.ends_at,
    } for e in qs]

    return Response(data)
