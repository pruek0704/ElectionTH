# voting/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """ใช้ทั้ง Admin และ Citizen — แยกด้วย is_staff"""
    national_id = models.CharField(
        max_length=13, blank=True, verbose_name='เลขบัตรประชาชน'
    )
    district = models.CharField(
        max_length=100, default='เขต 1', verbose_name='เขตเลือกตั้ง'
    )

    class Meta:
        verbose_name = 'ผู้ใช้งาน'


class Party(models.Model):
    name       = models.CharField(max_length=200, unique=True)
    short_name = models.CharField(max_length=50, blank=True)
    ideology   = models.CharField(max_length=200, blank=True)
    color      = models.CharField(max_length=7, default='#1a56db')
    logo_emoji = models.CharField(max_length=10, default='🗳️')
    vote_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-vote_count']

    def __str__(self):
        return self.name


class Candidate(models.Model):
    full_name        = models.CharField(max_length=200)
    party            = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='candidates')
    district         = models.CharField(max_length=100)
    candidate_number = models.PositiveIntegerField()
    vote_count       = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['candidate_number']
        unique_together = [['district', 'candidate_number']]

    def __str__(self):
        return f"หมายเลข {self.candidate_number} — {self.full_name}"


class VoteUsage(models.Model):
    VOTE_TYPE = [
        ('constituency', 'ส.ส. เขต'),
        ('party', 'พรรคการเมือง'),
    ]
    citizen  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vote_usages')
    vote_type = models.CharField(max_length=20, choices=VOTE_TYPE)
    voted_at  = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [['citizen', 'vote_type']]  # ป้องกันโหวตซ้ำระดับ DB

    def __str__(self):
        return f"{self.citizen.get_full_name()} | {self.get_vote_type_display()}"