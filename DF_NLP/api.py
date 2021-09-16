"""Module handling process of API request answers."""

import re
import xml.etree.ElementTree as ET
from typing import Literal

# Determined API type
Api = Literal["elsevier", "ieee", "springer"]
# Common namespace used in Elsevier XML
ns = "{http://www.elsevier.com/xml/common/dtd}"


def _process_xml(answer: str) -> str:
    """Process XML to remove unwanted tags.

    Args:
        answer: Raw XML answer as a string.

    Returns:
        Harmonized XML string as answer.
    """
    # Flatten the XML
    answer = re.sub(r'\n\s*', " ", answer)
    # Clean non-body tags
    answer = re.sub("<body>.+?<body>", "<body>", answer)
    answer = re.sub("</body>.+?</body>", "</body>", answer)
    # Remove tags cutting text content
    answer = re.sub(r'</?fn[ \w="]*>', "", answer)
    answer = re.sub(r'<ce:float-anchor[ \w="]*/>', "", answer)
    answer = re.sub(r'</?ext-link[- \w=":/.%@#?&;,\[\]()~+*!\'$]*>',
                    "", answer)
    answer = re.sub(r'<ce:hsp[ \w=".]*/>', "", answer)
    answer = re.sub("</?(ce:)?bold>", "", answer)
    answer = re.sub(r'</?uri[- \w=":/.%@#?&;,\[\]()~+*!\'$]*>', "", answer)
    answer = re.sub("</?(ce:)?italic>", "", answer)
    answer = re.sub("</?(ce:)?monospace>", "", answer)
    answer = re.sub(r' ?<(ce:)?sup[ \w="]*> ?', "^", answer)
    answer = re.sub(r' ?<(ce:)?(inf|sub)( [ \w="]*)?> ?', "_", answer)
    answer = re.sub(r'</(ce:)?(sup|inf|sub)>', "", answer)
    answer = re.sub("</?ce:small-caps>", "", answer)
    answer = re.sub(r'<ce:textbox[ \w="]*>.+?</ce:textbox>', "", answer)
    answer = re.sub(r'</?ce:enunciation[ \w="]*>', "", answer)
    answer = re.sub("</?ce:underline>", "", answer)
    answer = re.sub("</?ce:sans-serif>", "", answer)
    answer = re.sub(r'<ce:vsp[ \w=".]*/>', "", answer)
    answer = re.sub("</?sc>", "", answer)
    answer = re.sub("</?ce:cross-out>", "", answer)
    answer = re.sub('<ce:glyph name="sbnd"/>', "-", answer)
    answer = re.sub(r'<ce:anchor[ \w="]*/>', "", answer)
    answer = re.sub(r'</?boxed-text[ \w="]*>', "", answer)
    answer = re.sub("<(def|term)-head>.+?</(def|term)-head>", "", answer)
    answer = re.sub(r'<index-term[ \w="]*>.+?</index-term>', "", answer)
    answer = re.sub("\xa0", " ", answer)
    # Handle references
    answer = re.sub(r'</?ce:cross-refs?[- \w=".]*>', "", answer)
    answer = re.sub(
        r'(&gt;)?</?ce:inter-ref[- \w=":/.%@#?&;,\[\]()~+*!\'$]*>(&lt;)?',
        "", answer)
    answer = re.sub(r'</?ce:intra-ref[- \w=":/.%@#?&;,\[\]()~+*!\'$]*>',
                    "", answer)
    answer = re.sub(r'</?xref[- \w=".]*/?>', " ", answer)
    # Remove footnotes
    answer = re.sub(r'<ce:footnote [ \w="]*>.+?</ce:footnote>', "", answer)
    # Handle quotes
    answer = re.sub(
        r'<ce:displayed-quote[- \w=".]*> ?<ce:simple-para[- \w=".]*>',
        "'", answer)
    answer = re.sub(r'</ce:simple-para> ?<ce:simple-para[- \w=".]*>',
                    "", answer)
    answer = re.sub(r'</ce:simple-para> ?</ce:displayed-quote>', "'", answer)
    answer = re.sub("</ce:simple-para> ?<ce:source>", "'", answer)
    answer = re.sub("</ce:source> ?</ce:displayed-quote>", "", answer)
    answer = re.sub("<disp-quote><p>", "<p>'", answer)
    answer = re.sub("</p></disp-quote>", "'</p>", answer)
    # Remove grant informations
    answer = re.sub(r'</?ce:grant-sponsor[- \w=":/.%@#?&;,\[\]()~+*!\'$]*>',
                    "", answer)
    answer = re.sub(r'</?ce:grant-number[ \w="]*>', "", answer)
    # Remove statements
    answer = re.sub(r'<statement[- \w="]*>', "<p>", answer)
    answer = re.sub(r'</statement>', "</p>", answer)
    # Remove formula
    answer = re.sub(r'<mml:math[ \w=".]*>.+?</mml:math>', "[Formula]", answer)
    answer = re.sub("</?ce:display>", "", answer)
    answer = re.sub(r'<disp-formula[ \w="]*>.+?</disp-formula>',
                    "[Formula]", answer)
    answer = re.sub(r'<ce:formula[ \w="]*>.+?</ce:formula>( *</ce:formula>)*',
                    "[Formula]", answer)
    answer = re.sub(r'<inline-formula[ \w="]*>.+?</inline-formula>',
                    "[Formula]", answer)
    answer = re.sub(r'<disp-formula[- \w="]*>.+?</disp-formula>',
                    "[Formula]", answer)
    # Remove figures
    answer = re.sub(r'<ce:inline-figure[ \w=".]*>.+?</ce:inline-figure>',
                    "[Inline Fig.]", answer)
    answer = re.sub(r'<ce:figure[ \w="]*>.+?</ce:figure>', "[Fig.]", answer)
    answer = re.sub(r'<fig[ \w="]*>.+?</fig>', "[Fig.]", answer)
    # Avoid error after figures deletion by deleting floats section
    answer = re.sub("<ce:floats>.+?</ce:floats>", "", answer)
    # Remove graphics
    answer = re.sub(r'<graphic[- \w=":/.]*>', "[Graphic]", answer)
    answer = re.sub("<opening-graphic>.+?</opening-graphic>", "", answer)
    answer = re.sub(r'<inline-graphic[- \w=":/.%@#?&;,\[\]()~+*!\'$]*>',
                    "[Graphic]", answer)
    # Remove algorithms
    answer = re.sub(r'<algorithm[- \w="]*>.+?</algorithm>', "[Algo]", answer)
    # Remove tables
    answer = re.sub(r'<ce:table[ \w=":/.]*>.+?</ce:table>', "[Table]", answer)
    answer = re.sub(r'<table-wrap[ \w="]*>.+?</table-wrap>', "[Table]", answer)
    # Remove Appendix
    answer = re.sub(r'<app[ \w="]*>.+?</app>', "", answer)
    # Remove Aknowledgements
    answer = re.sub("<ack>.+?</ack>", "", answer)
    # Fix multispaces
    answer = re.sub(" +", " ", answer)

    return answer


