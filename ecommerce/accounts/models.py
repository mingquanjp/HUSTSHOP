from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        if not username:
            raise ValueError('Username is required')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 3)  # 3 = Manager

        return self.create_user(email, username, password, **extra_fields)

class Account(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        (1, 'Customer'),
        (2, 'Staff'),
        (3, 'Manager'),
    )

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be in format: '+999999999'. Up to 15 digits allowed."
    )

    # Thông tin đăng nhập
    email = models.EmailField(unique=True, verbose_name='Email')
    username = models.CharField(max_length=50, unique=True, verbose_name='Username')

    # Thông tin cá nhân
    first_name = models.CharField(max_length=50, verbose_name='First Name')
    last_name = models.CharField(max_length=50, verbose_name='Last Name')
    phone_number = models.CharField(
        max_length=17,
        validators=[phone_regex],
        blank=True,
        verbose_name='Phone Number'
    )
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, default=1, verbose_name='Role')
    dob = models.DateField(null=True, blank=True, verbose_name='Date of Birth')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, verbose_name='Gender')
    address = models.TextField(blank=True, verbose_name='Address')

    # Trường hệ thống
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name='Date Joined')
    last_login = models.DateTimeField(auto_now=True, verbose_name='Last Login')  # Sửa thành auto_now
    is_staff = models.BooleanField(default=False, verbose_name='Is Staff')
    is_active = models.BooleanField(default=True, verbose_name='Is Active')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_role_name(self):
        return dict(self.ROLE_CHOICES).get(self.role, 'Unknown')



