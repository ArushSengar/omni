from django.db import models

class GrowthPost(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SCHEDULED', 'Scheduled'),
        ('PUBLISHED', 'Published'),
        ('FAILED', 'Failed'),
    ]

    title = models.CharField(max_length=255)
    domain = models.CharField(max_length=100, default='Cyber Security & Systems')
    source = models.CharField(max_length=100, default='assignment')
    linkedin_content = models.TextField(blank=True)
    twitter_content = models.TextField(blank=True)
    image_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PUBLISHED')
    linkedin_urn = models.CharField(max_length=255, blank=True)
    twitter_url = models.CharField(max_length=255, blank=True)
    likes = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"


class ResearchTopic(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    technical_problem = models.TextField()
    commands = models.TextField(blank=True)
    solution = models.TextField()
    impact = models.CharField(max_length=255, blank=True)
    tags = models.CharField(max_length=255, blank=True)
    is_used = models.BooleanField(default=False)
    researched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-researched_at']

    def __str__(self):
        return f"[{self.category}] {self.title}"


class SystemStatus(models.Model):
    pi_uptime = models.CharField(max_length=100, blank=True)
    pi_ram_free = models.CharField(max_length=100, blank=True)
    omniroute_status = models.CharField(max_length=50, default="Active")
    last_sync = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pi Status @ {self.last_sync}"


class WeeklyGrowthReview(models.Model):
    period_label = models.CharField(max_length=100)
    total_posts = models.IntegerField(default=0)
    total_views = models.IntegerField(default=0)
    total_likes = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)
    avg_views = models.FloatField(default=0.0)
    engagement_rate = models.FloatField(default=0.0)
    growth_status = models.CharField(max_length=100, default="Steady Progress")
    recommendations_json = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review {self.period_label} - {self.growth_status}"