def _process_def_list(dlist: ET.Element, text: str) -> str:
    """Extract text content from a def-list.

    Args:
        dlist: XML element containing a def-list
        text: Text already found in this section.

    Returns:
        Text content of the def-list

    Raises:
        ValueError: Find an unknown subtag in the def-list.
    """
    for child in list(dlist):
        # Elsevier term
        if child.tag == f"{ns}def-term":
            text += f"\n- {child.text}: "
        # Elsevier definition
        elif child.tag == f"{ns}def-description":
            text += f"{child.text}"
        # Springer
        elif child.tag == "def-item":
            text += (f"- {child.find('./term').text}: " +
                     f"{child.find('./def/p').text}")
        else:
            raise ValueError(f"Unknown def-list tag: {child.tag}")
    return text


def _process_paragraph(para: ET.Element, text: str) -> str:
    """Extract text content from a paragraph.

    Args:
        para: XML element containing a paragraph.
        text: Text already found in this section.

    Returns:
        Text content of the paragraph.

    Raises:
        ValueError: Find an unknown subtag in the paragraph.
    """
    text += f"{para.text}"

    for child in list(para):
        # Ignore labels
        if child.tag == f"{ns}label" or child.tag == "label":
            continue
        # Elsevier
        if child.tag == f"{ns}list":
            items = child.findall(f".//{ns}para")
            text += "\n".join([f"- {i.text}" for i in items])
        # Springer and IEEE
        elif child.tag == "list":
            items = child.findall(".//p")
            text += "\n".join([f"- {i.text}" for i in items])
        elif child.tag == f"{ns}def-list" or child.tag == "def-list":
            text = _process_def_list(child, text)
        elif child.tag == f"{ns}section-title" or child.tag == "title":
            text += f"{child.text}\n"
        elif child.tag == f"{ns}para" or child.tag == "p":
            text = _process_paragraph(child, text)
        else:
            raise ValueError(f"Unknown paragraph tag: {child.tag}")
        text += "\n"

    text = re.sub("( *\n *)+", " ", text)
    text = re.sub("^ ", "", text)
    return text


