import lxml.etree
import glob
from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import SKOS, RDF, DC, DCTERMS, RDFS
from Levenshtein import distance

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

generalURI = "https://museumsvokabular-de.github.io/Museumsvokabular-Hub/"

for rdfFile in allRdfFiles:
    with open(rdfFile, 'r', encoding="utf-8") as f:
        text = f.read()
        #replace "xml:base="http://www.museumsvokabular.de/museumvok/" in file with generalURI
        text = text.replace("xml:base=\"http://www.museumsvokabular.de/museumvok/\"", "xml:base=\""+generalURI+"\"")
    
    # load text sting with encoding utf-8
    root = lxml.etree.fromstring(text.encode("utf-8"))

    # find first element with tag "{http://www.w3.org/2004/02/skos/core#}Concept"
    firstConcept = root.find("{http://www.w3.org/2004/02/skos/core#}Concept")
    scheme = firstConcept.find("{http://www.w3.org/2004/02/skos/core#}inScheme").text

    schemeURI = URIRef(generalURI + scheme)

    print(schemeURI)

    skosList = ["{http://www.w3.org/2004/02/skos/core#}narrower",
                "{http://www.w3.org/2004/02/skos/core#}broader"]
    topConcepts = []
    allconcepts = []
    #iterate over all elements of root
    for element in root.iter():
        if element.tag == "{http://www.w3.org/2004/02/skos/core#}Concept":
            uuid= element.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")
            element.set("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", uuid.replace(" ", "_"))
            allconcepts.append(uuid.replace(" ", "_"))

    for element in root.iter():
        if element.tag == "{http://www.w3.org/2004/02/skos/core#}Concept":
            uuid= element.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")
            for subElement in element.iter():
                if subElement.tag in skosList:
                    subElement.set("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource", subElement.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource").replace(" ", "_"))
                    if not scheme+"/" in subElement.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"):
                        wrongScheme = subElement.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource").split("/")[0]
                        # replace wrong scheme with correct scheme
                        subElement.set("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource", subElement.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource").replace(wrongScheme, scheme))
                        referenceConcept = subElement.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource")
                        if "�" in referenceConcept:
                            matchDistances = []
                            for concept in allconcepts:
                                    matchDistances.append(distance(referenceConcept, concept))
                            minDistance = min(matchDistances)
                            # get all indexes of the minimum distance in matchDistances
                            minDistanceIndexes = [i for i, x in enumerate(matchDistances) if x == minDistance]
                            if len(minDistanceIndexes) > 1:
                                print("Multiple matches found for concept: " + referenceConcept)
                                print ("Please choose the correct concept from the following list:")
                                for index in minDistanceIndexes:
                                    print(allconcepts[index])
                            elif len(minDistanceIndexes) == 1:
                                print("Match found for concept: " + referenceConcept)
                                print("Match: " + allconcepts[minDistanceIndexes[0]])  
                                subElement.set("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource", allconcepts[minDistanceIndexes[0]])
                            else:
                                print("No match found for concept: " + referenceConcept)
                if subElement.tag == "{http://www.w3.org/2004/02/skos/core#}inScheme":
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
    g = Graph()
    modifiedText = lxml.etree.tostring(root, encoding="utf-8").decode("utf-8")
    g.parse(data=modifiedText, format="xml", encoding="utf-8")
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