# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations
import json as simplejson

QUESTIONS = {
    'nerve': {
        'cs': {
            't2ts': u'Který nerv inervuje sval {}',
            'ts2t': u'Který sval je inervován nervem {}',
        },
        'en': {
            't2ts': u'Which nerve inerves muscle {}',
            'ts2t': u'Which muscle is inerved by {}',
        },
    },
    'artery': {
        'cs': {
            't2ts': u'Která arterie zásobuje sval {}',
            'ts2t': u'Který sval je zásoben arterií {}',
        },
        'en': {
            't2ts': u'Which artery supplies muscle {}',
            'ts2t': u'Which muscle is supplied by {}',
        },
    },
    'action': {
        'cs': {
            't2ts': u'Jaká je funkce svalu {}',
            'ts2t': u'Který sval má funkci {}',
        },
        'en': {
            't2ts': u'What is function of {}',
            'ts2t': u'Which muscle has function {}',
        },
    },
    'antagonist': {
        'cs': {
            't2ts': u'Co je antagonistou svalu {}',
            'ts2t': u'Co je antagonistou svalu {}',
        },
        'en': {
            't2ts': u'What is antagonist of {}',
            'ts2t': u'What is antagonist of {}',
        },
    },
    'insertion': {
        'cs': {
            't2ts': u'Kde má úpon sval {}',
            'ts2t': u'Který sval má úpon na {}',
        },
        'en': {
            't2ts': u'Where is insertion of {}',
            'ts2t': u'Which muscle has insertion on {}',
        },
    },
    'origin': {
        'cs': {
            't2ts': u'Kde má počátek sval {}',
            'ts2t': u'Který sval má počátek na {}',
        },
        'en': {
            't2ts': u'Where is origin of {}',
            'ts2t': u'Which muscle has origin on {}',
        },
    },
    'bone': {
        'cs': {
            't2ts': u'Kteru kostí je ohraničen {}',
            'ts2t': u'Který kanálek je ohraničen {}',
        },
        'en': {
            't2ts': u'Which bone forms the margin of {}',
            'ts2t': u'Which foramen is bounded by {}',
        },
    },
    'cranialfossa': {
        'cs': {
            't2ts': u'V jaké lebeční jámě se nachází {}',
            'ts2t': u'Který kanálek se nachází v {}',
        },
        'en': {
            't2ts': u'In which cranial fossa lies {}',
            'ts2t': u'Which foramen lies in {}',
        },
    },
    'vessels': {
        'cs': {
            't2ts': u'Která céva prochází skrz {}',
            'ts2t': u'Kterým kanálkem prochází {}',
        },
        'en': {
            't2ts': u'Which vessel passes through {}',
            'ts2t': u'Through which foramen passes {}',
        },
    },
    'nerves': {
        'cs': {
            't2ts': u'Který nerv prochází skrz {}',
            'ts2t': u'Kterým kanálkem prochází {}',
        },
        'en': {
            't2ts': u'Which nerve passes through {}',
            'ts2t': u'Through which foramen passes {}',
        },
    },
}
CATEGORIES = {
    'nerve': {
        'cs': u'Inervace',
        'en': u'Nerve supply',
        'display-priority': 40,
    },
    'artery': {
        'cs': u'Cévní zásobení',
        'en': u'Arterial supply',
        'display-priority': 30,
    },
    'action': {
        'cs': u'Funkce svalu',
        'en': u'Actions',
        'display-priority': 50,
    },
    'antagonist': {
        'cs': u'Antagonisté',
        'en': u'Antagonists',
        'display-priority': 60,
    },
    'insertion': {
        'cs': u'Úpon svalu',
        'en': u'Insertions',
        'display-priority': 20,
    },
    'origin': {
        'cs': u'Začátek svalu',
        'en': u'Origins',
        'display-priority': 10,
    },
    'foramina': {
        'cs': u'Foramina',
        'en': u'Foramina',
        'display-priority': 70,
    },
    'bone': {
        'cs': u'Kosti',
        'en': u'Bones',
        'type': 'subrelation',
    },
    'cranialfossa': {
        'cs': u'Jámy lebeční',
        'en': u'Cranial fossa',
        'type': 'subrelation',
    },
    'vessels': {
        'cs': u'Cévy',
        'en': u'Vessels',
        'type': 'subrelation',
    },
    'nerves': {
        'cs': u'Nervy',
        'en': u'Nerves',
        'type': 'subrelation',
    },
}


def fill_relation_type_info(apps, schema_editor):
    RelationType = apps.get_model("anatomy_tagging", "RelationType")
    for rel_type in RelationType.objects.all():
        rel_type.identifier = rel_type.identifier.lower()
        if rel_type.identifier in CATEGORIES:
            rel_type.name_en = CATEGORIES[rel_type.identifier]['en']
            rel_type.name_cs = CATEGORIES[rel_type.identifier]['cs']
            rel_type.display_priority = CATEGORIES[rel_type.identifier].get('display-priority', 0)
        if rel_type.identifier in QUESTIONS:
            rel_type.question_en = simplejson.dumps(QUESTIONS[rel_type.identifier]['en'], sort_keys=True)
            rel_type.question_cs = simplejson.dumps(QUESTIONS[rel_type.identifier]['cs'], sort_keys=True)
        rel_type.save()


class Migration(migrations.Migration):

    dependencies = [
        ('anatomy_tagging', '0014_relation_info'),
    ]

    operations = [
        migrations.RunPython(fill_relation_type_info),
    ]
