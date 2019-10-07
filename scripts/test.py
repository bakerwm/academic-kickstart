#!/usr/bin/env python3

"""Parse EndNote full records, All fields
save output
"""

import os, sys, re



def get_blocks(lines, sep='Reference Type'):
    """Split lines into blocks by `sep`
    each one means one block/record
    """
    data = []
    for line in lines:
        if line.startswith('#') or not line:
                continue # skip '#' and blank lines
        if line.startswith(sep):
            if data:
                yield data
                data = []
        data.append(line)

    if data:
        yield data


def endnote_all(x, bib=None):
    """Parse the export from EndNote X9
    output style: Show All Fields
    file type: Text File
    
    Begin-line: 
    Reference Type
    """
    with open(x, 'rt') as f:
        for i, record in enumerate(get_blocks(f, 'Reference Type'), start=1):
            # record
            Endnote(record, bib).to_md_file()
            Endnote(record, bib).to_bib_file()


class Endnote(object):
    """Processing Endnote records
    input1: All fields
    input2: bib
    export markdown 
    """

    def __init__(self, block, bib, overwrite=False):
        """Parse records for one record
        All fields 
        """
        self.block = block
        self.bib = bib
        self.overwrite = overwrite

        # dict for one record
        d = self.block2dict()

        # workding dir
        src_dir = os.path.dirname(os.path.realpath(__file__))
        base_dir = os.path.dirname(src_dir)

        # target files
        year = str(d['year'])
        journal = d['journal']
        journal = journal.replace(' ', '-')
        author_1st = d['full_names'][0] # the first one
        author_1st_fm = author_1st.split(',')[0] # the family name
        target_dirname = '-'.join([year, journal, author_1st_fm])
        target_dir = os.path.join(base_dir, 'content', 'publication',
            target_dirname)
        target_md = os.path.join(target_dir, 'index.md')
        target_bib = os.path.join(target_dir, 'cite.bib')

        self.d = d
        self.base_dir = base_dir
        self.target_dir = target_dir
        self.target_md = target_md
        self.target_bib = target_bib


    def item2dict(self, x):
        """Save one line: key-value pair
        return dict
        """
        assert isinstance(x, list)

        d = {} # init dict

        if len(x) > 0:
            # the key-value line
            lineA = x.pop(0) # the first line
            key, value = lineA.strip().split(':', 1)
            key = re.sub('[^\w]', '', key)
            value = value.strip() # remove blanks

            if len(x) > 0:
                value = [value]
                value.extend(x)

            # save as dict
            d[key] = value

        return d


    def endnote_parser(self, block):
        """Parse the EndNote output in Text format
        Title:
        Journal:
        Volumn:
        Issue:
        Pages:
        Epub Date:
        DOI:
        Accesion Number:
        Author:
        Notes:
        URL:

        """
        assert isinstance(block, list)
        
        # id: value(s)
        p = re.compile('^\'?[A-Z]\'?\\w+(\s)?\\w+:')

        # init dict
        d = {}

        # split into records
        units = []
        items = []
        for line in block:
            if re.search(p, line):
                # the id line
                # units.append(items) # last record
                dn = self.item2dict(items)
                d = {**d, **dn} # save to dict
                items = [line] # new record
            else:
                items.append(line)

        return d


    def block2dict(self):
        """Convert block to dict
        refine values:
        """
        d = self.endnote_parser(self.block)

        # global data
        dx = {}

        dx['rec_num'] = d.get('Record Number', 1)
        dx['pmc'] = d.get('PMCID', 'PMC0000001')
        dx['pub_type'] = d.get('Reference Type', 'Journal article')
        title = d.get('Title', 'title')
        dx['title'] = re.sub('\"', '\\\"', title) # remove '\"'
        
        dx['doi'] = d.get('DOI', '')

        dx['year'] = d.get('Year', '2019')
        dx['journal'] = d.get('Journal', 'Journal')
        date = d.get('EpubDate', '2019-01-01')
        dx['date'] = date.replace('/', '-') # format: 2016-01-02

        notes = d.get('Notes', ['name, name'])
        dx['full_names'] = [i for i in notes if self.is_name(i)] # full names
        dx['pub_name'] = notes[-1]
        dx['pub_short'] = d.get('Publication_short', "")
        url = d.get('URL', 'https://www.pubmed.com')
        if isinstance(url, list):
            url = url[0]
        dx['url'] = url

        abstract = d.get('Abstract', 'abstract')
        dx['abstract'] = re.sub('\"', '\\\"', abstract)

        # wrap authors into 'list'
        full_name_list = ['"' + i.strip() + '"' for i in dx['full_names']]
        full_name_list = [i.replace(',', '') for i in full_name_list]
        dx['full_name_line'] = '[' + ', '.join(full_name_list) + ']'

        # name list
        name_str = d.get('Author', 'author')
        name_str = name_str.replace(' and ', ', ') # remove and
        name_list = name_str.split('., ')
        name_list = [i.replace(',', '') for i in name_list]
        dx['name_line'] = '[' + ', '.join(name_list) + ']'

        # extra urls
        dx['url_pdf'] = d.get('url_pdf', '')
        dx['url_code'] = d.get('url_code', '')
        dx['url_dataset'] = d.get('url_dataset', '')
        dx['url_poster'] = d.get('url_poster', '')
        dx['url_project'] = d.get('url_project', '')
        dx['url_slides'] = d.get('url_slides', '')
        dx['url_source'] = d.get('url_source', '')
        dx['url_video'] = d.get('url_video', '')
                
        return dx


    def is_name(self, x):
        """Check if x is a name
        Zhang, Chao
        Zhang, C
        Chin, M. H.
        """
        p = re.compile('^\w+,\s\w+(\.\s\w+)?\.?')
        return re.search(p, x)


    def name_simplify(self, name, lower=True, rm_spaces=True):
        """Simplify the Author names, to lower case
        re.sub('[^A-Za-z0-9]', '', x)
        """
        name_out = re.sub('[^A-Za-z0-9 ]', '', name)
        if lower:
            name_out = name_out.lower()
        if rm_spaces:
            name_out = name_out.replace(' ', '')

        return name_out


    def name_reverse(self, name):
        """Switch family name and given name"""
        fam, giv = name.split(',', 1)
        giv = giv.strip()
        return giv + ', ' + fam


    def get_name_list(self):
        """Return the list of authors
        """
        pass


    def get_pub_num(self):
        """For Academic theme
        0: Uncategorized
        1: Conference paper
        2: Journal article
        3: Preprint 
        4: Report 
        5: Book
        6: Book section 
        7: Thesis 
        8: Patent
        """
        d = self.d # refined

        # support one type
        dpub = {
            'uncategorized': 0,
            'conference paper': 1,
            'journal article': 2,
            'preprint': 3,
            'report': 4,
            'book': 5,
            'book section': 6,
            'thesis': 7,
            'patent': 8,
        }

        # return 
        pub_type = d['pub_type']
        pub_num = dpub.get(pub_type.lower(), 2)

        return pub_num


    def get_md_text(self, yaml=True):
        """Generate markdown file for one publication
        records save as dict

        """
        d = self.d # refined 

        # YAML format
        lines = ['---']
        lines.append('featured: false') # !!!! manual fix
        lines.append('title: "{}"'.format(d['title']))
        lines.append('authors: {}'.format(d['name_line']))
        lines.append('date: {}'.format(d['date']))
        lines.append('doi: "{}"'.format(d['doi']))
        lines.append('\n')

        lines.append('# Publication type')
        lines.append('# Legend: 0 = Uncategorized')
        lines.append('#   1 = Conference paper')
        lines.append('#   2 = Journal article')
        lines.append('#   3 = Preprint / Working Paper')
        lines.append('#   4 = Report')
        lines.append('#   5 = Book')
        lines.append('#   6 = Book section')
        lines.append('#   7 = Thesis')
        lines.append('#   8 = Patent')
        lines.append('publication_types: ["{}"]'.format(self.get_pub_num()))
        lines.append('publication: "{}"'.format(d['journal']))
        lines.append('publication_short: "{}"'.format(d['pub_short']))
        lines.append('\n')

        lines.append('# Manual curate this section')
        lines.append('summary: "{}"'.format('')) # !!!! manual
        lines.append('projects: "{}"'.format('')) # !!!! manual
        lines.append('\n')

        lines.append('links:')
        lines.append('url_pdf: "{}"'.format(d['url_pdf']))
        lines.append('url_code: "{}"'.format(d['url_code']))
        lines.append('url_dataset: "{}"'.format(d['url_dataset']))
        lines.append('url_poster: "{}"'.format(d['url_poster']))
        lines.append('url_project: "{}"'.format(d['url_project']))
        lines.append('url_slides: "{}"'.format(d['url_slides']))
        lines.append('url_source: "{}"'.format(d['url_source']))
        lines.append('url_video: "{}"'.format(d['url_video']))

        lines.append('abstract: "{}"'.format(d['abstract']))
        lines.append('\n')
        lines.append('---')

        return lines


    def bib_reader(self):
        """Create cite.bib file
        retrieve by: Record Number
        at the first line of bib file
        @article{RN001,
        """
        # save as dict
        db = {}
        try:
            with open(self.bib) as f:
                for i, group in enumerate(get_blocks(f, '@article'), start=1):
                    # parse doi
                    for line in group:
                        if line.strip().startswith('DOI'):
                            doi = line.split('=')[1]
                            doi = doi.strip().strip('{').strip(',').strip('}')
                            db[doi] = group
                            print(doi)
        except:
            print('bib file not found: {}'.format(self.bib))

        return db


    def to_md_file(self):
        """Save markdown to file
        in directory:
        content/publication/<dir>/index.md
        featured.jpg (png)
        cite.bib 

        track records by : Record Number


        # folder name: 2018-Cell-Res-Chen
        # if duplicated, add "-PMC6170407" suffix

        """
        # check existence
        if not os.path.exists(self.target_dir):
            os.makedirs(self.target_dir)

        # save md
        md_text = self.get_md_text()
        if not os.path.exists(self.target_md) or self.overwrite:
            print('write publication')
            with open(self.target_md, 'wt') as fo:
                fo.write('\n'.join(md_text) + '\n')
        else:
            print('skip file')


    def to_bib_file(self):
        """Save bibtext record to cite.bib file
        if full.bib exists
        """
        d = self.d # all fields
        doi = d.get('doi', '1')
        print('doi-from: {}'.format(doi))

        # bib dict
        db = self.bib_reader()

        # record
        bib_text = db.get(doi, [])
        # print(list(db.keys()))

        if not os.path.exists(self.target_bib) or self.overwrite:
            print('write bib')
            with open(self.target_bib, 'wt') as fo:
                fo.write(''.join(bib_text))


def main():
    if len(sys.argv) < 3:
        sys.exit('python pub.py <pub.txt> <pub.bib>')
    txt = sys.argv[1]
    bib = sys.argv[2]
    endnote_all(txt, bib)







# def main():
#     f = sys.argv[1]
#     with open(f, 'rt') as f:
#         for i, record in enumerate(get_blocks(f, 'Reference Type'), start=1):
#             print('Group {}'.format(i))
#             print(record[1])



















if __name__ == '__main__':
    main()






# from StackOverflow
# by: Bakuriu
# https://stackoverflow.com/a/38663342/2530783

# from itertools import groupby

# def make_grouper(sep='Reference Type'):
#     counter = 0
#     def key(line):
#         nonlocal counter
#         if line.startswith(sep):
#             counter += 1
#         return counter
#     return key


# def main():
#     f = sys.argv[1]
#     with open(f, 'rt') as fi:
#         for k, group in groupby(fi, key=make_grouper()):
#             print('Group {}'.format(k))
#             # a = ''.join(group)
#             # print(a)
#             a = list(group)
#             print(a[1])

