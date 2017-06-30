
import requests
import re
import igraph
import cairocffi

import unicodedata
from unidecode import unidecode

from bs4 import BeautifulSoup


def get_article_links(url):

    profile_url = url

    r = requests.get(profile_url)

    soup_profile = BeautifulSoup(r.content, "html.parser")

    print(soup_profile)

    data = soup_profile.find_all("a", {"class": "gsc_a_at"})

    article_links = []

    print(data)

    for article_info in data:

        strings = str(article_info).split()
        link_chunk = strings[2]

        link = re.findall(r'\"(.+?)\"', link_chunk)
        article_links.append(link)

    return article_links


def find_coauthors(links):

    coauthors = []

    for link in links:

        if link == links[-1]:
            print("yeah")

        link_string = str(link)
        link_string = link_string.replace("[", "")
        link_string = link_string.replace("]", "")
        link_string = link_string.replace("'", "")
        link_string = link_string.replace("amp;", "")

        if link_string == "/citations?view_op=view_citation&hl=en&oe=ASCII&user=1UL3-ocAAAAJ&citation_for_view=1UL3-ocAAAAJ:2osOgNQ5qMEC":
            continue

        print("https://scholar.google.com.hk" + link_string)
        r = requests.get("https://scholar.google.com.hk" + link_string)

        soup_article = BeautifulSoup(r.content, "html.parser")

        author_data = soup_article.find_all("div", {"class": "gsc_value"})

        authors = author_data[0]
        author_string = authors.text

        authors = author_string.split(', ')

        title_data = soup_article.find_all("a", {"class": "gsc_title_link"})

        paper = Paper(title_data[0].text)

        for author in authors:  # Iterate through author strings just found on page

            if len(coauthors) == 0:
                coauthor_new = Coauthor(paper, author)
                coauthors.append(coauthor_new)
                continue

            match_found = False
            for coauthor in coauthors:  # Iterate through the existing coauthor objects

                if coauthor.is_a_match(author):  # If this coauthor already exists
                    coauthor.add_paper(paper)  # Add this paper to their "resume"
                    match_found = True
                    break

            if not match_found:  # If the coauthor was never found
                coauthor_new = Coauthor(paper, author)
                coauthors.append(coauthor_new)

        print(authors)

    print(len(coauthors))

    file = open("coauthors-edge-list.txt", "w")

    for coauthor in coauthors:
        print(coauthor.to_string())
        name = str(coauthor.to_string())

        names = name.split()
        name = "".join(names)

        for paper in coauthor.papers:

            title = str(paper.title)
            titles = title.split()
            title = "".join(titles)

            file.write("%s %s\n" % (name, title))

            print("~~%s", paper.title)

    file.close()

    return coauthors


def create_graph():

    graph: igraph.Graph = igraph.Graph.Read_Ncol("new_list.txt", directed=False)
    ##graph1, graph2 = graph.bipartite_projection(False, True, -1, "both")

    graph: igraph.Graph = igraph.Graph.simplify(graph)

    graph.vs["color"] = "#75546E"
    vert = graph.vs.find(name="MichelleReneLowry")
    vert["color"] = "#A3809C"
    vert["label"] = "Me"
    vert["size"] = 40
    vert["label_size"] = 18

    layout = graph.layout("fr").fit_into((200, 600), False)

    igraph.plot(graph, "finished.png", layout=layout, bbox=(1200, 600))

def create_new_list(coauthors):

    file = open("new_list.txt", "w")

    for coauthor in coauthors:

        coauthor1: Coauthor = coauthor
        for coauthor_2 in coauthors:

            coauthor2: Coauthor = coauthor_2

            if coauthor1 != coauthor2:

                for paper in coauthor1.papers:

                    for paper_2 in coauthor2.papers:

                        if paper.title == paper_2.title:
                            names_1 = coauthor1.to_string().split()
                            string_1 = "".join(names_1)

                            names_2 = coauthor2.to_string().split()
                            string_2 = "".join(names_2)

                            file.write(string_1 + " " + string_2 + "\n")

    file.write("PaulBenjaminLowry VernRichardson\n")
    file.write("MichelleReneLowry VernRichardson\n")



