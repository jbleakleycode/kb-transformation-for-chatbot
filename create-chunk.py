# Need to create property 'hasBeenChunked

import csv
from openai import OpenAI
from neo4j import GraphDatabase, exceptions
from langchain.text_splitter import TokenTextSplitter
from langchain_core.documents import Document
import time

# Query to get articles and their content
def unit_of_work_for_getting_articles(tx):
    result = tx.run("MATCH(a:Article)-[]-(c:Content) RETURN a.name as name, c.content as content")
    return result.values("name", "content")

# Main function to create chunks out of the article content
def main(driver, csv_file_path):
    with driver.session() as session:
        result = session.execute_read(unit_of_work_for_getting_articles)
        
        # For each article node retrieved
        for record in result:
            print(record[0])
            attempt = 0
            max_attempts = 5
            backoff_time = 5
            while attempt < max_attempts:
                try:
                    # Defining content and article name
                    document = record[1]
                    documentName = record[0]
                    # Sending article content to get chunked
                    function_with_prompt(driver, documentName, csv_file_path, document)
                    break
                except exceptions.ServiceUnavailable as e:
                    attempt += 1
                    print(f"Attempt {attempt} failed with error: {str(e)}. Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)

            if attempt >= max_attempts:
                print("Max retries reached. Exiting.")
                raise e

# Transaction query - Writes chunks to the database
def unit_of_work_for_creating_chunk(tx, result, documentName):
    tx.run("""
           MATCH(a:Content{articleName: $articleName})
           WITH a
           MERGE(ch:Chunk{content: $result})
           WITH ch, a
           MERGE (ch)<-[:HAS_CHUNK]-(a);
           
           """
            , articleName = documentName, result = result)
      
# Function to create chunks out of the article content
def function_with_prompt(driver, documentName, csv_file_path, document):
    text_splitter = TokenTextSplitter(chunk_size=4000, chunk_overlap=2000)
    print('Splitting document with name:', documentName)
    doc =  Document(page_content=document)
    results = text_splitter.split_documents([doc])
    for result in results:
        with driver.session() as session:
            session.execute_write(unit_of_work_for_creating_chunk, result.page_content, documentName)
    print('Chunking completed for document:', documentName)
    

if __name__ == "__main__":
    print("Starting the process")
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "password"
    driver = GraphDatabase.driver(uri, auth=(user, password), max_connection_lifetime=200)
    csv_file_path = "/Users/c02f41k7md6r/Documents/team_chatbot/graph-construction/general_taxonomies.csv"
    main(driver, csv_file_path)
    driver.close()