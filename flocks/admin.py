from django.contrib import admin

from .models import Flock, FeedLog, HealthLog, EggCollection


@admin.register(Flock)
class FlockAdmin(admin.ModelAdmin):
    list_display = ('name', 'breed', 'status', 'farm', 'start_date', 'end_date', 'current_quantity')
    list_filter = ('status', 'farm', 'closure_reason')
    search_fields = ('name', 'breed')
    readonly_fields = (
        'total_eggs_collected', 'total_feed_kg', 'total_feed_cost',
        'total_health_cost', 'total_mortality', 'total_income', 'total_expense',
    )


admin.site.register(FeedLog)
admin.site.register(HealthLog)
admin.site.register(EggCollection)
