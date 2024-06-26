from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId

import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)

@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template('index.html',words=words, msg=msg)

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = '94cbb6f1-8277-4f59-ad6c-3cf3e5ca6d9d'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}';
    response = requests.get(url)
    definitions = response.json()

    if not definitions:
        return render_template('error.html', words=keyword)
    
    if type(definitions[0]) is str:
        suggestions = get_suggestions(keyword)
        return render_template('error.html', words=keyword, suggestions=suggestions)

    status = request.args.get('status_give', 'new')
    return render_template("detail.html", word=keyword, definitions=definitions, status=status)

def get_suggestions(keyword):
    api_key = 'd25c522e-0386-426e-b3e4-9a275531173e'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    suggestions = []
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and isinstance(data[0], str):
            suggestions = data
    return suggestions

@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y%m%d'),
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })

from flask import request

@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    # Menghapus semua contoh yang terkait dengan kata yang akan dihapus
    db.examples.delete_many({'word': word})
    # Menghapus kata itu sendiri
    db.words.delete_one({'word': word})
    return jsonify({'result': 'success', 'msg': 'word and related examples deleted'})


@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word': word})
    examples = []
    for example in example_data:
        examples.append({
            'example': example.get('example'),
            'id': str(example.get('_id')),
        })
    return jsonify({'result': 'success', 'examples': examples})

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word': word,
        'example': example
    }
    db.examples.insert_one(doc)
    return jsonify({'result': 'success'})

@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({'result': 'success', 'msg': f'example {word} deleted successfully'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)