"""Module handling process of API request answers."""

import xml.etree.ElementTree as ET
import re
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
    # Clean non-body tags
    answer = re.sub("<body>.+(\n.+)*<body>", "<body>", answer)
    answer = re.sub("</body>.+(\n.+)*</body>", "</body>", answer)
    # Remove tags cutting text content
    answer = re.sub(r',?<ce:cross-ref[ \w="]+>', "", answer)
    answer = re.sub("</ce:cross-ref>", "", answer)
    answer = re.sub(r'((, )|–)?</?xref[- \w="]*>', "", answer)
    answer = re.sub(r" (\[\d+\])+", "", answer)
    answer = re.sub(r'<xref[- \w="]+/>', "", answer)
    answer = re.sub("<(?=fn )", "\n<", answer)
    answer = re.sub("(?<=</fn)>", ">\n", answer)
    answer = re.sub("\n<fn .+\n", "", answer)
    answer = re.sub(r'<ce:footnote[ \w="]+>(\n.+){3}</ce:footnote>',
                    "", answer)
    answer = re.sub(r'(\n\s+)?<ce:float-anchor[ \w="]+/>', "", answer)
    answer = re.sub(r'<ce:inter-ref[ \w=":/.]+>[\w:/.]+</ce:inter-ref>',
                    "", answer)
    answer = re.sub("<ce:display>(\n.+){5}</ce:display>", "", answer)
    answer = re.sub(r'</?ext-link[- \w=":/.,?&;%#~]*>', "", answer)
    answer = re.sub("</?bold>", "", answer)
    answer = re.sub("</?uri>", "", answer)
    answer = re.sub("</?italic>", "", answer)
    answer = re.sub("</?sub>", "", answer)
    answer = re.sub("</?sc>", "", answer)
    answer = re.sub("<sup>", "^", answer)
    answer = re.sub("</sup>", "", answer)
    answer = re.sub("</?ack>", "", answer)
    answer = re.sub("\xa0", " ", answer)
    # Need to add carriage return...
    answer = re.sub(">(?=<label>)", ">\n", answer)
    answer = re.sub("(?<=</label>)<", "\n<", answer)
    answer = re.sub(">(?=</caption>)", ">\n", answer)
    answer = re.sub(">(?=<graphic)", ">\n", answer)
    answer = re.sub(">(?=</fig>)", ">\n", answer)
    # ...to improve identification & deletion of figure tags
    answer = re.sub(r'\n?<fig[ \w="]+>(\n.+){4}\n</fig>', "", answer)
    # Remove formula
    answer = re.sub(r'\n\s*\\usepackage\{\w+\}', "", answer)
    answer = re.sub(r'\n\s*\\setlength[-\w\{\}\\]+', "", answer)
    answer = re.sub(r'\n\t+(\\)+begin', "\begin", answer)
    answer = re.sub("<(?=tex-math)", "\n<", answer)
    answer = re.sub("(?<=</tex-math)>", ">\n", answer)
    answer = re.sub("<tex-math .+>\n+", "", answer)
    answer = re.sub(r'<inline-graphic[ \w=":.]+/>', "", answer)
    answer = re.sub(r'<(?=mml:math[ \w="]*>)', "\n<", answer)
    answer = re.sub("((?<=</mml:math)>)\n?", ">\n", answer)
    answer = re.sub(r'<mml:math[ \w="]*>.+</mml:math>\n', "", answer)
    answer = re.sub("<alternatives>\n</alternatives>", "", answer)
    answer = re.sub(
        r'<inline-formula[ \w="]*>\n*</inline-formula>', "", answer)
    answer = re.sub(r'<alternatives>\n*<graphic[ \w=".:]+/></alternatives>',
                    "", answer)
    answer = re.sub(r'<disp-formula[ \w="]*>\n<label>.+</label>\n', "", answer)
    answer = re.sub(r'</?disp-formula[ \w="]*>', "", answer)
    # Remove algorithms
    answer = re.sub(r'<alg-item[ \w="]+>(\n.+){2}</alg-item>', "", answer)
    answer = re.sub(r'<algorithm[- \w="]+>(\n.+){2}</algorithm>', "", answer)
    # Remove tables
    answer = re.sub(r'<caption[ \w=":]+>.+\n</caption>', "", answer)
    answer = re.sub(r'<(?=table-wrap[ \w="]+>)', "\n<", answer)
    answer = re.sub("(?<=</table-wrap)>", ">\n", answer)
    answer = re.sub("<table-wrap .+>(\n.*){2,5}</table-wrap>\n", "", answer)
    # Remove Appendix
    answer = re.sub(r'<app[\w\W]+</app>', "", answer)
    # Fix multispaces
    answer = re.sub(" +", " ", answer)

    return answer


def _process_paragraph(para: ET.Element) -> str:
    """Extract text content from a paragraph.

    Args:
        para: XML element containing a paragraph.

    Returns:
        Text content of the paragraph.

    Raises:
        ValueError: Find an unknown subtag in the paragraph.
    """
    text = f"{para.text}"

    for child in list(para):
        # Ignore labels
        if child.tag == f"{ns}label" or child.tag == "label":
            continue
        # Elsevier
        if child.tag == f"{ns}list":
            items = child.findall(f".//{ns}para")
        # Springer and IEEE
        elif child.tag == "list":
            items = child.findall(".//p")
        else:
            raise ValueError(f"Unknown paragraph tag: {child.tag}")
        text += "\n".join([f"- {i.text}" for i in items])
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
            text += f"{_process_paragraph(child)}\n"
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
            or (api == "springer" and root.find("book-part")):
        raise NameError("Full text unavailable!")

    for child in list(root):
        if child.tag == f"{ns}section" or child.tag == "sec":
            with open(path, "a+") as f:
                f.write(f"{_process_section(child, text)}\n")
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
                text += _process_section(child, text)
            elif child.tag == "p":
                text = _process_paragraph(child)
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

    return desc.text if desc else ""
