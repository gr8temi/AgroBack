from django.db import models
from core.models import Farm, User

class ReportConfig(models.Model):
    farm = models.OneToOneField(Farm, on_delete=models.CASCADE, related_name='report_config')
    is_enabled = models.BooleanField(default=False)
    deadline_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ReportConfig for {self.farm.name}"

class Question(models.Model):
    QUESTION_TYPES = (
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Yes/No'),
    )
    INPUT_TYPES = (
        ('default', 'Default'),
        ('custom', 'Custom'),
    )

    config = models.ForeignKey(ReportConfig, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='text')
    is_required = models.BooleanField(default=True)
    input_type = models.CharField(max_length=20, choices=INPUT_TYPES, default='custom')
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.text

class DailyReport(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='daily_reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reports')
    reference_date = models.DateField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('farm', 'reference_date')
        ordering = ['-reference_date']

    def __str__(self):
        return f"Report {self.reference_date} - {self.farm.name}"

class ReportAnswer(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(null=True, blank=True)
    answer_number = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    answer_date = models.DateField(null=True, blank=True)
    answer_boolean = models.BooleanField(null=True, blank=True)
    
    def __str__(self):
        return f"Answer to {self.question.text}"
