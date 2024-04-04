from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    telegram_id = models.IntegerField('Айди телеграмма', blank=False)
    paronim = models.CharField('Отчество', blank=True, max_length=100)
