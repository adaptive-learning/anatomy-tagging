# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from anatomy_tagging.models import Term
from optparse import make_option
import wikipedia
from bs4 import BeautifulSoup


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
        page = wikipedia.page('List_of_muscles_of_the_human_body')
        soup = BeautifulSoup(page.html())
        # page = ''.join(open('List_of_muscles.html', 'r').readlines())
        # soup = BeautifulSoup(page)
        tables = soup.findAll("table", {"class": "wikitable"})
        relations_db = []
        for table in tables:
            relations = self.process_table(table)
            relations_db = relations_db + relations
        return relations_db

    def get_term_name(self, cell):
        title = None
        text = " ".join(cell.findAll(text=True))
        link = cell.find('a')
        if link is not None and 'title' in link:
            title = link['title']
        if title is not None:
            term = title
        else:
            term = text
        return term

    def get_term(self, name):
        term = None
        try:
            term = Term.objects.get(name_en__iexact=name.strip())
            # print term
            # print "OK",
        except Term.DoesNotExist:
            # print 'not found', c
            # print "  ",
            pass
        except Term.MultipleObjectsReturned:
            # print 'multiple found', c
            # print "  ",
            pass
        return term

    def process_table(self, table):
        relations = []
        header = table.find("tr").findAll("th")
        header = [h.find(text=True).strip() for h in header]
        for row in table.findAll("tr")[1:]:
            cells = row.findAll("td")
            cells = [self.get_term_name(c) for c in cells]
            if len(cells) == len(header):
                relations_dict = {}
                main_term = self.get_term(cells[0])
                for h, c in zip(header[1:], cells[1:]):
                    term = self.get_term(c)
                    relations_dict[h] = c
                    relation = {
                        'type': h,
                        'term1': main_term,
                        'term2': term,
                        'text1': cells[0],
                        'text2': c,
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
