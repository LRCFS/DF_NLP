"""Contains variable to update SpaCy stop words and lemmatization rules"""

SCI_PAPER_STOP = {"additional", "answer", "approach", "art", "beebe",
                  "breitinger", "challenge", "choo", "concept", "conduct",
                  "data", "describe", "discuss", "enumerate", "experiment",
                  "experimental", "face", "false", "fig", "figs", "focus",
                  "follow", "follows:-", "formula", "future", "garfinkel",
                  "general", "illustrate", "important", "information",
                  "interesting", "keyword", "list", "literature", "method",
                  "methodology", "model", "note", "overview", "page", "paper",
                  "point", "previous", "prior", "propose", "purpose",
                  "question", "quick", "®", "result", "related", "relevant",
                  "research", "review", "roussev", "search", "section",
                  "spafford", "state", "subsection", "table", "term", "™",
                  "useful", "view", "×", "work"}

GENERIC_STOP = {"activity", "applicable", "autopsy", "carrier", "calculate",
                "consideration", "contain", "customer", "different",
                "facilitate", "feasible", "good", "huge", "increase",
                "issue", "know", "large", "leverage", "mechanism", "new",
                "organizational", "pertinent", "reasonable", "requirement",
                "satisfy", "scale", "scalpel", "simplicity", "sophisticated",
                "total", "underlie", "unused", "usage", "usefulness",
                "utilization", "valuable"}

DIGTAL_FORENSICS_STOP = {"agency", "analyse", "analysis", "application",
                         "client", "clue", "community", "computing",
                         "computation", "computational", "credential", "crime",
                         "custody", "cyber", "dataset", "default", "device",
                         "digital", "domain", "enforcement", "estimation",
                         "evidence", "examiner", "forensic", "forensics",
                         "ground", "insight", "investigation", "investigator",
                         "laboratory", "law", "practitioner", "process",
                         "programming", "proof", "scenario", "scene", "setup",
                         "similarity", "taxonomy", "technique", "tool",
                         "truth", "user", "vendor"}
