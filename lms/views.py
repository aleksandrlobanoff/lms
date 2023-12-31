from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated

from lms import services
from lms.models import Course, Lesson, Payments, CourseSubscription
from lms.paginators import CoursePaginator, LessonPaginator
from lms.permissions import IsStaff, IsOwner
from lms.serializers import CourseSerializer, LessonSerializer, PaymentsSerializer, CourseSubscriptionSerializer
from lms.tasks import send_email_course_update


class CourseViewSet(viewsets.ModelViewSet):
    """ Класс для работы с представлением курсов"""

    serializers_class = CourseSerializer
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated, IsStaff | IsOwner]

    pagination_class = CoursePaginator

    def perform_create(self, serializer):
        new_course = serializer.save()
        new_course.owner = self.request.user
        new_course.save()

    def perform_update(self, serializer):
        updated_course = serializer.save()
        send_email_course_update.delay(updated_course.pk)


class LessonCreateAPIView(generics.CreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsStaff]

    def perform_create(self, serializer):
        new_lesson = serializer.save()
        new_lesson.owner = self.request.user
        new_lesson.save()


class LessonListAPIView(generics.ListAPIView):
    """
       Класс представления для списка занятий.
    """
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsOwner | IsStaff]

    pagination_class = LessonPaginator


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """
    Класс представления для получения информации об уроке.
    """
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsOwner | IsStaff]


class LessonUpdateAPIView(generics.UpdateAPIView):
    """
      Класс представления для обновления информации об уроке.
    """
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsOwner | IsStaff]


class LessonDestroyAPIView(generics.DestroyAPIView):
    """
        Класс представления для удаления урока.
    """
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated, IsOwner, IsStaff]


class PaymentsListAPIView(generics.ListAPIView):
    """
        Класс представления для списка платежей.
    """
    serializer_class = PaymentsSerializer
    queryset = Payments.objects.all()
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ('paid_course', 'paid_lesson', 'payment_method')
    ordering_fields = ('date',)


class PaymentsCreateAPIView(generics.CreateAPIView):
    def create(self, request, *args, **kwargs):
        number = request.data['card_number']
        exp_month = request.data['card_exp_month']
        exp_year = request.data['card_exp_year']
        cvc = request.data['card_cvc']
        bill_id = services.create_payment(1000, 'usd')
        status = services.make_payment(bill_id, number, exp_month, exp_year, cvc)
        return Response({'status': status})


class CourseSubsriptionCreateApiView(generics.CreateAPIView):
    """
       Класс представления для создания подписки на курс.
    """
    serializer_class = CourseSubscriptionSerializer


class CourseSubscriptionDeleteApiView(generics.DestroyAPIView):
    """
       Класс представления для удаления подписки на курс.
    """
    serializer_class = CourseSubscriptionSerializer
    queryset = CourseSubscription.objects.all()
