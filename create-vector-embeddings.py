# export OPENAI_API_KEY="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"
from neo4j import GraphDatabase, exceptions
from openai import OpenAI
import time
client = OpenAI()

# Query to get articles and their content
def unit_of_work_for_getting_chunks(tx):
    result = tx.run("MATCH(ch:Chunk)-[]-(c:Content) WHERE ch.embedding IS NULL RETURN ch.content as content, c.articleName as articleName")
    return result.values("content", "articleName")

# Main function to create chunks out of the article content
def main(driver, csv_file_path):
    with driver.session() as session:
        chunks = session.execute_read(unit_of_work_for_getting_chunks)
        
        # For each chunk node retrieved
        for chunk in chunks:
            attempt = 0
            max_attempts = 5
            backoff_time = 5
            while attempt < max_attempts:
                try:
                    # Defining content
                    content = chunk[0]
                    articleName = chunk[1]
                    # Sending article content to get chunked
                    function_with_prompt(driver, content, articleName)
                    break
                except exceptions.ServiceUnavailable as e:
                    attempt += 1
                    print(f"Attempt {attempt} failed with error: {str(e)}. Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)

            if attempt >= max_attempts:
                print("Max retries reached. Exiting.")
                raise e
            
# Transaction query - Writes chunks to the database
def unit_of_work_for_creating_chunk(tx, embedding, content):
    tx.run("""
           
           MATCH(ch:Chunk{content: $content})
           WITH ch
           CALL db.create.setNodeVectorProperty(ch, 'embedding', $embedding)
           """
            , embedding = embedding, content = content)
      
# Function to create chunks out of the article content
def function_with_prompt(driver, content, articleName):
    model="text-embedding-ada-002"
    embedding = client.embeddings.create(input = [content], model=model).data[0].embedding
    with driver.session() as session:
        session.execute_write(unit_of_work_for_creating_chunk, embedding, content)
    print('Embedding completed for chunks on document:', articleName)
    
if __name__ == "__main__":
    print("Starting the process")
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "password"
    driver = GraphDatabase.driver(uri, auth=(user, password), max_connection_lifetime=200)
    csv_file_path = "/Users/c02f41k7md6r/Documents/team_chatbot/graph-construction/general_taxonomies.csv"
    main(driver, csv_file_path)
    driver.close()