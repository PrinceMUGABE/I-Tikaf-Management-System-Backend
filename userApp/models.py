from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.timezone import now


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, role, email=None, password=None, status=False, 
                   first_name=None, middle_name=None, last_name=None):
        if not phone_number:
            raise ValueError("The phone number must be provided")
        if not role:
            raise ValueError("The role must be provided")
        if role not in [choice[0] for choice in CustomUser.ROLE_CHOICES]:
            raise ValueError("Invalid role selected")

        # If role is 'admin', email must be provided
        if role == 'imam' and not email:
            raise ValueError("The email must be provided for admin users")

        user = self.model(
            phone_number=phone_number,
            role=role,
            status=status,
            first_name=first_name or '',
            middle_name=middle_name or '',
            last_name=last_name or ''
        )
        
        if email:
            email = self.normalize_email(email)
            user.email = email
        
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, middle_name, last_name, phone_number, email, password=None):
        if not phone_number:
            raise ValueError("The phone number must be provided for superuser")
        if not email:
            raise ValueError("The email must be provided for superuser")
        if not password:
            raise ValueError("The password must be provided for superuser")
        if not first_name:
            raise ValueError("The First name must be provided for superuser")
        if not last_name:
            raise ValueError("The Last name must be provided for superuser")
        
        
        user = self.create_user(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            phone_number=phone_number,
            role='imam',
            email=email,
            status=True,
            password=password
        )
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

    def create_customer(self, phone_number, email=None, password=None, 
                       first_name=None, middle_name=None, last_name=None):
        if not phone_number:
            raise ValueError("The phone number must be provided for customer")
        if not password:
            raise ValueError("The password must be provided for customer")

        user = self.create_user(
            phone_number=phone_number,
            role='participant',
            email=email,
            password=password,
            status=False,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name
        )
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('imam', 'Imam'),
        ('participant', 'Participant')
    ]

    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=now)
    first_name = models.CharField(max_length=50, blank=True, null=True, default='')
    middle_name = models.CharField(max_length=50, blank=True, null=True, default='')
    last_name = models.CharField(max_length=50, blank=True, null=True, default='')


    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email'] 

    objects = CustomUserManager()

    def __str__(self):
        return self.phone_number

    def has_perm(self, perm, obj=None):
        return self.is_admin if hasattr(self, 'is_admin') else False

    def has_module_perms(self, app_label):
        return self.is_admin if hasattr(self, 'is_admin') else False
