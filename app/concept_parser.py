from typing import Dict, Any, Tuple
from bs4 import BeautifulSoup
import requests
from typing import NamedTuple, List
import re


# From: https://stackoverflow.com/questions/4576077/how-can-i-split-a-text-into-sentences
alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"


def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences


class Related(NamedTuple):

    """ Represents a related concept from ConceptNet.
    """

    name: str
    weight: float

    def __repr__(self):
        return f"<Related: name={self.name} weight={self.weight}>"


class ConceptMention:

    """
    A mention of a concept in an article.
    """

    name: str
    mentions: List[str]
    get_related: bool
    related: List[Related]

    def __init__(self, name: str, mentions: List[str], get_related: bool):
        """
        :param name: Concept name.
        :param mentions: Dict start_char: sentence.
        :param get_related: True if ConceptNet should be searched else False.
        """
        self.name = name
        self.mentions = mentions
        self.get_related = get_related
        self.related = []

    def __repr__(self):
        return f"<ConceptMention name=\'{self.name}\' count={len(self.mentions)}>"


def html_to_text(content: str) -> str:

    """ Convert an HTML string to a text string.

    :param content: HTML string.
    :return: Text string (HTML Tags stripped)
    """

    soup = BeautifulSoup(content, 'html.parser')
    return soup.get_text()


def parse_concepts(content: str) -> List[ConceptMention]:

    """ Parse concepts from an html string.

    :param content: Article content
    :return: List of ConceptMentions or None
    """

    # Parse html
    soup = BeautifulSoup(content, 'html.parser')
    concepts = soup.find_all("span", class_="concept")

    sentinel = "☀"
    data: Dict[str, Dict[str, Any]] = {}

    # Get concepts
    for concept in concepts:
        # HTML Element info
        concept_text = concept.string
        # TODO: Bug: This adds the lower version to the mention text
        concept_text = concept_text.lower()
        attrs = concept.attrs

        # Finding index within text string
        concept.string = sentinel
        idx = soup.get_text().index(sentinel)
        concept.string = concept_text

        # Whether or not to search ConceptNet
        get_related = True \
            if attrs.get("get_related") and attrs["get_related"] == 1 \
            else False

        # Add Concept info
        if not data.get(concept_text):
            data[concept_text] = {"mentions": [], "get_related": True}

        # Find the sentence context of the concept
        sentences = split_into_sentences(soup.get_text())
        start_char = 0
        end_char = 0
        for sentence in sentences:
            end_char += len(sentence)
            if concept_text in sentence:
                if start_char <= idx <= end_char:
                    mention_sentence = sentence.replace(concept_text, f"<span class='concept'>{concept_text}</span>")
                    data[concept_text]["mentions"].append(sentence)
                    continue
            start_char = end_char + 1

        data[concept_text]["get_related"] = get_related

    return [
        ConceptMention(name=key, mentions=value["mentions"], get_related=value["get_related"])
        for key, value in data.items()
    ]


class ConceptNet:

    """ Enables querying related concepts from ConceptNet.
    """

    base_url: str
    related_url: str

    def __init__(self):
        self.base_url = "http://api.conceptnet.io"
        self.related_url = "http://api.conceptnet.io/related"

    def _get_related_concepts(self, name: str) -> List[Related]:

        """ Query the ConceptNet related API.

        :param name: Name of the concept.
        :return: A list of related concepts.
        """

        url = f"{self.related_url}/c/en/{name.lower().replace(' ', '_')}?filter=/c/en"
        obj = requests.get(url).json()
        ret = []
        for item in obj["related"]:
            name = item["@id"].split("/")[3].replace('_', " ")
            weight = item["weight"]
            ret.append(Related(name=name, weight=weight))
        return ret

    def add_related_concepts(self, concepts: List[ConceptMention]) -> List[ConceptMention]:

        """ Get related concepts and weights from ConceptNet.

        :return: A list of ConceptMentions
        """

        for concept in concepts:
            if not concept.get_related:
                continue
            related = self._get_related_concepts(concept.name)
            concept.related = related
        return concepts