class Coauthor(object):

    def __init__(self, paper, name):
        self.papers = [paper]

        name_new = unidecode(name)
        if find_alternate_name(name_new) == "Already Initials":  # If the parameter was initials
            self.initials = name_new
            self.full_name = None
        else:  # If the parameter was a full name
            self.full_name = name_new
            self.initials = None

    def add_paper(self, paper):
        self.papers.append(paper)

    def is_a_match(self, string):

        output = find_alternate_name(string)

        string_s = string

        if len(output) == 2:  # If a new name was found
            alternate = output[0]
            string_s = output[1]
        else:  # If just the alternate was returned
            alternate = output

        string_new = unidecode(string_s)

        # Array of string to check for middle name difference
        name_strings = string_new.split()
        if self.full_name is not None:
            full_name_strings = self.full_name.split()
            if name_strings[0] == full_name_strings[0] and name_strings[-1] == full_name_strings[-1]: # If the first and last names match, then consider it a match
                return True

        if string_new == self.full_name:
            return True
        elif string_new == self.initials:
            return True
        elif alternate == "Already Initials":  # If the name parameter is initials
            if self.full_name is not None:
                if find_alternate_name(self.full_name) == string_new:
                    self.initials = string_new  # Set the initials
                    return True  # The initials match the name
                else:
                    return False
            else:  # If the object only has initials
                if alternate == self.initials:
                    return True
                else:
                    return False
        else:  # If the name parameter was a full name
            if self.initials is not None:
                if alternate == self.initials:
                    self.full_name = string_new  # Set the full name
                    return True
                else:
                    return False
            else:  # If the object only contains a full name
                if string_new == self.full_name:
                    return True
                else:
                    return False

    def to_string(self):
        if self.full_name is None:
            return self.initials
        elif self.initials is None:
            return self.full_name
        else:
            return self.full_name

class Paper(object):

    def __init__(self, title):
        self.title = title


'''
def add_coauthors(coauthors):

    for coauthor in coauthors:
'''


def find_alternate_name(name):

    name_chunks = str(name).split()

    first_name = name_chunks[0]

    if first_name == first_name.upper() and len(first_name) < 4:  # If the name is already capitalized (i.e. Initials)
        return "Already Initials"
    else:

        altered_name = None

        if len(first_name) > 3 and first_name == first_name.upper():

            # Properly capitalize the name
            first_letter = first_name[0:1]
            other_letters = first_name[1:len(first_name)]

            first_name = first_letter + other_letters.lower()
            name_chunks[0] = first_name

            altered_name = " ".join(name_chunks)

        if altered_name is None:
            return find_initials(name_chunks)
        else:
            return [find_initials(name_chunks), altered_name]


def find_initials(name_list):

    initial_string = ""

    for name in name_list:

        if name == name_list[-1]:  # If it is the last name
            initial_string += " "
            initial_string += name
        else:
            initial_string += str(name)[0].capitalize()

    return initial_string

'''
coauthor = Coauthor("Paul Benjamin Lowry", None)
print(coauthor.is_a_match("PB Lowry"))
print(coauthor.initials)

coauthor2 = Coauthor(None, "PB Lowry")
print(coauthor.is_a_match("Paul Benjamin Lowry"))
print(coauthor.full_name)
print(coauthor.is_a_match("Paul Benjamin Lowry"))
'''

##print(find_alternate_name("Paul Benjamin Lowry"))


##links = get_article_links("https://scholar.google.com.hk/citations?hl=en&user=1UL3-ocAAAAJ")
print("what")
##print(links)
##coauthors_list = find_coauthors(links)
##create_txt_file(coauthors_list)



##create_new_list(coauthors_list)
create_graph()





