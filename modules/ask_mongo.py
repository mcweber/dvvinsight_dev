# ---------------------------------------------------
# Version: 11.03.2025
# Author: M. Weber
# ---------------------------------------------------
# ---------------------------------------------------

from datetime import datetime
import os
from dotenv import load_dotenv

import modules.ask_llm as ask_llm

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

import torch
from transformers import BertTokenizer, BertModel

from modules.ask_mongo_prompts import (
    WRITE_SUMMARY_TASK,
    WRITE_SUMMARY_SYSTEM_PROMPT,
    WRITE_TAKEAWAYS_TASK,
    WRITE_TAKEAWAYS_SYSTEM_PROMPT,
    CREATE_KEYWORDS_TASK,
    CREATE_KEYWORDS_SYSTEM_PROMPT,
    CREATE_ENTITIES_TASK,
    CREATE_ENTITIES_SYSTEM_PROMPT,
    GENERATE_QUERY_TASK
    )

# Init LLM ----------------------------------
llm = ask_llm.LLMHandler(llm="gpt-4o", local=False)
# llm = ask_llm.LLMHandler(llm="llama3", local=True)

# Init MongoDB Client ----------------------------------
load_dotenv()
mongoClient = MongoClient(os.environ.get('MONGO_URI_DVV'))
database = mongoClient.dvv_content_pool
collection = database.dvv_artikel
collection_config = database.config

# Init pre-trained model and tokenizer ------------------
os.environ["TOKENIZERS_PARALLELISM"] = "false"
model_name = "bert-base-german-cased" # 768 dimensions
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)


# Define Summary & Takeaways ----------------------------------
def generate_abstracts(input_field: str, output_field: str, max_iterations: int = 20) -> None:
    cursor = collection.find({output_field: ""}).limit(max_iterations)
    cursor_list = list(cursor)
    for record in cursor_list:
        abstract = write_summary(str(record[input_field]))
        print(record['titel'][:50])
        print("-"*50)
        collection.update_one({"_id": record.get('_id')}, {"$set": {output_field: abstract}})
    cursor.close()

def write_summary(text: str = "", length: int = 500) -> str:
    if text:
        return llm.ask_llm(
            temperature=0.1,
            question=WRITE_SUMMARY_TASK,
            system_prompt=WRITE_SUMMARY_SYSTEM_PROMPT.format(length=length),
            db_results_str=text
            )
    else:
        return ""
    
def write_takeaways(text: str = "", max_takeaways: int = 5) -> str:
    if text:
        return llm.ask_llm(
            temperature=0.1, 
            question=WRITE_TAKEAWAYS_TASK.format(max_takeaways=max_takeaways), 
            system_prompt=WRITE_TAKEAWAYS_SYSTEM_PROMPT, 
            db_results_str=text)
    else:
        return ""


# Embeddings -------------------------------------------------            
def generate_embeddings(input_field: str, output_field: str, 
                        max_iterations: int = 10) -> None:
    cursor = collection.find({output_field: []}).limit(max_iterations)
    cursor_list = list(cursor)
    for record in cursor_list:
        article_text = record[input_field]
        if article_text:
            embeddings = create_embeddings(text=article_text)
            collection.update_one({"_id": record['_id']}, {"$set": {output_field: embeddings}})
        else:
            article_text = "Fehler: Kein Text vorhanden."
    print(f"\nGenerated embeddings for {max_iterations} records.")

