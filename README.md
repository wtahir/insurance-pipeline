This project is about creating an end to end pipeline to extract and process insurance information. I am building it to get to know the challenges while using latest state of the art tech.

## The pipeline consists of the following steps:
 
1. Ingestion: This takes the pdfs as input and performs processing to convert data in structured format for the next steps. It creates jsons with text stored as a dict and additional keys for useful information.

2. Extraction: Takes the jsons created in step 1 and extracts information such as claim number, document type etc.

3. Chunking: Now that the data has the useful information in json format, chunking step chunks it into a fixed chunk size of 800 with minimum chunk size of 100. There is also a document threshold of 600 so that any document having less text should have a single chunk. Meanwhile the chunk size of 100 to avoid short less meaningful chunks. Chunking is done based on sentences with overlapping of few words and making sure that words dont split between chunks. It also contains meta data which is required to retrieve relevant chunks

4. Embedding: Converts chunking results into vectors and stores those in ChromaDB along with its metadata for retrieval in the later stage. Since the language is non English but the query is in English. The model used for embedding is capable of handling multiple languages.

5. Retrieval: Retrieve relevant chunks from Chroma based on user querry. Then generates an answer using GPT-4o using the context of the retrieved chunks.

6. Evaluation: Evaluate the relevancy of the chunks retrieved and generated answer

## What I learned:

I hit some bugs while creating this pipeline. I found out that because of the overlap calculation used, the character positions could land mid-word, so I added a word boundary search using text.find(' ') after calculating the new start position. There was an issue in formating prompt using .format method. Its simpler and bug free to keep prompt as it is and use it later on by calling it directly in a method. I also experienced the token limitation error which can happen if the LLM call generates an answer needing more tokens than the defined limit.
