# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from anatomy_tagging.models import Term
from optparse import make_option
import wikipedia
from bs4 import BeautifulSoup
import json
import os
from django.conf import settings
import copy


class Command(BaseCommand):
    help = u"""Scrape info about terms from wikipedia"""
    option_list = BaseCommand.option_list + (
        make_option(
            '--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete images and paths at first',
        ),
    )
    IMAGES_DIR = '/svg/'

    def handle(self, *args, **options):
        relations_db = self.get_relations()
        print relations_db
        print len(relations_db)

    def get_relations(self):
        name = 'List_of_muscles_of_the_human_body'
        json_name = os.path.join(settings.MEDIA_DIR, name + '.json')
        if os.path.isfile(json_name):
            with open(json_name, 'r') as f:
                relations_db = json.load(f)
                return relations_db

        page = wikipedia.page(name)
        soup = BeautifulSoup(page.html())
        # page = ''.join(open('List_of_muscles.html', 'r').readlines())
        # soup = BeautifulSoup(page)
        tables = soup.findAll("table", {"class": "wikitable"})
        relations_db = []
        self.load_terms()
        for table in tables:
            relations = self.process_table(table)
            relations_db = relations_db + relations

        with open(json_name, 'w') as f:
            raw_relations = copy.deepcopy(relations_db)
            for r in raw_relations:
                if r['term1'] is not None:
                    r['term1'] = r['term1'].to_serializable()
                if r['term2'] is not None:
                    r['term2'] = r['term2'].to_serializable()
            json.dump(raw_relations, f)
        return relations_db

    def load_terms(self):
        terms = Term.objects.all()
        self.terms = {}
        for t in terms:
            for name in t.name_la.split(';'):
                self.terms[name.lower()] = t
            for name in t.name_en.split(';'):
                self.terms[name.lower()] = t

    def get_term_name(self, cell):
        text = " ".join(cell.findAll(text=True))
        return text

    def get_term_from_cell(self, cell):
        term = None
        links = cell.findAll('a')
        if len(links) == 1:
            title = links[0].get('title', None)
            term = self.get_term_from_name(title)
        if term is not None:
            return term

        name = self.get_term_name(cell)
        term = self.get_term_from_name(name)
        return term

    def get_term_from_name(self, name):
        term = None
        if name is None:
            return None
        name = name.lower().strip()
        if name != "":
            term = self.terms.get(name, None)
            if term is None:
                term = self.terms.get(name.replace(" muscle", ""), None)
        return term

    def process_table(self, table):
        relations = []
        header = table.find("tr").findAll("th")
        header = [h.find(text=True).strip() for h in header]
        for row in table.findAll("tr")[1:]:
            cells = row.findAll("td")
            if len(cells) == len(header):
                relations_dict = {}
                main_term = self.get_term_from_cell(cells[0])
                for h, c in zip(header[1:], cells[1:]):
                    term = self.get_term_from_cell(c)
                    relations_dict[h] = c
                    relation = {
                        'type': h,
                        'term1': main_term,
                        'term2': term,
                        'text1': self.get_term_name(cells[0]),
                        'text2': self.get_term_name(c),
                    }
                    relations.append(relation)
        return relations

    def scrape_terms(self):
        terms = Term.objects.exclude(
            code__in=['no-practice', 'too-small']).filter(
            name_en__in=['Biceps brachii'])[:1]
        for term in terms:
            print "Fetching", term.name_en
            if term.name_en != "":
                try:
                    page = wikipedia.page(term.name_en)
                    print page.content
                except wikipedia.exceptions.PageError:
                    print 'Page missing', term.name_en
