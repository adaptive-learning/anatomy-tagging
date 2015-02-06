from models import Image, Path, Term, Category, Bbox
from django.contrib import admin


class ImageAdmin(admin.ModelAdmin):
    list_display = ('filename', 'name_cs', 'textbook_page')


class PathAdmin(admin.ModelAdmin):
    list_display = ('image', 'color', 'opacity')


class TermAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name_cs', 'name_en')


class BboxAdmin(admin.ModelAdmin):
    list_display = ('x', 'y', 'width', 'height')


class CategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Image, ImageAdmin)
admin.site.register(Path, PathAdmin)
admin.site.register(Term, TermAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Bbox, BboxAdmin)
