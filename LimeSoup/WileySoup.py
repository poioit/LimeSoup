import re 

from LimeSoup.lime_soup import Soup, RuleIngredient
from LimeSoup.parser.parser_paper_wiley import ParserPaper
from bs4 import BeautifulSoup

__author__ = 'Zach Jensen'
__maintainer__ = ''
__email__ = 'zjensen@mit.edu'



class WileyRemoveTagsSmallSub(RuleIngredient):

    @staticmethod
    def _parse(html_str):
        """
        Deal with spaces in the sub, small tag and then remove it.
        """
        parser = ParserPaper(html_str, parser_type='html.parser', debugging=True)
        rules = [{'name':'i'},
                 {'name':'sub'},
                 {'name':'sup'},
                 {'name':'b'}, 
                 {'name':'em'}]

        parser.operation_tag_remove_space(rules)
        # Remove some specific all span that are inside of a paragraph 'p'
        parser.strip_tags(rules)
        tags = parser.soup.find_all(**{'name': 'p'})
        for tag in tags:
            tags_inside_paragraph = tag.find_all(**{'name': 'span'})
            for tag_inside_paragraph in tags_inside_paragraph:
                tag_inside_paragraph.replace_with_children()

        # Remove some specific span that are inside of a span and p
        parser.strip_tags(rules)
        tags = parser.soup.find_all(**{'name': re.compile('span|p')})
        for tag in tags:
            for rule in rules:
                tags_inside_paragraph = tag.find_all(**rule)
                for tag_inside_paragraph in tags_inside_paragraph:
                    tag_inside_paragraph.replace_with_children()
        # Recreating the ParserPaper bug in beautifulsoup
        html_str = str(parser.soup)
        parser = ParserPaper(html_str, parser_type='html.parser', debugging=False)
        return parser.raw_html

class WileyRemoveTrash(RuleIngredient):
    # TODO: error in two papers: 10.1039/B802997K - 10.1039/B717130G, some heading inside a span tag:
    @staticmethod
    def _parse(html_str):
        # Tags to be removed from the HTML paper ECS
        list_remove = [
            {'name': 'div', 'class': 'loa-wrappers loa_authors hidden-xs'},
            {'name':'div', 'class':'article-header__authors-container'},  # Authors X
            {'name': 'div', 'id': 'art-admin'},  # Data rec./accept. 
            {'name': 'div', 'class': 'article-section__inline-figure'},
            {'name': 'section', 'class':'article-section article-section--inline-figure'},
            {'name':'figure'},  # Figures X
            {'name': 'div', 'id': 'crossmark-content'},  # Another Logo
            {'name': 'code'},  # Codes inside the HTML
            {'name': 'div', 'class': 'article-table-content'},  # Remove table X
            {'name': 'header', 'class': 'page-header'}, # Navigation links X 
            {'name': 'div', 'class':'page-footer'},
            {'name':'div', 'class':'js-module notification'},
            {'name':'img'}, 
            {'name':'aside'},
            {'name':'div', 'class':'issue-header js-module'}, 
            {'name':'span', 'class':'article-header__category article-category'},
            {'name':'article-header__meta-info-container'},
            {'name':'a', 'class':'figZoom'},
            {'name':'ul', 'class':'meta-navigation u-list-plain'},
            {'name':'div', 'id':'js-article-nav'},
            {'name':'section', 'id':'pdf-section'},
            {'name':'section', 'class':'article-footer__section article-section'}, 
            {'name':'div', 'class':'l-article-support'}, 
            {'name':'footer', 'role':'contentinfo'}, 
            {'name':'div', 'data-module':'infoplane'},
            {'name':'header', 'role':'banner'},
            {'name':'header', 'class':'journal-header'},
            {'name':'div', 'class':'article-header__meta-info-container'},
            {'name':'div', 'class':'article-header__references-container'},
            {'name':'section', 'id':'footer-article-info'},
            {'name':'section', 'id':'related-content'},
            {'name':'section', 'id':'footer-citing'},
            {'name':'section', 'id':'footer-support-info'},
            {'name':'ul', 'class':'article-section__references-list-additional u-horizontal-list'}, # Remove Footnote X
        ]
        parser = ParserPaper(html_str, parser_type='html.parser', debugging=False)
        parser.remove_tags(rules=list_remove)
        parser.remove_tag(
            rules=[{'name': 'p', 'class': 'bold italic', 'string': parser.compile('First published on')}]
        )
        return parser.raw_html

class WileyCreateTags(RuleIngredient):

    @staticmethod
    def _parse(html_str):
        # This create a standard of sections tag name
        parser = ParserPaper(html_str, parser_type='html.parser', debugging=False)
        parser.create_tag_sections()
        return parser.raw_html

class WileyCreateTagAbstract(RuleIngredient):

    @staticmethod
    def _parse(html_str):
        # Create tag from selection function in ParserPaper
        parser = ParserPaper(html_str, parser_type='html.parser', debugging=False)
        parser.create_tag_from_selection(
            rule={'name': 'p', 'class': 'abstract'},
            name_new_tag='h2'
        )
        # Guess introductions
        #parser.create_tag_to_paragraphs_inside_tag(
        #  #   rule={'name': 'section_h1'},
        #     name_new_tag='h2',
        #     name_section='Introduction(guess)'
        # )
        return parser.raw_html

class WileyReplaceDivTag(RuleIngredient):

    @staticmethod
    def _parse(html_str):
        parser = ParserPaper(html_str, parser_type='html.parser', debugging=False)
        rules = [{'name': 'div'}]
        parser.strip_tags(rules)
        rules = [{'name': 'span', 'id': parser.compile('^sect[0-9]+$')}]  # some span are heading
        _ = parser.strip_tags(rules)
        return parser.raw_html


class WileyCollect(RuleIngredient):

    @staticmethod
    def _parse(html_str):
        soup = BeautifulSoup(html_str, 'html.parser')
        parser = ParserPaper(html_str, parser_type='html.parser', debugging=False)
        # Collect information from the paper using ParserPaper
        keywords = soup.find_all(attrs={'name':'citation_keywords'})
        keys = []
        for key in keywords:
            keys.append(key.get('content'))
        journal_name = soup.find(attrs={'name':'citation_journal_title'})
        journal_name = journal_name.get('content')
        doi = soup.find(attrs={'name':'citation_doi'})
        doi = doi.get('content')
        title = soup.find(attrs={'name':'citation_title'})
        title = title.get('content')
        # Create tag from selection function in ParserPaper
        data = list()
        """
        Can deal with multiple Titles in the same paper
        """
        parser.deal_with_sections()
        data = parser.data_sections
        obj = {
            'DOI': doi,
            'Title': title,
            'Keywords': keys,
            'Journal': journal_name,
            'Sections': data
        }
        return {'obj': obj, 'html_txt': parser.raw_html}

WileySoup = Soup()
WileySoup.add_ingredient(WileyRemoveTagsSmallSub())
WileySoup.add_ingredient(WileyRemoveTrash())
WileySoup.add_ingredient(WileyCreateTags())
WileySoup.add_ingredient(WileyCreateTagAbstract())
WileySoup.add_ingredient(WileyReplaceDivTag())
WileySoup.add_ingredient(WileyCollect())