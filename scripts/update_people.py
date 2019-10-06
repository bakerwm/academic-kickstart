#!/usr/bin/env python3

"""Create/update people in directory `content/authors`:
name/
file: _index.md
file: avatar.jpg

# read Jason files from directory:
`static/people/`
  - shortname.xlsx
  - shortname.jpg (png)


1. Shortname
2. Name:
3. identity:
4. organization
5. phone:
6. email:
7. github
8. twitter
9. website
10. B.S.
11. M.S.
12. Ph.D. 
13. Postdoc.
14. status
15. interests
16. one-sentence
17. brief
18. content
19. order


"""


import os
import sys
import re
import shutil
import random
import datetime
import textwrap
import pandas as pd # require xlrd


def avatar_picker(x, base_dir):
    """Pick the file name of specific user
    default: static/people/
    backup: static/img/people/
    """
    path_default = os.path.join(base_dir, 'static', 'people')
    path_backup = os.path.join(base_dir, 'static', 'img', 'people')

    # specific names
    x_names = [x + '.jpg', x + '.png']
    x_files = [os.path.join(path_default, i) for i in x_names]
    x_files = [i for i in x_files if os.path.exists(i)]

    # pick a random pick in backup
    bk_files = [i for i in os.listdir(path_backup) if i.endswith('.jpg') or i.endswith('.png')]
    rnd_num = random.choice(range(len(bk_files) - 1))
    bk_file = os.path.join(path_backup, bk_files[rnd_num])

    # output
    if len(x_files) > 0:
        img_out = x_files[0] # the first one
    else:
        img_out = bk_file

    return img_out


def excel_reader(x, lang='en'):
    """Read Excel file
    export as dictionary
    Check if the file exists, 
    19 rows x 3 columns
    """
    df = pd.read_excel(x, index_col=0, usecols=[0,1,2,3])
    df.columns = ['group', 'en', 'cn']

    if not df.shape == (19, 3):
        raise Exception('Excel file should be 19 rows x 3 columns, check: ' + x)

    return df
    

def get_group(x, lang='en'):
    """
    "Principal Investigator",
    "Grad Students",
    "Postdoc",
    "Researchers",
    "Visitors",
    "Alumni"

    # check row-3:
      Principal Investigator
          - PI
      Grad Students:
          - 2017, Ph.D.
          - 2017, M.S.
      Researchers
        - 2017, Assisstant Prof
          - 2018, Postdoc
      Visitors
          - 2018, Visitor
          - 2019, B.S.
      Alumni
          - yes (row-14)

    # input the dict
    row-3: identity
    row-14: leave: yes|no
    """

    current = x.loc[3][lang]
    status = x.loc[14][lang]

    if status.lower() == 'yes':
        group = 'Alumni'
    elif re.search('(Principal Investigator)|PI', current):
        group = 'Principal Investigator'
    elif re.search('Ph.D.|M.S.', current):
        group = 'Grad Students'
    elif re.search('Postdoc|Assistant', current):
        group = 'Researchers'
    elif re.search('Visitor', current):
        group = 'Visitors'
    elif re.search('Manager', current):
        group = 'Researchers'
    else:
        group = 'Visitors'

    return group


def get_org(x, lang='en'):
    """Get the organization of people

    status + Org name

    2018, Ph.D. IBP

    row-3: 2018, Ph.D.
    ror-4: IBP
    
    """
    org = x.loc[4][lang]
    return org


def get_bio(x, lang='en'):
    """Get the one-sentence introduction"""
    bio = x.loc[16][lang]
    return bio


def get_inte(x, lang='en'):
    """Get the intersets
    separated by comma
    return:
        list
    """
    inte = x.loc[15][lang]
    inte_list = [i.strip() for i in inte.split(',')]
    return inte_list


def edu_reader(x):
    """Parse the education
    2017, Ph.D. in biology, Peking Uinversity, Tang
    year, course, univ, prof
    """
    seps = re.findall(',', x)
    year = course = univ = prof = ""
    if len(seps) > 2:
        year, course, univ, prof = x.split(',', 3)
    elif len(seps) == 2:
        year, course, univ = x.split(',', 2)
    else:
        course = x
    return [year, course, univ, prof]


def edu_parser(x, type=1, lang='en', yaml=False):
    """Generate the education values for user

    course:
    institution:
    year:


    # groups
    1:postdoc
    2:phd
    3:ms
    4:bs

    """
    dt = {
        1: 13, # postdoc
        2: 12, # phd
        3: 11, # ms
        4: 10, # bs
    }

    line = x.loc[dt[type]][lang]
    if not isinstance(line, str):
        line = ''

    if line:
        year, course, univ, prof = edu_reader(line)
        # YAML format
        lines = []
        if yaml:
            lines.append('  - course: {}, {}'.format(course, prof))
            lines.append('    institution: {}'.format(univ))
            lines.append('    year: {}'.format(year))
            out = '\n'.join(lines)
        else:
            out = [year, course, univ, prof]
    else:
        out = ""

    return out


