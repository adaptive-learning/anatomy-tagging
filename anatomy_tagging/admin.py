from models import Image, Path, Term, Category, Bbox, Relation, RelationType, CompositeRelationType
from django.contrib import admin


class ImageAdmin(admin.ModelAdmin):
    search_fields = ('name_cs', 'name_en')
    list_display = ('filename', 'name_cs', 'bbox', 'category', 'textbook_page', 'body_part')
    list_filter = ('category',)


class PathAdmin(admin.ModelAdmin):
    list_display = ('image', 'term', 'bbox', 'color', 'opacity')
    search_fields = ('image__name_cs', 'image__name_en', 'term__name_la', 'term__name_en')


class TermAdmin(admin.ModelAdmin):
    search_fields = ('name_la', 'name_cs', 'name_en', 'code', 'slug')
    list_display = ('name_la', 'name_cs', 'name_en', 'parent', 'body_part')


class BboxAdmin(admin.ModelAdmin):
    list_display = ('x', 'y', 'width', 'height')


class RelationTypeAdmin(admin.ModelAdmin):
    pass


class CompositeRelationTypeAdmin(admin.ModelAdmin):

    list_display = ('name_en', 'name_cs', 'ready', 'definition')


class CategoryAdmin(admin.ModelAdmin):
    pass


class RelationAdmin(admin.ModelAdmin):
    list_display = ('type', 'term1', 'term2', 'text1', 'text2')
    search_fields = (
        'term1__name_en', 'term2__name_en',
        'term1__name_la', 'term2__name_la',
        'term1__name_cs', 'term2__name_cs',
        'text1', 'text2')
    list_filter = ('type__identifier', 'type__source')
    raw_id_fields = ('term1', 'term2')


admin.site.register(Image, ImageAdmin)
admin.site.register(Path, PathAdmin)
admin.site.register(Term, TermAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Bbox, BboxAdmin)
admin.site.register(Relation, RelationAdmin)
admin.site.register(RelationType, RelationTypeAdmin)
admin.site.register(CompositeRelationType, CompositeRelationTypeAdmin)
