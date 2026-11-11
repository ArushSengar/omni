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
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['domain']),
        ]

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
        indexes = [
            models.Index(fields=['-researched_at']),
            models.Index(fields=['category']),
            models.Index(fields=['is_used']),
        ]

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
        indexes = [
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Review {self.period_label} - {self.growth_status}"


class VaultResource(models.Model):
    SAFETY_CHOICES = [
        ('SAFE', 'Safe / Verified'),
        ('PENTEST_ONLY', 'Pentest / Authorized Lab Only'),
        ('CAUTION', 'Caution / Privacy Caveats'),
        ('SUSPICIOUS', 'Suspicious / Untrusted'),
    ]

    title = models.CharField(max_length=255)
    url = models.CharField(max_length=500, blank=True)
    one_liner = models.CharField(max_length=400, help_text="Punchy 1-line purpose in simple Hindi/English")
    category = models.CharField(max_length=100, default="AI & LLM Tools")
    subcategory = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=300, blank=True)
    detailed_summary = models.TextField(blank=True)
    how_to_use = models.TextField(blank=True)
    safety_status = models.CharField(max_length=50, choices=SAFETY_CHOICES, default='SAFE')
    safety_notes = models.CharField(max_length=400, blank=True)
    source_type = models.CharField(max_length=50, default='screenshot')
    raw_ocr_text = models.TextField(blank=True)
    image_path = models.CharField(max_length=500, blank=True)
    favorite = models.BooleanField(default=False)
    rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['subcategory']),
            models.Index(fields=['category', 'subcategory']),
            models.Index(fields=['safety_status']),
            models.Index(fields=['favorite']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"[{self.category}] {self.title}"


class JobOpportunity(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New Match'),
        ('REVIEWED', 'Reviewed'),
        ('APPLIED', 'Applied'),
        ('INTERVIEW', 'Interview'),
        ('ARCHIVED', 'Archived'),
    ]

    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, default='Remote')
    url = models.CharField(max_length=500, blank=True)
    source = models.CharField(max_length=100, default='RemoteOK')
    role_type = models.CharField(max_length=100, default='Cybersecurity')
    match_score = models.IntegerField(default=75)
    matched_skills = models.CharField(max_length=300, blank=True)
    salary = models.CharField(max_length=100, blank=True)
    summary = models.TextField(blank=True)
    tailored_pitch = models.TextField(blank=True, help_text="Bespoke human cover note tailored to Arush's profile")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='NEW')
    detected_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-match_score', '-detected_at']
        indexes = [
            models.Index(fields=['-match_score']),
            models.Index(fields=['status']),
            models.Index(fields=['role_type']),
            models.Index(fields=['-detected_at']),
        ]

    @property
    def skills_list(self):
        """Returns clean list of matched skills without trailing commas or spaces."""
        if not self.matched_skills:
            return []
        return [s.strip() for s in self.matched_skills.split(',') if s.strip()]

    @property
    def is_high_match(self):
        """Returns True if role match score is 80% or higher."""
        return self.match_score >= 80

    def __str__(self):
        return f"[{self.match_score}%] {self.title} @ {self.company}"


