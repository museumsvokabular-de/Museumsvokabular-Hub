import lxml.etree
import glob
from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import SKOS, RDF, DC, DCTERMS, RDFS
import random

def idGenerator(size=6, chars= "ABCDFG123456789"):
    return "".join(random.choice(chars) for _ in range(size))

def createNewId(checkList):
    x = idGenerator()
    hasLetters = any(c.isalpha() for c in x)
    hasNumbers = any(c.isdigit() for c in x)
    while x in checkList or not hasLetters or not hasNumbers or not x[0].isalpha():
        x = idGenerator()
        hasLetters = any(c.isalpha() for c in x)
        hasNumbers = any(c.isdigit() for c in x)
    return x

numberOfIds = 10000
idList = []
checkList = []
for i in range(numberOfIds):
    ID = createNewId(checkList)
    idList.append(ID)
    checkList.append(ID)

allRdfFiles = [x for x in glob.glob("*.rdf") if not "modified" in x]
languageLabel = "@de"
descriptionDict = {
    "gefaess": {"description": "Gefäße und Formen. Eine Typologie für Museen und Sammlungen", "title":"Gefäßtypologie", "author":"Landesstelle für die nichtstaatlichen Museen in Bayern"}, 
    "ackerbau":{"description":"Thesaurus zu Ackerbaugerät, Feldbestellung - Landwirtschaftliche Transport- und Nutzfahrzeuge - Werkzeuge (Holzbearbeitung)", "title":"Ackerbaugeräte-Systematik", "author":"Spengler, W. Eckehart"},
    "grobsystematik":{"description":"EDV-gestützte Bestandserschließung in kleinen und mittleren Museen", "title":"Grobsystematik", "author":"Institut für Museumskunde"},
    "moebel":{"description":"Möbel. Eine Typologie für Museen und Sammlungen", "title":"Möbeltypologie", "author":["Westfälisches Museumsamt", "Landesstelle für die nichtstaatlichen Museen in Bayern"]},
    "spitzen":{"description":"Systematik für Spitzen und Stickereien", "title":"Spitzensystematik", "author":"Sächsische Landesstelle für Museumswesen"},
    "technik_spitzen":{"description":"Systematik für die Technik zur Herstellung von Spitzen und Stickereien", "title":"Spitzentechnik-Systematik", "author":"Sächsische Landesstelle für Museumswesen"},
    }

#conceptDict = {}
#conceptSchemesDict = {}

generalURI = "https://museumsvokabular-de.github.io/Museumsvokabular-Hub/"

for rdfFile in allRdfFiles:
    #replace "xml:base="http://www.museumsvokabular.de/museumvok/" in file with generalURI
    with open(rdfFile, 'r', encoding="utf-8") as f:
        text = f.read()
        text = text.replace("xml:base=\"http://www.museumsvokabular.de/museumvok/\"", "xml:base=\""+generalURI+"\"")
    with open(rdfFile, 'w', encoding="utf-8") as f:
        f.write(text)
    # load rdf file with encoding utf-8
    tree = lxml.etree.parse(rdfFile, parser=lxml.etree.XMLParser(encoding='utf-8'))

    # find first element with tag "{http://www.w3.org/2004/02/skos/core#}Concept"
    firstConcept = tree.find("{http://www.w3.org/2004/02/skos/core#}Concept")
    scheme = firstConcept.find("{http://www.w3.org/2004/02/skos/core#}inScheme").text

    """
    # check if scheme is already key in conceptSchemesDict
    if scheme in conceptSchemesDict:
        conceptDict[scheme] = idList.pop()
    schemeURI = URIRef(generalURI + conceptDict[scheme])
    baseURI = URIRef(generalURI + conceptDict[scheme] + "/")
    """

    schemeURI = URIRef(generalURI + scheme)

    print(schemeURI)

    root = tree.getroot()

    skosList = ["{http://www.w3.org/2004/02/skos/core#}narrower",
                "{http://www.w3.org/2004/02/skos/core#}broader"]
    topConcepts = []
    #iterate over all elements of root
    for element in root.iter():
        if element.tag == "{http://www.w3.org/2004/02/skos/core#}Concept":
            uuid= element.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")
            element.set("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", uuid.replace(" ", "_"))
            for subElement in element.iter():
                if subElement.tag in skosList:
                    subElement.set("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource", subElement.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource").replace(" ", "_"))
                    if not scheme+"/" in subElement.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"):
                        # change tag to broaderMatch or narrowerMatch
                        subElement.tag = "{http://www.w3.org/2004/02/skos/core#}broadMatch" if subElement.tag == "{http://www.w3.org/2004/02/skos/core#}broader" else "{http://www.w3.org/2004/02/skos/core#}narrowMatch"
                if subElement.tag == "{http://www.w3.org/2004/02/skos/core#}inScheme":
                    #subElement.text = schemeUUID
                    # delete element
                    element.remove(subElement)
            examples = element.findall("{http://www.w3.org/2004/02/skos/core#}example")
            if len(examples) > 0:
                if len(examples) > 1:
                    exampleText = ""
                    for example in examples:
                        exampleText += example.text + ", "
                    exampleText += languageLabel
                    # delete all but one element in examples
                    exampleLenght = len(examples)
                    while exampleLenght > 1:
                        element.remove(examples[exampleLenght-1])
                        exampleLenght -= 1
                    examples[0].text = exampleText
                else:
                    examples[0].text += languageLabel
            if subElement.tag == "{http://www.w3.org/2004/02/skos/core#}example":
                subElement.text += languageLabel
            # find all elements with tag "{http://www.w3.org/2004/02/skos/core#}definition" and add language label
            definitions = element.findall("{http://www.w3.org/2004/02/skos/core#}definition")
            if len(definitions) > 1:
                definitionText = ""
                for definition in definitions:
                    definitionText += definition.text
                definitionText += languageLabel
                # delete all but one element in definitions
                definitionLenght = len(definitions)
                while definitionLenght > 1:
                    element.remove(definitions[definitionLenght-1])
                    definitionLenght -= 1
                definitions[0].text = definitionText
            elif len(definitions) == 1:
                definitions[0].text += languageLabel
    tree.write(scheme+"_modified.rdf", pretty_print=True, encoding="utf-8")
    g = Graph()
    g.parse(scheme+"_modified.rdf", format="xml", encoding="utf-8")
    g.add ((schemeURI, RDF.type, SKOS.ConceptScheme))
    g.add ((schemeURI, DC.title, Literal(descriptionDict[scheme]["title"])+languageLabel))
    g.add ((schemeURI, DC.description, Literal(descriptionDict[scheme]["description"])+languageLabel))
    # iterate over all nodes which belong to skos:concept and add the scheme to them
    for s, p, o in g.triples((None, RDF.type, SKOS.Concept)):
        g.add((s, SKOS.inScheme, schemeURI))
        # if the concept has no broader concept, add it to the topConcepts list
        if not (s, SKOS.broader, None) in g:
            topConcepts.append(s)
    # add top concepts to the scheme
    for topConcept in topConcepts:
        g.add((schemeURI, SKOS.hasTopConcept, topConcept))
    g.serialize(scheme+"_modified.ttl", format="turtle", encoding="utf-8")
    with open(scheme+"_modified.ttl", 'r', encoding="utf-8") as f:
        text = f.read()
        text = text.replace('@de"', '"@de')
        text = text.replace('^^rdf:XMLLiteral', '')
    with open(scheme+"_modified.ttl", 'w', encoding="utf-8") as f:
        f.write(text)