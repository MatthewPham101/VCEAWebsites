from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth.models import BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MaxValueValidator, MinValueValidator




class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(("email address"), unique = True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    first_name = models.CharField(max_length=30, blank=False)  
    last_name = models.CharField(max_length=30, blank=False)  
    is_admin = models.BooleanField(default=False)
    is_student = models.BooleanField(default=True)
    is_tutor = models.BooleanField(default=False)
    objects = CustomUserManager()


class Major(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20, default="placeholder")

    def __str__(self):
        return self.abbreviation

class Admin(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True)
    
class Tutor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True)
    minutes_tutored = models.IntegerField(default=0)
    day_started = models.DateField(max_length=20, null=True)
    rating = models.FloatField(default=0, validators=[MaxValueValidator(5.0), MinValueValidator(0.0)])
    description = models.TextField(blank=True, null=True)
    major = models.ForeignKey(Major, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name

class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True)
    
#connect the relationship to the student, tutor, and admin
@receiver(post_save, sender=CustomUser)
def manage_user_profile(sender, instance, created, **kwargs):
    # Handle new user creation
    if created:
        if instance.is_student:
            Student.objects.create(user=instance)
        elif instance.is_admin:
            Admin.objects.create(user=instance)
        elif instance.is_tutor:
            Tutor.objects.create(user=instance)
        return

    # Handle role changes for existing users
    if instance.is_student:
        Student.objects.get_or_create(user=instance)
        Admin.objects.filter(user=instance).delete()
        Tutor.objects.filter(user=instance).delete()
    elif instance.is_admin:
        Admin.objects.get_or_create(user=instance)
        Student.objects.filter(user=instance).delete()
        Tutor.objects.filter(user=instance).delete()
    elif instance.is_tutor:
        Tutor.objects.get_or_create(user=instance)
        Student.objects.filter(user=instance).delete()
        Admin.objects.filter(user=instance).delete()


class Class(models.Model):
    class_major = models.ForeignKey(Major, on_delete=models.CASCADE)
    course_num = models.IntegerField()
    course_name = models.CharField(max_length=100, null=True)
    available_tutors = models.ManyToManyField(Tutor, related_name="tutored_classes")
    hours_tutored = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.class_major.abbreviation} {self.course_num}"


class TutoringSession(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='appointments')
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    tutored_class = models.ForeignKey(Class, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.student} session with {self.tutor} on {self.date} at {self.start_time}"
