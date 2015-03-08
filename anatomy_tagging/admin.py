from models import Image, Path, Term, Category, Bbox
from django.contrib import admin


class ImageAdmin(admin.ModelAdmin):
    search_fields = ('name_cs', 'name_en')
    list_display = ('filename', 'name_cs', 'bbox', 'category', 'textbook_page')
    list_filter = ('category',)


class PathAdmin(admin.ModelAdmin):
    list_display = ('image', 'term', 'bbox', 'color', 'opacity')


class TermAdmin(admin.ModelAdmin):
    search_fields = ('name_la', 'name_cs', 'name_en')
    list_display = ('name_la', 'name_cs', 'name_en', 'parent', 'body_part')


class BboxAdmin(admin.ModelAdmin):
    list_display = ('x', 'y', 'width', 'height')


class CategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Image, ImageAdmin)
admin.site.register(Path, PathAdmin)
admin.site.register(Term, TermAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Bbox, BboxAdmin)
