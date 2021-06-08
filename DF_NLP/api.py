"""Module handling process of API request answers."""

import xml.etree.ElementTree as ET
import re

# Common namespace used in Elsevier XML
ns = "{http://www.elsevier.com/xml/common/dtd}"


def _process_elsevier_para(para: ET.Element) -> str:
    """Extract text content from an Elsevier paragraph.

    Args:
        para: XML element containing a paragraph.

    Returns:
        Text content of the paragraph.

    Raises:
        ValueError: Find an unknown subtag in the paragraph.
    """
    text = f"{para.text}"

    for child in list(para):
        if child.tag == f"{ns}list":
            items = child.findall(f".//{ns}para")
            text += "\n".join([f"- {i.text}" for i in items])
            text += "\n"
        else:
            raise ValueError(f"Unknown para tag: {child.tag}")

    text = re.sub("( *\n *)+", " ", text)
    text = re.sub("^ ", "", text)

    return text


def _process_elsevier_section(section: ET.Element, text: str) -> str:
    """Extract text content from an Elsevier section.

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
        if child.tag == f"{ns}label":
            continue
        elif child.tag == f"{ns}section-title":
            text += f"{child.text}\n"
        elif child.tag == f"{ns}para":
            text += f"{_process_elsevier_para(child)}\n"
        elif child.tag == f"{ns}section":
            text = _process_elsevier_section(child, text)
        else:
            raise ValueError(f"Unknown section tag: {child.tag}")

    return text


def process_elsevier(answer: str, path: str) -> str:
    """Extract text content from the Elsevier answer.

    Args:
        answer: Raw Elsevier XML answer as string.
        path: Path where to write the resulting file.

    Returns:
        Processed Springer XML answer as string.

    Raises:
        NameError: Full text is unavailable.
        ValueError: Find an unknown subtag in the root.
    """
    # Remove tags cutting text content
    answer = re.sub(r',?<ce:cross-ref[ \w="]+>', "", answer)
    answer = re.sub("</ce:cross-ref>", "", answer)
    answer = re.sub(r" \[\d+\]", "", answer)
    answer = re.sub(r'<ce:sup[\w ="]+>\d+</ce:sup>', "", answer)
    answer = re.sub(r'<ce:footnote[ \w="]+>(\n.+){3}</ce:footnote>',
                    "", answer)
    answer = re.sub(r'(\n\s+)?<ce:float-anchor[ \w="]+/>', "", answer)
    answer = re.sub(r'<ce:inter-ref[ \w=":/.]+>[\w:/.]+</ce:inter-ref>',
                    "", answer)
    answer = re.sub("<ce:display>(\n.+){5}</ce:display>", "", answer)
    answer = re.sub("</?ce:bold>", "", answer)
    answer = re.sub("</?ce:italic>", "", answer)

    root = ET.fromstring(answer)
    root = root.find(f".//{ns}sections")
    text = str()

    if not root:
        raise NameError("Full text unavailable!")

    # Clear the file
    with open(path, "w") as f:
        f.write("")

    for child in list(root):
        if child.tag == f"{ns}section":
            with open(path, "a+") as f:
                f.write(f"{_process_elsevier_section(child, text)}\n")
        else:
            raise ValueError(f"Unknown root tag: {child.tag}")

    return answer


def get_elsevier_abstract(answer: str) -> str:
    """Extract abstract from the Elsevier answer.

    Args:
        answer: Raw Elsevier XML answer as string.

    Returns:
        Abstract of the reference as string.
    """
    root = ET.fromstring(answer)
    desc = root.find(".//{http://purl.org/dc/elements/1.1/}description").text

    desc = re.sub("\n +", "", desc)

    return desc


def _process_springer_para(para: ET.Element) -> str:
    """Extract text content from a Springer paragraph.

    Args:
        para: XML element containing a paragraph.

    Returns:
        Text content of the paragraph.

    Raises:
        ValueError: Find an unknown subtag in the paragraph.
    """
    text = f"{para.text}"

    for child in list(para):
        if child.tag == "list":
            items = child.findall(".//p")
            text += "\n".join([f"- {i.text}" for i in items])
            text += "\n"
        else:
            raise ValueError(f"Unknown para tag: {child.tag}")

    text = re.sub("( *\n *)+", " ", text)
    text = re.sub("^ ", "", text)

    return text


def _process_springer_section(section: ET.Element, text: str) -> str:
    """Extract text content from a Springer section.

    Args:
        section: XML element containing a section.
        text: Text already found in this section.

    Returns:
        Text content of the section.

    Raises:
        ValueError: Find an unknown subtag in the section.
    """
    for child in list(section):
        if child.tag == "title":
            text += f"{child.text}\n"
        elif child.tag == "p":
            text += f"{_process_springer_para(child)}\n"
        elif child.tag == "sec":
            text = _process_springer_section(child, text)
        else:
            raise ValueError(f"Unknown section tag: {child.tag}")

    return text


def process_springer(answer: str, path: str) -> str:
    """Extract text content from the Springer answer.

    Args:
        answer: Raw Springer XML answer as string.
        path: Path where to write the resulting file.

    Returns:
        Processed Springer XML answer as string.

    Raises:
        NameError: Full text is unavailable.
        ValueError: Find an unknown subtag in the root.
    """
    # Remove tags cutting text content
    answer = re.sub(r'((, )|–)?<xref[- \w="]+>', "", answer)
    answer = re.sub("</xref>", "", answer)
    answer = re.sub(r" \[\d+\]", "", answer)
    # Need to add carriage return...
    answer = re.sub(">(?=<label>)", ">\n", answer)
    answer = re.sub("(?<=</label>)<", "\n<", answer)
    answer = re.sub(">(?=</caption>)", ">\n", answer)
    answer = re.sub(">(?=<graphic)", ">\n", answer)
    answer = re.sub(">(?=</fig>)", ">\n", answer)
    # ...to improve identification & deletion of figure tags
    answer = re.sub(r'\n<fig[ \w="]+>(\n.+){4}\n</fig>', "", answer)
    answer = re.sub("</?bold>", "", answer)
    answer = re.sub("</?italic>", "", answer)
    answer = re.sub("</?sub>", "", answer)
    answer = re.sub("<sup>", "^", answer)
    answer = re.sub("</sup>", "", answer)
    answer = re.sub("\xa0", " ", answer)

    root = ET.fromstring(answer)
    root = root.find(".//body")
    text = str()

    if not root:
        raise NameError("Full text unavailable!")

    # Clear the file
    with open(path, "w") as f:
        f.write("")

    for child in list(root):
        if child.tag == "sec":
            with open(path, "a+") as f:
                f.write(f"{_process_springer_section(child, text)}\n")
        else:
            raise ValueError(f"Unknown root tag: {child.tag}")

    return answer


def get_springer_abstract(answer: str) -> str:
    """Extract abstract from the Springer answer.

    Args:
        answer: Raw Springer XML answer as string.

    Returns:
        Abstract of the reference as string.
    """
    root = ET.fromstring(answer)
    root = root.find("./records/article/front/article-meta/abstract")
    text = str()

    for child in list(root):
        # Ignore title which is 'Abstract'
        if child.tag == "title":
            continue
        if child.tag == "sec":
            text += _process_springer_section(child, text)
        else:
            raise ValueError(f"Unknown root tag: {child.tag}")

    return text
