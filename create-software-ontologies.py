# export OPENAI_API_KEY="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"
import csv
from openai import OpenAI
from neo4j import GraphDatabase, exceptions
from langchain.text_splitter import TokenTextSplitter
from langchain_core.documents import Document
import time

client = OpenAI()

def unit_of_work_for_getting_articles(tx):
    result = tx.run("MATCH(a:Article)-[]-(c:Content) WHERE a.softwareCompleted IS NULL RETURN a.name as name, c.content as content")
    return result.values("name", "content")

# Function to query Neo4j and process results
def main(driver, csv_file_path):
    with driver.session() as session:
        result = session.execute_read(unit_of_work_for_getting_articles)
        
        for record in result:
            print("Starting entity resolution for "+record[0])
            attempt = 0
            max_attempts = 100
            backoff_time = 5
            while attempt < max_attempts:
                try:
                    document = record[1]
                    documentName = record[0]
                    function_with_prompt(driver, documentName, csv_file_path, document)
                    break
                except exceptions.ServiceUnavailable as e:
                    attempt += 1
                    print(f"Attempt {attempt} failed with error: {str(e)}. Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)

            if attempt >= max_attempts:
                print("Max retries reached. Exiting.")
                raise e
            
def unit_of_work_for_setting_article_ontology_as_complete(tx, articleName):
    tx.run("""
            MATCH (a:Article {name: $articleName})
            SET a.softwareCompleted = true
            """, articleName=articleName)
      
def openai_call(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You are an assistant helping to identify labels for the document which will be applied to an ontology. If the response to the question is yes, please response in the format 'yes'. 'no' if otherwise. You may be asked multiple questions. Please give yes or no answers in the same order as the questions."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content          
                
def function_with_prompt(driver, documentName, csv_file_path, document):
    text_splitter = TokenTextSplitter(chunk_size=12000, chunk_overlap=4000)
    doc =  Document(page_content=document)
    results = text_splitter.split_documents([doc])
    for result in results:
        with open(csv_file_path, mode='r', newline='') as file:
            reader = csv.reader(file)
            header = next(reader)
            for row in reader:
                user_prompt = f"In summary of what the document: '{result}' with document title: '{documentName}' is about, could the software label '{row[2]}' potentially directly apply to the document where the definition of the label is '{row[5]}'?. You can only answer with 'yes' pr 'no'. Response must be lowercase and should not include comment or punctuation."
                response = openai_call(user_prompt)
                if response == "yes":
                    print(f"Adding {row[2]} to the software ontology of '{documentName}'")
                    db_write_ontologies(driver, documentName, row[2])
                    
    with driver.session() as session:
        session.execute_write(unit_of_work_for_setting_article_ontology_as_complete, documentName)
    print('Entity resolution completed for document:', documentName)
        
def unit_of_work_write_ontologies(tx, articleName, softwareName):
    tx.run("""MERGE (a:Article {name: $articleName})
                                MERGE (sw:Software {name: $softwareName})
                                MERGE (a)-[r:REFERS_TO_SOFTWARE]->(sw)"""
                                , articleName=articleName, softwareName=softwareName
                                )
def db_write_ontologies(driver, articleName, softwareName):
    with driver.session() as session:
        session.execute_write(unit_of_work_write_ontologies, articleName, softwareName)
    

if __name__ == "__main__":
    print("Starting the process")
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "password"
    driver = GraphDatabase.driver(uri, auth=(user, password), max_connection_lifetime=200)
    csv_file_path = "/Users/c02f41k7md6r/Documents/team_chatbot/graph-construction/software-taxonomies.csv"
    main(driver, csv_file_path)
    driver.close()