def social_parser(x, type=1, lang='en', yaml=False):
    """Parse the social
    email, github, twitter

    - icon: 
      icon_pack:
      link:

    # group
    1=email
    2=github
    3=twitter

    # input
    dict
    """
    if type == 1:
        val = x.loc[6][lang] # email
        line = val.strip() if isinstance(val, str) else ''
        icon = 'envelope'
        icon_pack = 'fas'
        link = 'mailto:{}'.format(line)
    elif type == 2:
        val = x.loc[7][lang] # github
        line = val.strip() if isinstance(val, str) else ''
        icon = 'github'
        icon_pack = 'fab'
        link = 'https://github.com/{}'.format(line)
    elif type == 3:
        val = x.loc[8][lang] # twitter
        line = val.strip() if isinstance(val, str) else ''
        icon = 'twitter'
        icon_pack = 'fab'
        link = 'https://twitter.com/{}'.format(line)
    else:
        line = icon = icon_pack = link = ""

    # YAML ourput
    if line:
        if yaml:
            lines = []
            lines.append('- icon: {}'.format(icon))
            lines.append('  icon_pack: {}'.format(icon_pack))
            lines.append('  link: {}'.format(link))
            out = '\n'.join(lines)
        else:
            out = [val, icon, icon_pack, link]
    else:
        out = ""

    return out


def people_md(x, lang='en'):
    """Generate markdown file for one people
    header in YAML format
    """
    d = excel_reader(x, lang)

    # create YAML
    lines = ['---']

    # NAME
    name = d.loc[2][lang].strip()
    lines.append('# Display name')
    lines.append('name: {}\n'.format(name))

    # shortName
    shortname = d.loc[1][lang].strip()
    lines.append('# Username (this should match the folder name')
    lines.append('authors:')
    lines.append('- {}\n'.format(shortname))

    # group
    group = get_group(d, lang)
    lines.append('# Organizational groups that you belong to (for People widget)')
    lines.append('#  Set this to `[]` or comment out if you are not using People widget.')
    lines.append('user_groups:')
    lines.append('- {}\n'.format(group))

    # role
    role = d.loc[3][lang].strip()
    lines.append('# Role/position')
    lines.append('role: {}\n'.format(role))

    # org
    org = get_org(d, lang)
    lines.append('# Organizations/Affiliations')
    lines.append('organizations:')
    lines.append('- name: {}'.format(org))
    lines.append('  url: {}\n'.format(""))

    # short
    bio = get_bio(d, lang)
    lines.append('# Short bio (displayed in user profile at end of posts')
    lines.append('bio: {}\n'.format(bio))

    # intersets
    inte = get_inte(d, lang)
    lines.append('# Intersets, displayed at end of portrait')
    lines.append('interests:')
    for i in inte:
        lines.append('- {}'.format(i))
    lines.append('\n')

    # education
    lines.append('# Show the education of user')
    lines.append('education:')
    lines.append('  courses:')
    lines.append(edu_parser(d, 1, lang, yaml=True)) # postdoc
    lines.append(edu_parser(d, 2, lang, yaml=True)) # phd
    lines.append(edu_parser(d, 3, lang, yaml=True)) # ms
    lines.append(edu_parser(d, 4, lang, yaml=True)) # bs
    lines.append('\n')

    # social
    lines.append('# Social/Academic Networking')
    lines.append('# For available icons, see: https://sourcethemes.com/academic/docs/widgets/#icons')
    lines.append('# For an email link, use "fas" icon pack, "envelope" icon, and a link in the')
    lines.append('# from "mailto:email@abc.com" or "#contact" for contact widget.')
    lines.append('social:')
    lines.append(social_parser(d, 1, lang, yaml=True)) # email
    lines.append(social_parser(d, 2, lang, yaml=True)) # github
    lines.append(social_parser(d, 3, lang, yaml=True)) # twitter

    # user
    lines.append('# Enter email to display Gravatar (if Gravatar enabled in Config)')
    lines.append('email: ""')
    lines.append('\n')    

    # superuser
    lines.append('# Is this the primary user of the site?')
    lines.append('superuser: false')
    lines.append('---')

    # main text
    text = d.loc[18][lang].strip()
    lines.append(text)

    return [shortname, '\n'.join(lines)]


def main():
    if len(sys.argv) < 2:
        sys.exit('python update_member.py [update_all: 0|1]')
    update_all = eval(sys.argv[1])

    # script directory
    src_dir = os.path.dirname(os.path.realpath(__file__))
    base_dir = os.path.dirname(src_dir)

    # static_dir
    static_dir = os.path.join(base_dir, 'static', 'people')
    # author_dir
    author_dir = os.path.join(base_dir, 'content', 'authors')

    # iterator xlsx files
    for f in os.listdir(static_dir):
        # xlsx file
        if not f.endswith('.xlsx'):
            continue
        # source files
        xlsx_file = os.path.join(static_dir, f)
        shortname, md_text = people_md(xlsx_file, 'en')
        img_file = avatar_picker(shortname, base_dir)
        img_ext = os.path.splitext(img_file)[1]

        # target files
        people_dir = os.path.join(author_dir, shortname)
        md_file = os.path.join(people_dir, '_index.md')
        avatar_file = os.path.join(people_dir, 'avatar' + img_ext)
        # check dir
        if not os.path.exists(people_dir):
            os.makedirs(people_dir)

        # copy avatar
        shutil.copyfile(img_file, avatar_file)
        print(img_file)
        # write md
        if update_all or not os.path.exists(md_file):
            print('{:>15s} | {} Done'.format(shortname, 'people added,updated '.ljust(50, '.')))
            with open(md_file, 'wt') as fo:
                fo.write(md_text)



if __name__ == '__main__':
    main()

