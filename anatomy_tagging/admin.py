from models import Image, Path, Term, Category
from django.contrib import admin


class ImageAdmin(admin.ModelAdmin):
    list_display = ('name_cs', 'filename', 'textbook_page')


class PathAdmin(admin.ModelAdmin):
    list_display = ('image', 'color', 'opacity')


class TermAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name_cs', 'name_en')


class CategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Image, ImageAdmin)
admin.site.register(Path, PathAdmin)
admin.site.register(Term, TermAdmin)
admin.site.register(Category, CategoryAdmin)
