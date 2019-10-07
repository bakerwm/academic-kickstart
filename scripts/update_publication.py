#!/usr/bin/env python3
"""Update publications

fileds:

featured:
title:
authors:
date:
doi:
publishDate:
publication_types:
publication:
publication_short:
abstract:
summary:
tags:
links:
url_pdf:
url_code
url_dataset:
url_poster:
url_project:
url_source:
url_video:

image:
  caption:
  focal_point: 
  preview_only:

projects:
 -

slides:


#####
Input: EndNote export style: "Show All Fields", type: "Text File (*.txt)".

Output: *.md file
"""

import os
import sys
import re
import datetime


def Endnote_text(f):
    """Parse the EndNote X9:
    output style: Show All Fields
    file type: Text File
    
    Begin-line: 
    Reference Type

    """
    # split records
    records = Endnote_text_split(f)

    # save to parser
    rec_list = []
    for r in Endnote_text_split(f):
        d = Endnote_record_parser(r)
        if len(d) < 1:
            continue  # skip empty blocks
        rec_list.append(d)

    return rec_list


def Endnote_text_split(f):
    """Parse the EndNote output in Text format
    split into records
    """
    records = []
    blocks = []
    with open(f, 'rt') as fi:
        for line in fi:
            line = line.strip()
            if line.startswith('#') or not line:
                continue # skip '#' and blank lines
            if line.startswith('Reference Type'):
                if len(blocks) > 0:
                    records.append(blocks)
                blocks = []
            blocks.append(line)

    # last block
    if len(blocks) > 0:
        records.append(blocks)

    return records


def Endnote_item2dict(x):
    """Save one line: key-value pair"""
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


def Endnote_record_parser(block):
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
            dn = Endnote_item2dict(items)
            d = {**d, **dn} # save to dict
            items = [line] # new record
        else:
            items.append(line)

    return d


def is_member(x):
    """Check the auther is member or not
    show in content/member
    """
    x = re.sub('\W', '', x) # remove non-alphabit
    x_md = os.path.join('content', 'member', x + '.md')

    return os.path.exists(x_md)


def is_name(x):
    """Check if x is a name
    Zhang, Chao
    Zhang, C
    Chin, M. H.
    """
    p = re.compile('^\w+,\s\w+(\.\s\w+)?\.?')
    return re.search(p, x)


def name_simplify(name, lower=True, rm_spaces=True):
    """Simplify the Author names, to lower case
    re.sub('[^A-Za-z0-9]', '', x)
    """
    name_out = re.sub('[^A-Za-z0-9 ]', '', name)
    if lower:
        name_out = name_out.lower()
    if rm_spaces:
        name_out = name_out.replace(' ', '')

    return name_out
    # x_out = ''
    # for i in x:
    #     if 'A' <= i <= 'z':
    #         x_out += 'i'.lower()
    # return x_out


def name_reverse(name):
    """Switch family name and given name"""
    fam, giv = name.split(',', 1)
    giv = giv.strip()
    return giv + ', ' + fam


def name_block_one(name):
    """Create one block for user
    [[authors]]
    name = "Thijs van de Laar"
    is_member = true
    link = "/thijs"

    """
    name_simple = name_simplify(name)
    member = is_member(name_simple)

    # show name
    name_display = name_reverse(name)
    name_display = name_display.replace(',', '')

    block = ['[[authors]]']
    block.append('    name = \"{}\"'.format(name_display))
    block.append('    is_member = {}'.format(str(member).lower()))
    block.append('    link = \"/{}\"'.format(name_simple))
    # block = '[[authors]]\n    name=\"{}\"\n    is_member = {}\n    link = \"\/{}\"'.format(
    #     x, str(member), name_simple
    #     )

    return '\n'.join(block)


def name_block_all(names):
    """Convert a list of names to blocks"""
    blocks = [name_block_one(i) for i in names]
    return '\n\n'.join(blocks)


def record2toml(d, save2md=True, force_update=0):
    """save record to toml format"""
    assert isinstance(d, dict)

    # title
    title = d.get('Title', 'title')
    # title = name_simplify(title, lower=False, rm_spaces=False)
    # title = title[:80]
    # title = re.sub('[\'\"]', '', title)
    title = re.sub('\"', '\\\"', title)

    # date
    date = d.get('EpubDate', '2019-01-01')
    date = date.replace('/', '-') # 2019/01/01 -> 2019-01-01

    # names
    notes = d.get('Notes', ['name, name'])
    names = [i for i in notes if is_name(i)]

    # publication_long
    pub_long = notes[-1] # last one

    url = d.get('URL', 'https://www.pubmed.com')
    if isinstance(url, list):
        url = url[0]

    # abstract
    abstract = d.get('Abstract', 'abstract')
    abstract = re.sub('\"', '\\\"', abstract)

    # toml format
    lines = ['+++']
    lines.append('selected = false')
    lines.append('title = \"{}\"'.format(title))
    lines.append('date = \"{}\"'.format(date))
    lines.append('image = ""')
    lines.append('image_preview = ""')
    lines.append('math = false')
    lines.append('publication = \"{}\"'.format(d.get('Journal', 'journal')))
    lines.append('publication_short = \"{}\"'.format(''))
    lines.append('url_code = "{}"'.format(url))
    lines.append('url_dataset = ""')
    lines.append('url_pdf = "{}"'.format(url))
    lines.append('url_project = ""')
    lines.append('url_slides = ""')
    lines.append('url_video = ""')
    lines.append('abstract = \"{}\"'.format(abstract))
    lines.append('abstract_short = \"\"')
    lines.append('\n')
    lines.append(name_block_all(names))
    lines.append('+++')

    if save2md:
        # create md file name
        year = d.get('Year', '2019')
        journal = d.get('Journal', 'Journal')
        title = d.get('Title', 'title')
        md_name = '-'.join([year, journal, title])
        md_name = re.sub('[\W]', '-', md_name)
        md_name = re.sub(' ', '-', md_name)
        md_name = md_name[:60] # fixed max width
        md_file = os.path.join('content', 'publication', md_name + '.md')
        
        if force_update or not os.path.exists(md_file):
            print('{:>8s} | {:5s} {:20s}'.format(
                'Add',
                year, 
                journal))
            with open(md_file, 'wt') as fo:
                fo.write('\n'.join(lines) + "\n")

    return '\n'.join(lines)


help_msg = """
Usage: python update_publication.py <force:0|1>

Convert EndNote output to markdown file
 
 input: static/publication/publication.txt
output: content/publication/*.md

If you want to add images, please refer to: 
image = "publication/2019-01-goldclip.png"
image_preview = "publication/2019-01-goldclip-view.png"

"""


if len(sys.argv) < 2:
    sys.exit(help_msg)


def main():
    # f = 'static/publication/abc.txt'
    endnote_txt = 'static/publication/publication.txt'
    force_update = eval(sys.argv[1])

    record_dicts = Endnote_text(endnote_txt)

    for d in record_dicts:
        if len(d) < 5:
            continue
        # save to file
        tmp = record2toml(d, save2md=True, force_update=force_update)
    

if __name__ == '__main__':
    main()