def create_embeddings(text: str) -> list:
    encoded_input = tokenizer(text, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        model_output = model(**encoded_input)
    return model_output.last_hidden_state.mean(dim=1).squeeze().tolist()


# Keywords ---------------------------------------------------
def generate_keywords(input_field: str, output_field: str, max_iterations: int = 10) -> None:
    print(f"Start: {input_field}|{output_field}")
    print(collection)
    cursor = collection.find({output_field: []}).limit(max_iterations)
    if cursor:
        print("MongoDB Suche abgeschlossen.")
        cursor_list = list(cursor)
        print(f"Anzahl Records: {len(cursor_list)}")
        for record in cursor_list:
            if record[input_field] == "":
                print("Kein Input-Text.")
                continue
            article_text = record.get(input_field, "Fehler: Kein Text vorhanden.")
            keywords = create_keywords(text=article_text)
            collection.update_one({"_id": record['_id']}, {"$set": {output_field: keywords}})
            print(keywords)
        print(f"\nGenerated keywords for {len(cursor_list)} records.")
    else:
        print("No articles without summary found.")
    cursor.close()

def create_keywords(text: str = "", max_keywords: int = 5) -> list:
    if text:
        keywords_str = llm.ask_llm(
            temperature=0.1, 
            question=CREATE_KEYWORDS_TASK.format(max_keywords=max_keywords), 
            system_prompt=CREATE_KEYWORDS_SYSTEM_PROMPT, 
            db_results_str=text
            )
        keywords_list = [keyword.strip() for keyword in keywords_str.split(',') if keyword.strip()]
        return keywords_list
    else:
        return []

def list_keywords() -> list:
    pipeline = [
    {'$unwind': '$schlagworte'},
    {'$group': {
        '_id': '$schlagworte', 
        'count': {'$sum': 1}
        }
        },
    {'$sort': {'count': -1}},
    {'$project': {
        '_id': 0, 
        'keyword': '$_id', 
        'count': 1
        }
        }
    ]
    cursor_list = list(collection.aggregate(pipeline))
    return cursor_list


# Entities (Personen und Firmen) --------------------------------
def generate_entities(input_field: str = "", output_field: str = "", max_iterations: int = 10) -> None:
    print(f"Start: {input_field}|{output_field}")
    cursor = collection.find({output_field: []}).limit(max_iterations)
    print(f"MongoDB Suche abgeschlossen.")
    cursor_list = list(cursor)
    print(f"Anzahl Records: {len(cursor_list)}")
    for record in cursor_list:
        # article_text = record.get(input_field, "Fehler: Kein Text vorhanden.")
        entities = create_entities(text=record[input_field])
        # collection.update_one({"_id": record['_id']}, {"$set": {output_field: keywords}})
        print(f"{record['_id']}|{record[input_field][:50]}: {entities}")
    print(f"\nGenerated entities for {len(cursor_list)} records.")

def create_entities(text: str = "") -> list:
    if not text:
        entities_str = llm.ask_llm(
            temperature=0.1, 
            question=CREATE_ENTITIES_TASK, 
            system_prompt=CREATE_ENTITIES_SYSTEM_PROMPT, 
            db_results_str=text
            )
        entities_list = [entity.strip() for entity in entities_str.split(',') if entity.strip()]
        return entities_list
    else:
        return []


# Query & Filter ------------------------------------------------
def generate_query(question: str = "") -> str:
    return llm.ask_llm(temperature=0.1, question=GENERATE_QUERY_TASK.format(question=question)) 
    
def generate_filter(filter: list, field: str) -> dict:
    return {field: {"$in": filter}} if filter else {}

# Search ------------------------------------------------
def text_search(search_text: str="*", gen_suchworte: bool=False, sort: str="score", score: float=0.0, filter: list=[], limit: int=10) -> list[list, str]:
    
    if not search_text:
        return [], ""
    
    if search_text == "*":
        suchworte = "*"
        score = 0.0
        query = {
            "index": "volltext_gewichtet",
            "exists": {"path": "text"},
        }
    
    else:
        if (gen_suchworte and len(search_text) > 30):
            suchworte = generate_query(question=search_text)
        else:
            suchworte = search_text
        query = {
            "index": "volltext_gewichtet",
            "text": {
                "query": suchworte,
                "path": {"wildcard": "*"}
            }
        }
    
    fields = {
        "_id": 1,
        "quelle_id": 1,
        "jahrgang": 1,
        "nummer": 1,
        "titel": 1,
        "datum": 1,
        "date": 1,
        "untertitel": 1,
        "text": 1,
        "ki_abstract": 1,
        "score": {"$meta": "searchScore"},
    }
    pipeline = [
        {"$search": query},
        {"$project": fields},
        {"$match": {"score": {"$gte": score}}},
        {"$sort": {sort: -1}},
        {"$limit": limit},
    ]
    if filter:
        pipeline.insert(1, {"$match": {"quelle_id": {"$in": filter}}})

    cursor = collection.aggregate(pipeline)
    return list(cursor), suchworte


def vector_search(query_string: str = "*", gen_suchworte: bool = False, score: float = 0.0, filter : list = [], sort: str = "score", limit: int = 10) -> list[list, str]:
    
    suchworte = generate_query(question=query_string) if gen_suchworte else query_string
    embeddings_query = create_embeddings(text=suchworte)
    query = {
            "index": "vector_index",
            "path": "text_embeddings",
            "queryVector": embeddings_query,
            "numCandidates": int(limit * 10),
            "limit": limit,
            }
    fields = {
            "_id": 1,
            "quelle_id": 1,
            "jahrgang": 1,
            "nummer": 1,
            "titel": 1,
            "datum": 1,
            "untertitel": 1,
            "text": 1,
            "ki_abstract": 1,
            "date": 1,
            "score": {"$meta": "vectorSearchScore"}
            }
    pipeline = [
        {"$vectorSearch": query},
        {"$project": fields},
        {"$match": {"quelle_id": {"$in": filter}}},
        {"$match": {"score": {"$gte": score}}},  # Move this up
        {"$sort": {sort: -1}},
        {"$limit": limit},  # Add this stage
    ]
    return collection.aggregate(pipeline), suchworte


# Div ------------------------------------------------

def collect_ausgaben(quelle:str, jahrgang:int, ausgabe:int) -> list:
    cursor = collection.find(
        {'$and': [
            {'quelle_id': quelle},
            {'jahrgang': jahrgang},
            {'nummer': ausgabe}
            ]
        }
        ).sort('seite_start', 1)
    return list(cursor)


def group_by_field() -> dict:
    pipeline = [
            {   
            '$group': {
                '_id': '$quelle_id', 
                'count': {
                    '$sum': 1
                    }
                }
            }, {
            '$sort': {
                'count': -1
                }
            }
            ]
    result = collection.aggregate(pipeline)
    # transfor into dict
    return_dict = {}
    for item in result:
        return_dict[item['_id']] = item['count']
    return return_dict

def list_fields() -> dict:
    result = collection.find_one()
    return result.keys()

def get_document(id: str) -> dict:
    document = collection.find_one({"id": id})
    return document

def get_system_prompt() -> str:
    result = collection_config.find_one({"key": "systemprompt"})
    return str(result["content"])
    
def update_system_prompt(text: str = ""):
    result = collection_config.update_one({"key": "systemprompt"}, {"$set": {"content": text}})
