from flask import Flask, redirect
from string import Template
import requests
import json
app = Flask(__name__)

STATIC_DISPLAY_TEMPLATE = Template("""
<h1> ${romaji}</h1>
<img src=${imgURL}>
""")

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/<anime_name>")
def anime_search(anime_name):
    query = '''
    query ($anime_name: String) { # Define which variables will be used in the query (id)
    Media (search: $anime_name, type: ANIME) { # Insert our variables into the query arguments (id) (type: ANIME is hard-coded in the query)
    id
    title {
    romaji
    english
    native
    }
    coverImage{
        extraLarge
    }
    }
    }
    '''
    url = 'https://graphql.anilist.co'
    variables = {
    'anime_name': anime_name
    }

    response = requests.post(url, json={'query': query, 'variables': variables})
    json_data = json.loads(response.text)
    romaji = json_data['data']['Media']['title']['romaji']
    imageURL = json_data['data']['Media']['coverImage']['extraLarge']
    return (STATIC_DISPLAY_TEMPLATE.substitute(romaji = romaji, imgURL = imageURL))