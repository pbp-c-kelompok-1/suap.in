from django.db import models
from django.contrib.auth.models import User


class University(models.Model):
    name = models.CharField(max_length=150, unique=True)
    short_name = models.CharField(max_length=20, unique=True)
    city = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.short_name

    class Meta:
        ordering = ['short_name']
        verbose_name_plural = 'Universities'


class CampusMembership(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='campus')
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='members')
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} @ {self.university.short_name}"


class Canteen(models.Model):
    name = models.CharField(max_length=100)
    faculty = models.CharField(max_length=50)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='canteens')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_m = models.PositiveIntegerField(default=150)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.faculty})"

    class Meta:
        ordering = ['faculty', 'name']


class CommunityPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_posts')
    photo = models.ImageField(upload_to='community/%Y/%m/', blank=True)
    # Foto data awal (showcase) disimpan sebagai file static di repo, bukan di media/,
    # supaya selalu ikut ter-deploy. Isinya path relatif static, contoh 'social/seed/kancil_1.jpg'.
    seed_image = models.CharField(max_length=200, blank=True)
    food_logs = models.ManyToManyField('scanner.FoodLog', blank=True, related_name='community_posts')
    total_co2_grams = models.FloatField(default=0)
    canteen = models.ForeignKey(Canteen, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    custom_location = models.CharField(max_length=100, blank=True)
    food_name = models.CharField(max_length=100, blank=True)
    price = models.PositiveIntegerField(null=True, blank=True)
    is_shared = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.food_name or 'Tanpa nama'}"

    class Meta:
        ordering = ['-created_at']


class PostReport(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_reports')
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Laporan {self.user.username} untuk post #{self.post_id}"

    class Meta:
        unique_together = ['post', 'user']


class Friendship(models.Model):
    """Satu baris = satu hubungan antara dua user (arah: pengirim -> penerima)."""

    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Menunggu'),
        (ACCEPTED, 'Berteman'),
        (REJECTED, 'Ditolak'),
    ]

    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_received')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"

    def other(self, user):
        return self.to_user if self.from_user_id == user.id else self.from_user

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['from_user', 'to_user'], name='unique_friend_request'),
        ]
