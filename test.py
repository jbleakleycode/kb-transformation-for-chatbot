import pandas as pd
from openai import OpenAI

# client = OpenAI

# def openai_call(prompt):
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo-0125",
#         messages=[
#             {"role": "system", "content": "You are an assistant helping to identify labels for the document which will be applied to an ontology. You will be provided the document and list of labels as well as the ontology they belong to. Please provide the response in the format 'label1, label2, label3' etc where label1, label2 and label3 DO apply to the document. Labels must have same spelling, spacing and casing as what it provided since clean data is necessary for querying later on. Do not give any extra explaination or content in the response."},
#             {"role": "user", "content": prompt}
#         ]
#     )
#     return response.choices[0].message.content 

import pandas as pd

def getOntologyStrings():
    # Read the CSV file
    df = pd.read_csv("/Users/c02f41k7md6r/Documents/team_chatbot/graph-construction/top-level-taxonomies.csv")
    
    # Extract the column with ontologies
    team_ontologies = df['Team'].dropna().tolist()
    content_distribution_ontologies = df['Content Distribution'].dropna().tolist()
    industry_ontologies = df['Industry'].dropna().tolist()
    use_case_ontologies = df['Use-Case'].dropna().tolist()
    content_maturity_ontologies = df['Content Maturity'].dropna().tolist()
    content_type_ontologies = df['Content Type'].dropna().tolist()
    editions_ontologies = df['Editions'].dropna().tolist()
    
    # Convert the list to a string
    team_string = "Team: " + ", ".join(team_ontologies) + " END"
    cd_string = "Content Distribution: " + ", ".join(content_distribution_ontologies) + " END"
    industry_string = "Industry: " + ", ".join(industry_ontologies) + " END"
    use_case_string = "Use-Case: " + ", ".join(use_case_ontologies) + " END"
    cm_string = "Content Maturity: " + ", ".join(content_maturity_ontologies) + " END"
    ct_string = "Content Type: " + ", ".join(content_type_ontologies) + " END"
    editions_string = "Editions: " + ", ".join(editions_ontologies) + " END"
    
    return team_string, cd_string, industry_string, use_case_string, cm_string, ct_string, editions_string

if __name__ == "__main__":
    strings = getOntologyStrings()
    for string in strings:
        print(string + "\n")

