# -*- coding: utf-8 -*-
from anatomy_tagging.models import Term
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand
from optparse import make_option
import copy
import json
import os
import wikipedia


WIKI_PAGE_MUSCLES = 'List_of_muscles_of_the_human_body'


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
        make_option(
            '--page',
            type=str,
            dest='page',
            default=WIKI_PAGE_MUSCLES,
            help='Name of the WIKI page'
        )
    )

    def handle(self, *args, **options):
        self.get_relations(options['page'])

    def get_relations(self, page_name):
        self.init_terms()
        json_name = os.path.join(settings.MEDIA_DIR, page_name + '.json')
        if os.path.isfile(json_name):
            with open(json_name, 'r') as f:
                raw_relations = json.load(f)
                return raw_relations

        page = wikipedia.page(page_name)
        soup = BeautifulSoup(page.html())
        tables = soup.findAll("table", {"class": "wikitable"})
        raw_relations = []
        for table in tables:
            relations = self.process_table(table)
            raw_relations = raw_relations + relations

        with open(json_name, 'w') as f:
            json.dump(raw_relations, f)

        return copy.deepcopy(raw_relations)

    def init_terms(self):
        if hasattr(self, 'terms'):
            return
        terms = Term.objects.all()
        self.terms = {}
        for t in terms:
            for name in t.name_la.split(';'):
                self.terms[name.lower()] = t
            for name in t.name_en.split(';'):
                self.terms[name.lower()] = t

    def get_term_name(self, cell):
        return " ".join([c.strip() for c in cell.findAll(text=True)]).strip()

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
        return None if term is None else term.to_serializable()

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
