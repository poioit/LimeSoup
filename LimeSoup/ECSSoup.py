import re

from LimeSoup.lime_soup import Soup, RuleIngredient
from LimeSoup.parser.paragraphs import extract_paragraphs_recursive
from LimeSoup.parser.parser_paper import ParserPaper
from bs4 import BeautifulSoup

__author__ = 'Tiago Botari, Haoyan Huo'
__maintainer__ = 'Haoyan Huo'
__email__ = 'haoyan.huo@lbl.gov'
__version__ = '0.3.0'


class ECSRemoveTrash(RuleIngredient):
    @staticmethod
    def _parse(html_str):
        parser = ParserPaper(html_str, parser_type='html.parser', debugging=False)

        # Tags to be removed from the HTML paper ECS
        list_remove = [
            {'name': 'div', 'class_': 'section-nav'},  # Navigation buttons
            {'name': 'div', 'class_': 'contributors'},  # Authors
            {'name': 'span', 'class_': 'disp-formula'},  # Formulas
            {'name': 'code'},  # Codes inside the HTML
            {'name': 'div', 'class_': 'fig pos-float odd'},  # Figures
            {'name': 'div', 'id': 'ref-list-1'},  # References
            {'name': 'span', 'class_': 'disp-formula'},  # Formulas
            {'name': 'span', 'class_': 'kwd-group-title'},  # Keyword labels
            {'name': 'div', 'class_': 'table-caption'},  # Caption Table
            {'name': 'div', 'class_': 'table-inline'},  # Table in line
            {'name': 'div', 'id': 'fn-group-1'},  # Footnotes
            {'name': 'div', 'id': 'license-1'},  # License
            {'name': 'ul', 'class': 'history-list'},  # some historical information of the paper
            {'name': 'ul', 'class': 'copyright-statement'},
            {'name': 'a', 'href': re.compile(r'#ref.*?')},
        ]
        parser.remove_tags(rules=list_remove)
        rules = [
            {'name': 'span', 'class': 'highwire-journal-article-marker-start'},
            {'name': 'ul', 'class': 'epreprint-list'}
        ]

        parser.strip_tags(rules)
        soup = BeautifulSoup(html_str, 'html.parser')
        metas = soup.find_all('meta')
        doi, journal = '', None
        for meta in metas:
            if meta.get('name') == 'DC.Identifier':
                doi = meta.get('content')
            if meta.get('name') == 'citation_journal_title':
                journal = meta.get('content')
        obj = {
            'Title': '',
            'Keywords': [],
            'Journal': journal,
            'DOI': doi
        }
        main_body = str(next(x for x in parser.soup.find_all('div', attrs={'class': 'fulltext-view'})))
        return main_body, obj
        

class ECSCollectTitleKeywords(RuleIngredient):

    @staticmethod
    def _parse(mainbody_text):
        mainbody_text, data = mainbody_text
        parser = ParserPaper(mainbody_text, parser_type='html.parser', debugging=False)
        # Collect information from the paper using ParserPaper
        keywords = parser.get_keywords(rules=[{'name': 'li', 'class_': 'kwd'}])
        title = parser.get_first_title(rules=[
            {'name': 'h1', 'recursive': True},
            {'name': 'h2', 'class_': 'subtitle', 'recursive': True}
        ])
        obj = {
            'Title': title,
            'Keywords': keywords,
            'Journal': data['Journal'],
            'DOI': data['DOI']
        }
        return obj, parser


class ECSCollectAbstract(RuleIngredient):
    @staticmethod
    def _parse(parser_obj):
        obj, parser = parser_obj

        abstract_section = next(
            x for x in parser.soup.find_all('div', attrs={'class': 'section abstract'})
        )
        obj['Sections'] = extract_paragraphs_recursive(abstract_section)
        abstract_section.extract()

        return obj, parser


class ECSCollect(RuleIngredient):
    @staticmethod
    def _parse(parser_obj):
        obj, parser = parser_obj

        exclude_sections = [
            re.compile(r'.*?acknowledge?ment.*?', re.IGNORECASE),
            re.compile(r'.*?reference.*?', re.IGNORECASE),
        ]
        obj['Sections'].extend(
            extract_paragraphs_recursive(parser.soup, exclude_section_rules=exclude_sections)
        )
        content = []
        stop = False
        index = 0
        for i, sect in enumerate(obj['Sections']):
            if stop:
                break
            if type(sect) == str:
                content.append(sect)
                if index == 0:
                    index = i
            if type(sect) == dict and content:
                stop = True
        if content:
            new = dict()
            new['content'] = content
            new['name'] = ""
            new['type'] = "section_h2"
            obj['Sections'] = obj['Sections'][:index] + [new] + obj['Sections'][(index+len(content)):]

        return obj


ECSSoup = Soup(parser_version=__version__)

# ECSSoup.add_ingredient(ECSCollectJournalDOI())
ECSSoup.add_ingredient(ECSRemoveTrash())
ECSSoup.add_ingredient(ECSCollectTitleKeywords())
ECSSoup.add_ingredient(ECSCollectAbstract())
ECSSoup.add_ingredient(ECSCollect())
