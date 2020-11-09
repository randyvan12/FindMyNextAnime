from flask import Flask, render_template, request, url_for
from string import Template
import requests
import json

app = Flask(__name__)

@app.route("/")
def home_view():
    return render_template('home.html', title="Home")

@app.route("/about")
def about_view():
    return render_template('about.html', title ="About")

@app.route("/animeInfo", methods=['POST'])
def anime_page_view():
    anime_name = request.form.get('search-bar')
    query = '''
        query ($id: Int, $page: Int, $perPage: Int, $search: String) {
            Page (page: $page, perPage: $perPage) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                    perPage
                }
                media (id: $id, search: $search, type: ANIME) {
                    id
                    title {
                        english
                    }
                    coverImage{
                        extraLarge
                    }
                }
            }
        }
    '''
    url = 'https://graphql.anilist.co'
    variables = {
        'search': anime_name,
        'page': 1,
        'perPage': 3
    }

    response = requests.post(url, json={'query': query, 'variables': variables})
    json_data = json.loads(response.text)

    if 'errors' in json_data:
        messages = []
        for error in json_data['errors']:
            messages.append(error['message'])
    
        return render_template('error.html', title = 'Error', msgs  = messages)

    anime_list = json_data['data']['Page']['media']

    english_names = []
    url_list = []
    for anime in anime_list:
        english_names.append(anime['title']['english'])
        url_list.append(anime['coverImage']['extraLarge'])
    return render_template('animePage.html', titles = english_names, imgURLs = url_list, n = len(english_names))

if __name__ == "__main__":
    app.run(debug=True)