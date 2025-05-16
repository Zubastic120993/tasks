from django.contrib import admin
from .models import Task, Category
from django.contrib.auth.models import User

# Register your models here.
admin.site.unregister(User)
 

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'completed', 'created_at', 'due_date')
    list_filter = ('priority', 'completed')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_per_page = 10


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active')
    search_fields = ('username', 'email')
    list_per_page = 10

