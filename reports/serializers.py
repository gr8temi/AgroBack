from rest_framework import serializers
from .models import ReportConfig, Question, DailyReport, ReportAnswer

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'is_required', 'input_type', 'sort_order']

class ReportConfigSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ReportConfig
        fields = ['id', 'is_enabled', 'deadline_time', 'questions']

class ReportAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    
    class Meta:
        model = ReportAnswer
        fields = ['id', 'question', 'question_text', 'answer_text', 'answer_number', 'answer_date', 'answer_boolean']

class DailyReportSerializer(serializers.ModelSerializer):
    answers = ReportAnswerSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = DailyReport
        fields = ['id', 'reference_date', 'submitted_at', 'user', 'user_name', 'answers']

class DailyReportSubmissionSerializer(serializers.ModelSerializer):
    answers = serializers.ListField(write_only=True)

    class Meta:
        model = DailyReport
        fields = ['reference_date', 'answers']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        # user and farm are injected into validated_data by perform_create
        
        report = DailyReport.objects.create(**validated_data)
        
        for ans in answers_data:
            question_id = ans.get('question_id')
            # Determine which field to save based on value type or question type
            # For simplicity, we expect the FE to send specific keys or we infer
            # But simpler: FE sends 'value' and we put it in right column?
            # Or FE sends 'answer_text', 'answer_number' etc.
            
            ReportAnswer.objects.create(
                report=report,
                question_id=question_id,
                answer_text=ans.get('answer_text'),
                answer_number=ans.get('answer_number'),
                answer_date=ans.get('answer_date')
            )
        return report
