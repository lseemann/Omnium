from galena.models import Field, Rider, Result, Race
from django.contrib import admin

class ResultAdmin(admin.ModelAdmin):
	search_fields = ['lname','fname','field__full','race__full']
	list_display = ('lname','field','race','place')

class RiderAdmin(admin.ModelAdmin):
  search_fields = ['lname','fname','team']
  list_display = ('lname','team','field','omnium','dq')

admin.site.register(Field)
admin.site.register(Result,ResultAdmin)
admin.site.register(Rider, RiderAdmin)
admin.site.register(Race)
