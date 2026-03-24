# voting/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone


class CitizenManager(BaseUserManager):
    def create_user(self, national_id, full_name, password=None, **extra_fields):
        if not national_id:
            raise ValueError('ต้องระบุเลขบัตรประชาชน')
        user = self.model(national_id=national_id, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class Citizen(AbstractBaseUser):
    """ประชาชนผู้มีสิทธิเลือกตั้ง"""
    national_id = models.CharField(
        max_length=13, unique=True, verbose_name='เลขบัตรประชาชน'
    )
    full_name = models.CharField(max_length=200, verbose_name='ชื่อ-นามสกุล')
    district = models.CharField(
        max_length=100, verbose_name='เขตเลือกตั้ง', default='เขต 1'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CitizenManager()

    USERNAME_FIELD = 'national_id'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        verbose_name = 'ประชาชน'
        verbose_name_plural = 'ประชาชน'

    def __str__(self):
        return f"{self.full_name} ({self.national_id})"


class Party(models.Model):
    """พรรคการเมือง"""
    name = models.CharField(max_length=200, unique=True, verbose_name='ชื่อพรรค')
    short_name = models.CharField(max_length=50, verbose_name='ชื่อย่อ', blank=True)
    ideology = models.CharField(max_length=200, verbose_name='อุดมการณ์', blank=True)
    color = models.CharField(max_length=7, default='#1a56db', verbose_name='สีพรรค')
    logo_emoji = models.CharField(max_length=10, default='🗳️', verbose_name='ไอคอน')
    vote_count = models.PositiveIntegerField(default=0, verbose_name='คะแนนเสียง')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'พรรคการเมือง'
        verbose_name_plural = 'พรรคการเมือง'
        ordering = ['-vote_count']

    def __str__(self):
        return self.name


class Candidate(models.Model):
    """ผู้สมัคร ส.ส. เขต"""
    full_name = models.CharField(max_length=200, verbose_name='ชื่อ-นามสกุล')
    party = models.ForeignKey(
        Party, on_delete=models.CASCADE,
        related_name='candidates', verbose_name='สังกัดพรรค'
    )
    district = models.CharField(max_length=100, verbose_name='เขตเลือกตั้ง')
    candidate_number = models.PositiveIntegerField(verbose_name='หมายเลขผู้สมัคร')
    bio = models.TextField(blank=True, verbose_name='ประวัติย่อ')
    vote_count = models.PositiveIntegerField(default=0, verbose_name='คะแนนเสียง')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'ผู้สมัคร ส.ส.'
        verbose_name_plural = 'ผู้สมัคร ส.ส.'
        ordering = ['candidate_number']
        unique_together = [['district', 'candidate_number']]

    def __str__(self):
        return f"หมายเลข {self.candidate_number} - {self.full_name} ({self.party.name})"


class VoteUsage(models.Model):
    """
    ตารางบันทึกว่าประชาชนคนใดใช้สิทธิ์ไปแล้วหรือยัง
    *** ไม่บันทึกว่าโหวตให้ใคร เพื่อรักษาความลับ ***
    """
    VOTE_TYPE_CHOICES = [
        ('constituency', 'ส.ส. เขต'),
        ('party', 'พรรคการเมือง'),
    ]

    citizen = models.ForeignKey(
        Citizen, on_delete=models.CASCADE,
        related_name='vote_usages', verbose_name='ประชาชน'
    )
    vote_type = models.CharField(
        max_length=20, choices=VOTE_TYPE_CHOICES, verbose_name='ประเภทการเลือกตั้ง'
    )
    voted_at = models.DateTimeField(default=timezone.now, verbose_name='เวลาที่ลงคะแนน')

    class Meta:
        verbose_name = 'ประวัติการใช้สิทธิ์'
        verbose_name_plural = 'ประวัติการใช้สิทธิ์'
        # ป้องกันการโหวตซ้ำ
        unique_together = [['citizen', 'vote_type']]

    def __str__(self):
        return f"{self.citizen.full_name} | {self.get_vote_type_display()} | {self.voted_at:%d/%m/%Y %H:%M}"