# DF_NLP
Grouping of scripts related to digital forensics NLP

<!-- TOC -->
<details open="open">
    <summary> Table of contents </summary>
    <ol>
        <li><a href="#about-the-project">About the project</a></li>
        <li><a href="#requirements">Requirements</a></li>
        <li><a href="#getting-started">Getting started</a></li>
        <li><a href="#usage">Usage</a>
            <ul>
                <li><a href="#corpus-creation">Corpus creation</a></li>
                <li><a href="#ate-methods-benchmarking">ATE methods benchmarking</a></li>
                <li><a href="#corpus-terms-extraction">Corpus terms extraction</a></li>
            </ul>
        </li>
        <li><a href="#data">Data</a></li>
        <li><a href="#roadmap">Roadmap</a></li>
        <li><a href="#contributing">Contributing</a></li>
        <li><a href="#versions">Versions</a></li>
        <li><a href="#author">Author</a></li>
        <li><a href="#license">License</a></li>
        <li><a href="#acknowledgement">Acknowledgement</a></li>
    </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About the project
This repository gathers several NLP tools used on digital forensics data. It
allows:
- the extraction of full text and abstracts from a raw corpus;
- the benchmarking of several ATE methods against the [SemEval-2017 Task 10](https://scienceie.github.io/task.html) corpus, and;
- the extraction of candidates terms from digital forensics full texts and abstracts.

<!-- REQUIREMENTS -->
## Requirements
In order to use this package you will need the latest version of [Python](https://www.python.org/downloads/), git and an access to the [LRCFS github](https://github.com/LRCFS).


<!-- GETTING STARTED -->
## Getting started
Create and activate your virtual environment:
```bash
# Example with the venv package
python3 -m venv ~/.venv/myenv
source ~/.venv/myenv/bin/activate
```

Download the last version of DF_NLP and install it:
```bash
git clone git@github.com:legallm/DF_NLP.git
python3 -m pip install -e ./DF_NLP
```

Install all the dependencies and test the package:
```bash
cd ./DF_NLP
make init
make tests
```


<!-- USAGE -->
## Usage
### Corpus creation
The corpus creation is handled by [corpus.py](https://github.com/legallm/DF_NLP/blob/main/DF_NLP/corpus.py). To create the corpus you will need the CLS JSON bibliography and the authentication keys to access Elsevier, Springer and IEEE APIs. The IEEE API has a limited use (200 query per day) and therefore you may need to provide a threshold value to ignore the first IEEE references handled in a previous run of the script. The new threshold value to use is provided at each exception raising.


To run the creation of the corpus use the following command:
```bash
# You can run the script either without providing any threshold
./DF_NLP/corpus.py ./path_to_input.json ./path_to_output_dir/ ./path_to_API_keys.json

# or with providing it (the first 344 IEEE references will be ignored here)
./corpus.py ./path_to_input.json ./path_to_output_dir/ ./path_to_API_keys.json --threshold 345
```

The file containing the API keys must have the following format:
```json
{
    "elsevier": "Elsevier_token",
    "springer": "Springer_token",
    "ieee": "IEEE_token"
}
```

The script will create an output file named *corpus.json* containing the main data of the references enriched with abstracts and path to the full texts (if available). It will also write in the output directory all the full texts.

### ATE methods benchmarking
A training corpus can be used to benchmarking 5 ATE methods:
- [Basic](https://aran.library.nuigalway.ie/handle/10379/4130)
- [ComboBasic](https://www.ispras.ru/en/publications/2015/methods_and_software_for_terminology_extraction_from_domain_specific_text_collection/)
- [C-value](https://www.researchgate.net/publication/281074961_Combining_C-value_and_Keyword_Extraction_Methods_for_Biomedical_Terms_Extraction)
- [Weirdness](https://www.researchgate.net/publication/221037471_University_of_Surrey_Participation_in_TREC8_Weirdness_Indexing_for_Logical_Document_Extrapolation_and_Retrieval_WILDER)

Those ATE methods can be benchmarked using one or more [scoring methods](https://www.cambridge.org/core/journals/natural-language-engineering/article/keyword-extraction-issues-and-methods/84BFD5221E2CA86326E5430D03299711) from the following list:
- **PRF**, which compute 3 scores for the extraction: its precision, recall and the F-Measure which balance the 2 previous features. 
- **Precision@K**, which compute the precision for terms above the rank K.
- **Bpref**, which evaluate the quantity of incorrect terms with an higher rank than correct ones.

The default benchmark use the PRF scoring:
```bash
./benchmarking.py ./path_to_the_input_dir/ ./path_to_the_output_dir/
```

But you can decide which scoring method to use:
```bash
# You can use Bpref
./benchmarking.py ./path_to_the_input_dir/ ./path_to_the_output_dir/ --scoring Bpref

# You can use several scoring methods
./benchmarking.py ./path_to_the_input_dir/ ./path_to_the_output_dir/ --scoring PRF Bpref
```

Finally to use the P@K you may be satisfied by the default rank or want to provide your own:
```bash
# Use default ranks (500, 1000 and 5000)
./benchmarking.py ./path_to_the_input_dir/ ./path_to_the_output_dir/ --scoring P@K

# Or provide your own ranks
./benchmarking.py ./path_to_the_input_dir/ ./path_to_the_output_dir/ --scoring PRF P@K --ranks 64 128 256 412
```


### Corpus terms extraction
Once you have chosen the relevant ATE method to use you can run the ATE pipeline on your corpus. You can use one or more ATE methods, the default one being the Weirdness.

```bash
# You can use Weirdness by default
./ate.py ./path_to_corpus.json ./path_to_output_dir/

# Or select one or more ATE method
./ate.py ./path_to_corpus.json ./path_to_output_dir/ --ate Basic Cvalue
```

<!-- DATA -->
## Data
The data directory contains several input and output related to this project:
- **biblio.json**, which is the input file for the corpus creation.
- **corpus.zip**, which is an archive containing the corpus.json and the full texts.
- **Training_set_SemEval_2017_Task_10**, which is the directory containing the text and annotated files for the benchmark.

<!-- MISC. -->
## Roadmap
See the [open issues](https://github.com/legallm/DF_NLP/issues) for a list of
proposed features (and known issues).

## Contributing
Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Versions
For the versions available, see the [tags](https://github.com/legallm/DF_NLP/tags) on this repository.

## Author(s)
- **Maël LE GALL** ([legallm](https://github.com/legallm)) - *Initial work* - mael.le_gall@tutanota.com

## License
Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgement
* [Best README template](https://github.com/othneildrew/Best-README-Template)
* [PyATE project](https://github.com/kevinlu1248/pyate)
* [SemEval-2017 Task 10](https://scienceie.github.io/task.html)