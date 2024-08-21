import os
from neo4j import GraphDatabase

#Dependency needed for langchain to write to Neo4j with pre-existing langchain tools
from langchain_community.graphs import Neo4jGraph

#Dependencies for splitting text into chunks and mapping content to specified nodes and relationships
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain.text_splitter import TokenTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain.prompts.prompt import PromptTemplate

#Specifying paths
os.environ["OPENAI_API_KEY"] = "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"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"

#Initialising the graph object
graph = Neo4jGraph()


llm = ChatOpenAI(temperature=0, model_name="gpt-4")

llm_transformer = LLMGraphTransformer(
    llm=llm,
    prompt = PromptTemplate.from_template("""
                                          
                                          """),
    allowed_nodes=["Contributer", "Document", "Organization", "Skill", "Application", "Tool", "Project"],
    allowed_relationships=["AUTHOR_OF", "HAS_SKILL", "WORKED_FOR_ORGANIZATION", "WORKED_FOR_PROJECT"]
    )


documents = [Document(page_content=text)]
text_splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=24)
results = text_splitter.split_documents(documents)
graph_documents = llm_transformer.convert_to_graph_documents(results)
print(f"Nodes:{graph_documents[0].nodes}")
print(f"Relationships:{graph_documents[0].relationships}")