def _process_section(section: ET.Element, text: str) -> str:
    """Extract text content from a section.

    Args:
        section: XML element containing a section.
        text: Text already found in this section.

    Returns:
        Text content of the section.

    Raises:
        ValueError: Find an unknown subtag in the section.
    """
    for child in list(section):
        # Ignore labels
        if child.tag == f"{ns}label" or child.tag == "label":
            continue
        elif child.tag == f"{ns}section-title" or child.tag == "title":
            text += f"{child.text}\n"
        elif child.tag == f"{ns}para" or child.tag == "p":
            text = f"{_process_paragraph(child, text)}\n"
        elif child.tag == f"{ns}section" or child.tag == "sec":
            text = _process_section(child, text)
        else:
            raise ValueError(f"Unknown section tag: {child.tag}")

    return text


def process(answer: str, path: str, api: Api) -> None:
    """Extract text content from an API answer.

    Args:
        answer: Raw XML answer as string.
        path: Path where to write the resulting file.
        api: Name of the API providing `answer`. Value of this parameter is
            limited to "elsevier", "ieee" and "springer".

    Raises:
        NameError: Full text is unavailable.
        ValueError: Find an unknown subtag in the root.
    """
    answer = _process_xml(answer)

    root = ET.fromstring(answer)
    if api == "elsevier":
        root = root.find(f".//{ns}sections")
    elif api == "springer" or api == "ieee":
        root = root.find(".//body")
    else:
        raise ValueError("Wrong value for api parameter.")

    text = str()

    if (not root) \
            or (api == "springer" and root.find("book-part") is not None):
        raise NameError("Full text unavailable!")

    for child in list(root):
        if child.tag == f"{ns}section" or child.tag == "sec":
            with open(path, "a+") as f:
                f.write(f"{_process_section(child, text)}\n")
        elif child.tag == f"{ns}para" or child.tag == "p":
            with open(path, "a+") as f:
                f.write(f"{_process_paragraph(child, text)}\n")
        else:
            raise ValueError(f"Unknown root tag: {child.tag}")


def get_elsevier_abstract(answer: str) -> str:
    """Extract abstract from the Elsevier answer.

    Args:
        answer: Raw Elsevier XML answer as string.

    Returns:
        Abstract of the reference as string.
    """
    answer = _process_xml(answer)
    root = ET.fromstring(answer)
    desc = root.find(".//{http://purl.org/dc/elements/1.1/}description")

    if isinstance(desc, ET.Element):
        desc = desc.text
        desc = re.sub("\n +", "", desc)

    return desc


def get_springer_abstract(answer: str) -> str:
    """Extract abstract from the Springer answer.

    Args:
        answer: Raw Springer XML answer as string.

    Returns:
        Abstract of the reference as string.
    """
    answer = _process_xml(answer)
    root = ET.fromstring(answer)
    desc = root.find(".//abstract")
    text = str()

    if desc:
        for child in list(desc):
            # Ignore title which is 'Abstract'
            if child.tag == "title":
                continue
            elif child.tag == "sec":
                text = _process_section(child, text)
            elif child.tag == "p":
                text = _process_paragraph(child, text)
            else:
                raise ValueError(f"Unknown root tag: {child.tag}")

    return text


def get_ieee_abstract(answer: str) -> str:
    """Extract abstract from the IEEE answer.

    Args:
        answer: Raw IEEE XML answer as string.

    Returns:
        Abstract of the reference as string.
    """
    answer = _process_xml(answer)
    root = ET.fromstring(answer)
    desc = root.find("./article/abstract")

    return desc.text if desc is not None else ""
