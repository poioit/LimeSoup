"""
ParserPaper is a class to parse HTML, XML papers from different publishers into
simples text. It can be used to feed a database.
This is the first version, I tried to separate things 
related to a specific publisher in the ParsePaper in order to help
to think how to reuse code in new publishers.
This class is not yet finished, just a security copy in GitHub.
"""

__author__ = "Zach Jensen"
__copyright__ = ""
__version__ = "1.1"
__maintainer__ = "Tiago Botari"
__email__ = "tiagobotari@gmail.com"
__date__ = "Apr 2019"

import re
import warnings

import bs4

import LimeSoup.parser.tools as tl


class ParserPaper:

    def __init__(self, raw_html, parser_type='lxml-xml', debugging=False):
        """
        :param raw_html:
        :param parser_type: can be 'html.parser', 'lxml', 'html5lib', 'lxml-xml'
        :param debugging: True or False
        """
        self.debugging = debugging
        # parsers 'html.parser', 'lxml', 'html5lib', 'lxml-xml'
        self.soup = bs4.BeautifulSoup('{:}'.format(raw_html), parser_type)
        self.parser_type = parser_type
        self.title = []
        self.keywords = []
        self.data_sections = []
        self.headings_sections = []
        self.number_paragraphs_sections = []
        if debugging:
            self.soup_orig = self.soup

    def deal_with_sections(self):
        """
        Deal with the sections, parse tags that contains <'section_h#'>
        Ex: <'section_h2'>
        :return:
        """
        self.data_sections = []
        parse_section = self.create_parser_sections(self.soup)
        # self.data_sections = parse_section.data
        # self.headings_sections = parse_section.heading
        # self.number_paragraphs_sections = parse_section.number_paragraphs
        # self.soup = parse_section.soup
        # del parse_section

    @staticmethod
    def compile(pattern):
        return re.compile(pattern)

    def create_section(self, name='no_name_section', type_section='no_type', content=[]):
       return {
            'type': type_section
            , 'name': name
            , 'content': content
        }


    def create_parser_sections(self, soup):
        search_str = re.compile('section_h[2-6]')
        section_tags = soup.find_all(search_str)
        for tag in section_tags:
            try:
                name = tag.find('h{}'.format(tag.name[-1])).text.strip().replace('\\n\'', '').replace(', \'', '')
                name = name.replace('\n', '')
                name = " ".join(name.split())
                name = name.replace('( ', '(').replace(' )', ')')
            except:
                name = ''
            content = []
            for p in tag.find_all('p'):
                text = self.format_text(p.text)
                if text[-1] != '.':
                    index = text.rfind('.')
                    text = text[:index+1]
                content.append(text)
            self.data_sections.append(self.create_section(
                name=name,
                type_section=tag.name,
                content= content
            ))
        # Nest data sections   
        for i in range(6, 1, -1):
            did_nest = False
            secname = "section_h{}".format(i)
            supersec_name = "section_h{}".format(i-1)
            supersupersec_name = "section_h{}".format(i-2)
            supersupersupersect_name = "section_h{}".format(i-3)
            curr_sec_set = []
            for j, sec in enumerate(reversed(self.data_sections)):
                if sec['type'] == secname:
                    curr_sec_set.insert(0, sec)
                elif sec['type'] == supersec_name and curr_sec_set:
                    for c in curr_sec_set:
                        curr = c['content']
                        for cu in curr:
                            if cu in sec['content']:
                                sec['content'].remove(cu)
                            elif isinstance(cu, dict):
                                curr2 = cu['content']
                                for cu2 in curr2:
                                    if cu2 in sec['content']:
                                        sec['content'].remove(cu2)
                    for c in curr_sec_set:
                        sec['content'].append(c)
                    curr_sec_set = []
                    did_nest = True

            if did_nest:
                self.data_sections = [s for s in self.data_sections if s['type'] != 'section_h{}'.format(i)]

    def format_text(self, text):
        text = re.sub('\n*\s+\n*',' ',text.strip()).strip()
        text = text.replace(' , , , , ', '').replace(' , , , ', '').replace(' , , ', '')
        text = text.replace('\\n', '').replace(', \'', '')
        text = text.replace('.\'', '.').replace(' , ', '')
        text = text.replace(' .', '.').replace(' [ ]', '')
        text = text.replace('\\uf8ff', '--').replace('\\u2005', '').replace('\\u2009', '').replace('\\uf8fe', '--')
        text = text.replace('\' \' \' \' ', '').replace('\' \' \' ', '')
        text = text.replace(' , , ', ' ').replace(' , ', ' ').replace(' )', ')')
        text = text.replace("<span class=\\'icomoon\\'>?</span>", "--")
        text = text.replace("<span class='icomoon'>?</span>", '--') 
        text = text.replace(' \' \'', '')
        text = text.replace("&amp;", "&")
        return text

    @staticmethod
    def create_soup(html_xlm, parser_type='html.parser'):
        # parser_types = ['html.parser', 'lxml', 'html5lib', 'lxml-xml']
        return bs4.BeautifulSoup(html_xlm, parser_type)

    def save_soup_to_file(self, filename='soup.html', prettify=True):
        """
        Save the soup to a file to be analysed. This can be used during the
        debugging process.
        :param filename: str that contain the name of the file
        :param prettify: boolean to add spaces on children tags
        :return: None - just save a file on disk
        """
        with open(filename, 'w', encoding='utf-8') as fd_div:
            if prettify:
                fd_div.write(self.soup.prettify())
                fd_div.write('\n')
            else:
                # for item in self.soup:
                #     #fd_div.write(item)
                fd_div.write(str(self.soup))
                fd_div.write('\n')

    def get_title(self, rules):
        self.title = self.get(rules)
    """ 
        for rule in rules:
            title = self.soup.find_all(**rule)
            for item_title in title:
                text = tl.convert_to_text(item_title.get_text())
                self.title.append(text)
                item_title.extract()
    """

    def get(self, rules):
        results = list()
        for rule in rules:
            finds = self.soup.find_all(**rule)
            for item in finds:
                text = tl.convert_to_text(item.get_text())
                results.append(text)
                item.extract()
        return results

    def get_keywords(self, rules):
        self.keywords = []
        for rule in rules:
            for keyword in self.soup.find_all(**rule):
                self.keywords.append(tl.convert_to_text(keyword.get_text()))
                keyword.extract()

    def remove_tags(self, rules):
        """
        Remove tags from bs4 soup object using a list of bs4 rules to find_all()
        :param rules: list() of dict() of rules of bs4 find_all()
        :return: None
        """
        for rule in rules:
            [s.extract() for s in self.soup.find_all(**rule)]

    def remove_tag(self, rules):
        """
        Remove the first found tag from bs4 soup object using
        a list of bs4 rules to find_all() Remove the first tag.
        :param rules: rules: list() of dict() of rules of bs4 find_all()
        :return: None
        """
        for rule in rules:
            [s.extract() for s in self.soup.find_all(limit=1, **rule)]

    @property
    def headings_orig(self):
        if not self.debugging:
            warnings.warn('Debugging mode has to be True when call the class')
            return None
        list_heading_soup = self.soup_orig.find_all(name=re.compile('^h[1-6]$'))
        list_heading = []
        for item in list_heading_soup:
            list_heading.append(item.get_text())
        return list_heading

    @property
    def headings(self):
        if not self.debugging:
            warnings.warn('Debugging mode has to be True when call the class')
            return None
        list_heading_soup = self.soup.find_all(name=re.compile('^h[1-6]$'))
        list_heading = []
        for item in list_heading_soup:
            list_heading.append(tl.convert_to_text(item.get_text()))
        return list_heading

    @property
    def paragraphs(self):
        if not self.debugging:
            warnings.warn('Debugging mode has to be True when call the class')
            return None
        list_paragraphs_soup = self.soup.find_all(name='p') # re.compile(
        list_paragraphs = []
        for item in list_paragraphs_soup:
            if len(tl.convert_to_text(item.get_text())) != 0:
                item.string = tl.convert_to_text(item.get_text())
                list_paragraphs.append(item.get_text())
        return list_paragraphs

    @property
    def span(self):
        import copy
        if not self.debugging:
            warnings.warn('Debugging mode has to be True when call the class')
            return None
        soup_one = copy.copy(self.soup)
        find_one1 = soup_one.find_all(name=re.compile('^h[1-6]$'))
        for e in find_one1:
            e.extract()
        find_one = soup_one.find_all(name=re.compile('span|p'), limit=1)
        list_paragraphs = []
        while len(find_one) != 0:
            text = tl.convert_to_text(find_one[0].get_text())
            if (find_one[0].name is not None) and (len(text) != 0):
                list_paragraphs.append(text)
            find_one[0].extract()
            find_one = soup_one.find_all(name=re.compile('span|p'), limit=1)
        return list_paragraphs

    @property
    def paragraphs_orig(self):
        if not self.debugging:
            warnings.warn('Debugging mode has to be True when call the class')
            return None
        list_paragraphs_soup = self.soup_orig.find_all(name=re.compile('p'))
        list_paragraphs = []
        for item in list_paragraphs_soup:
            list_paragraphs.append(item.get_text())
        return list_paragraphs

    def number_of_paragraphs_inside_parameters(self, parameters):
        if not self.debugging:
            warnings.warn('Debugging mode has to be True when call the class')
            return None
        soup_sec = self.soup_orig.find_all(parameters)
        number_of_paragraphs_soup_sec = 0
        for it in soup_sec:
            number_of_paragraphs_soup_sec += len(list(
                it.find_all('p', recursive=False)
            ))

    def number_of_paragraphs_children(self):
        if not self.debugging:
            warnings.warn('Debugging mode has to be True when call the class')
            return None
        number_of_paragraphs_children = len(list(list(
            self.soup_orig.children)[0].find_all('p', recursive=True)
                                                 )
                                            )


    def create_tag_from_selection(self, rule, name_new_tag, name_section='Abstract'):
        """
        Create a tag inside a bs4 soup object from a selection using a rule.
        :param rule: a dict() of rules of bs4 find_all()
        :param name_new_tag: new tag's name
        :param name_section: create a <h2> tag with the name_section content
        :return: None
        """
        inside_tags = self.soup.find_all(**rule)
        section = self.soup.new_tag('section_{}'.format(name_new_tag))
        heading = self.soup.new_tag('h2')
        heading.append(name_section)
        section.append(heading)
        for tag in inside_tags:
            tag.wrap(section)
            section.append(tag)

    def create_tag_to_paragraphs_inside_tag(self, rule, name_new_tag, name_section='Abstract'):
        inside_tags_inter = self.soup.find_all(**rule)
        if len(inside_tags_inter) == 0:
            # self.save_soup_to_file('selction_found_nothing.html')
            # input('Section not created, selection found nothing')
            return 'Section not created, number of paragraphs equal zero.'
        inside_tags = inside_tags_inter[0].find_all(re.compile('(p|ol)|span'), recursive=False)
        #inside_tags = inside_tags_inter[0].find_all('p', recursive=False)
        #inside_tags_ol = inside_tags_inter[0].find_all('ol', recursive=False)
        #inside_tags = inside_tags_p + inside_tags_ol
        if len(inside_tags) == 0:
            # self.save_soup_to_file('selction_found_nothing.html')
            # input('Section not created, number of paragraphs equal zero.')
            return 'Section not created, number of paragraphs equal zero.'
        section = self.soup.new_tag('section_{}'.format(name_new_tag))
        heading = self.soup.new_tag('h2')
        heading.append(name_section)
        section.append(heading)
        for tag in inside_tags:
            tag_next_sibling = tag
            while True:
                tag_next_sibling = tag_next_sibling.next_sibling
                if tag_next_sibling is None:
                    break
                if tag_next_sibling.name is None:
                    continue
                else:
                    break
            tag.wrap(section)
            section.append(tag)
            if tag_next_sibling is None: break
            if 'section_h' in tag_next_sibling.name:
                break

    def operation_tag_remove_space(self, rules):
        for rule in rules:
            tags = self.soup.find_all(**rule)
            for tag in tags:
                if tag is not None:
                    if tag.name is not None:
                        tag.string = tag.get_text().rstrip()

    def create_tag_sections(self, rule=None):
        """
        Create the standard tags (<section_#>) using a rule to bs4 find_all()
        :param rule:
        :return:
        """
        search_str = re.compile('h[2-6]')
        tags = self.soup.find_all(search_str)
        count = 0
        for each_tag in tags:
            if 'reference' in each_tag.text.lower():
                continue
            already_found = False
            if each_tag.get('class') is None:
                t = each_tag.parent
                if t.get('class') is None:
                    continue
                else:
                    if 'article' not in t.get('class')[0]:
                        continue
                    else:
                        already_found = True
            if already_found:
                pass
            elif 'article' not in each_tag.get('class')[0]:
                continue
            t = each_tag.parent
            section = self.soup.new_tag('section_'+each_tag.name)
            t.wrap(section)
            count += 1

    def rename_tag(self, rule, new_name='section_h4'):
        tags = self.soup.find_all(**rule)
        for tag in tags:
            tag.name = new_name

    def strip_tags(self, rules):
        """
        Replace some tag with the children tag.
        :param rules: list of rules for bs4 find_all()
        :return: None
        """
        tags = list()
        for rule in rules:
            for tag in self.soup.find_all(**rule):
                tag.replace_with_children()
                tags.append(tag.name)
        return tags

    def change_name_tag_sections(self):
        tags = self.soup.find_all(re.compile('^h[2-6]'))
        for each_tag in tags:
            each_tag.parent.name = 'section_{}'.format(each_tag.name)

    @property
    def raw_html(self):
        return self.soup.prettify()
