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

@app.route("/animeResults")
def anime_results_view():
    anime_name = request.args.get('search')
    page_num = request.args.get('page')
    query = '''
        query ($id: Int, $page: Int, $perPage: Int, $search: String) {
            Page (page: $page, perPage: $perPage) {
                pageInfo {
                    lastPage
                }
                media (id: $id, search: $search, type: ANIME) {
                    id
                    title {
                        romaji
                    }
                    coverImage{
                        medium
                    }
                }
            }
        }
    '''
    url = 'https://graphql.anilist.co'
    variables = {
        'search': anime_name,
        'page': page_num,
        'perPage': 5
    }

    response = requests.post(url, json={'query': query, 'variables': variables})
    json_data = json.loads(response.text)

    if 'errors' in json_data:
        messages = []
        for error in json_data['errors']:
            messages.append(error['message'])
    
        return render_template('error.html', title = 'Error', msgs  = messages)

    anime_list = json_data['data']['Page']['media']
    total_pages = json_data['data']['Page']['pageInfo']['lastPage']
    romaji_names = []
    url_list = []
    for anime in anime_list:
        romaji_names.append(anime['title']['romaji'])
        url_list.append(anime['coverImage']['medium'])
    return render_template('resultPage.html', titles = romaji_names, imgURLs = url_list, n = len(romaji_names), 
    currentPage = int(page_num), numPages = total_pages, name = anime_name)

if __name__ == "__main__":
    app.run(debug=True)