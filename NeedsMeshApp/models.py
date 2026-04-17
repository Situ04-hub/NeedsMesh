from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ---------------------------------------------------------------------------
# Role choices
# ---------------------------------------------------------------------------
ROLE_CHOICES = [
    ('admin', 'Organisation Admin'),
    ('field_worker', 'Field Worker'),
    ('volunteer', 'Volunteer'),
]

STATUS_CHOICES = [
    ('open', 'Open'),
    ('assigned', 'Assigned'),
    ('resolved', 'Resolved'),
    ('killed', 'Killed'),
]

URGENCY_CHOICES = [(i, str(i)) for i in range(1, 11)]

CATEGORY_CHOICES = [
    ('food', 'Food & Nutrition'),
    ('health', 'Health & Medical'),
    ('education', 'Education'),
    ('shelter', 'Shelter & Housing'),
    ('water', 'Water & Sanitation'),
    ('livelihood', 'Livelihood & Employment'),
    ('disability', 'Disability Support'),
    ('elderly', 'Elderly Care'),
    ('child', 'Child Welfare'),
    ('environment', 'Environment'),
    ('disaster', 'Disaster Relief'),
    ('other', 'Other'),
]


# ---------------------------------------------------------------------------
# Organisation — a group or NGO managing field workers and problems
# ---------------------------------------------------------------------------
class Organisation(models.Model):
    name = models.CharField(max_length=200, unique=True)
    admin_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='managed_organisation')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# UserProfile — extends Django's built-in User with role, full name, resume
# ---------------------------------------------------------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='volunteer')
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    # Task completion streak data
    completed_tasks = models.PositiveIntegerField(default=0)
    has_badge = models.BooleanField(default=False)
    # Role-specific fields
    organisation = models.ForeignKey(Organisation, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    locality = models.ForeignKey('Locality', on_delete=models.SET_NULL, null=True, blank=True, related_name='profiles')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True, help_text="For Volunteers")
    is_approved = models.BooleanField(default=True)  # New field for workflow approval

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    def save(self, *args, **kwargs):
        # Auto-award badge after 3 completed tasks
        if self.completed_tasks >= 3:
            self.has_badge = True
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Locality — a named area with latitude/longitude for the heatmap
# ---------------------------------------------------------------------------
class Locality(models.Model):
    name = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField(null=True, blank=True, help_text="For heatmap (decimal degrees)")
    longitude = models.FloatField(null=True, blank=True, help_text="For heatmap (decimal degrees)")

    class Meta:
        verbose_name_plural = "Localities"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def average_urgency(self):
        """Computed urgency score across all open problems in this locality."""
        problems = self.communityproblems.filter(status='open')
        if problems.exists():
            return round(sum(p.urgency for p in problems) / problems.count(), 1)
        return 0


# ---------------------------------------------------------------------------
# ProofImage — multiple images per CommunityProblem
# ---------------------------------------------------------------------------
class ProofImage(models.Model):
    image = models.ImageField(upload_to='proof_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.pk}"


# ---------------------------------------------------------------------------
# CommunityProblem — central model
# ---------------------------------------------------------------------------
class CommunityProblem(models.Model):
    submitted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='submitted_problems'
    )
    locality = models.ForeignKey(
        Locality, on_delete=models.SET_NULL, null=True, related_name='communityproblems'
    )
    # Category stored as comma-separated values (multi-select support)
    category = models.CharField(max_length=200)
    problem_statement = models.TextField()
    urgency = models.IntegerField(choices=URGENCY_CHOICES, default=5)
    proof_images = models.ManyToManyField(ProofImage, blank=True)
    detected_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    # Multi-Organisation Hierarchy
    organisation = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL, null=True, blank=True, related_name='problems'
    )
    volunteers_required = models.PositiveIntegerField(default=0, help_text="Set by NGO Admin")

    # After finalisation
    interested_volunteers = models.ManyToManyField(
        User, blank=True, related_name='interested_in'
    )
    selected_volunteers = models.ManyToManyField(
        User, blank=True, related_name='selected_for'
    )
    final_event_date = models.DateTimeField(null=True, blank=True)

    # Resolution fields
    before_after = models.TextField(
        blank=True, help_text="Describe before vs after the intervention"
    )
    total_need = models.TextField(blank=True, help_text="Overall community need summary")
    community_reaction = models.TextField(blank=True, help_text="Community feedback / emoji reactions")

    # Killed flag
    killed_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-urgency', '-created_at']

    def __str__(self):
        return f"{self.locality} | {self.category} | Urgency {self.urgency}"

    def get_category_list(self):
        """Return categories as a Python list."""
        return [c.strip() for c in self.category.split(',') if c.strip()]

    def get_category_display_list(self):
        """Return human-readable category labels."""
        cat_map = dict(CATEGORY_CHOICES)
        return [cat_map.get(c, c) for c in self.get_category_list()]

    def short_statement(self):
        """Teaser (first 100 chars) shown on the Needs Board."""
        return self.problem_statement[:100] + '...' if len(self.problem_statement) > 100 else self.problem_statement

    @property
    def needs_reminder(self):
        """True if urgency >= 8 and no volunteer has offered help within 2 days."""
        if self.urgency >= 8 and not self.interested_volunteers.exists():
            age = timezone.now() - self.created_at
            return age.days >= 2
        return False

    @property
    def is_finalised(self):
        return self.status in ('assigned', 'resolved')


# ---------------------------------------------------------------------------
# SurveySubmission — audit log of each survey submission
# ---------------------------------------------------------------------------
class SurveySubmission(models.Model):
    field_worker = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='survey_submissions'
    )
    problem = models.ForeignKey(
        CommunityProblem, on_delete=models.CASCADE, related_name='submissions'
    )
    submitted_data_json = models.JSONField(default=dict, blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Survey by {self.field_worker.username} on {self.submission_date:%Y-%m-%d}"


# ---------------------------------------------------------------------------
# Notification — in-app dashboard alerts
# ---------------------------------------------------------------------------
class Notification(models.Model):
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message[:40]}"

# ---------------------------------------------------------------------------
# ProblemMessage — in-app communication for a specific problem
# ---------------------------------------------------------------------------
class ProblemMessage(models.Model):
    problem = models.ForeignKey(CommunityProblem, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
        
    def __str__(self):
        return f"Msg by {self.sender.username} on {self.problem.pk}"


# ---------------------------------------------------------------------------
# PasswordResetOTP — OTP-based password reset
# ---------------------------------------------------------------------------
class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_otps')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.username} at {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def is_expired(self):
        """OTP expires after 10 minutes."""
        return (timezone.now() - self.created_at).total_seconds() > 600
