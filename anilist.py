from flask import Flask, render_template, request, url_for, redirect, session
from string import Template
from authlib.integrations.flask_client import OAuth
import requests
import json

# for auth
from datetime import timedelta
from auth_decorator import login_required

# the app
app = Flask(__name__)
# Session config
app.secret_key = "739b8f5167d69c5ded99a055d73c52ac"
app.config['SESSION_COOKIE_NAME'] = 'anilist-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

# Auth setup
oauth = OAuth(app)
anilist = oauth.register(
    name='anilist',
    client_id='4320',
    client_secret='PvdcI16xxNlq11QVR7F1ZA0ykH66rPyhJA8VcR4h',
    access_token_url='https://anilist.co/api/v2/oauth/token',
    access_token_params=None,
    authorize_url='https://anilist.co/api/v2/oauth/authorize',
    authorize_params=None,
    api_base_url='https://anilist.co/api/v2/oauth/',
)

# Start webpage


@app.route("/")
def home_view():
    return render_template('home.html', title="Home", login=dict(session).get('access_token', None))

# About webpage


@app.route("/about")
def about_view():
    return render_template('about.html', title="About", login=dict(session).get('access_token', None))


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

    response = requests.post(
        url, json={'query': query, 'variables': variables})
    json_data = json.loads(response.text)

    if 'errors' in json_data:
        messages = []
        for error in json_data['errors']:
            messages.append(error['message'])

        return render_template('error.html', title='Error', msgs=messages)

    anime_list = json_data['data']['Page']['media']
    total_pages = json_data['data']['Page']['pageInfo']['lastPage']
    romaji_names = []
    url_list = []
    for anime in anime_list:
        romaji_names.append(anime['title']['romaji'])
        url_list.append(anime['coverImage']['medium'])
    return render_template('resultPage.html', titles=romaji_names, imgURLs=url_list, n=len(romaji_names),
                           currentPage=int(page_num), numPages=total_pages, name=anime_name, login=dict(session).get('access_token', None))


@app.route('/anime')
def anime_view():
    anime_name = request.args.get("anime_name")
    query = '''
    query ($search: String) {
        Media (search: $search, type: ANIME) {
            coverImage{
                large
            }
        }
    }
    '''

    variables = {
        'search': anime_name
    }
    url = 'https://graphql.anilist.co'
    response = requests.post(
        url, json={'query': query, 'variables': variables}).json()
    imgURL = response['data']['Media']['coverImage']['large']
    return render_template('anime.html', name=anime_name, imgURL=imgURL, login=dict(session).get('access_token', None))

# login webpage


@app.route('/login')
def login():
    anilist = oauth.create_client('anilist')
    redirect_uri = url_for('authorize', _external=True)
    return anilist.authorize_redirect(redirect_uri)

# safe redirect to authorize then redirects to another page


@app.route('/authorize')
def authorize():
    anilist = oauth.create_client('anilist')
    token = anilist.authorize_access_token()

    session['access_token'] = token['access_token']
    session.permanent = True
    return redirect('/user')

# gets rid of the session cookie


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/user')

# user webpage


@app.route("/user")
@login_required
def user_view():
    url = "https://graphql.anilist.co"
    accessToken = session['access_token']

    headers = {
        "Authorization": f"Bearer {accessToken}"
    }

    query = '''
    query{
        Viewer{
            name
            avatar{
                large
            }
        }
    }
    '''
    response = requests.post(url, headers=headers, json={
                             "query": query}).json()
    username = response['data']['Viewer']['name']
    imageURL = response['data']['Viewer']['avatar']['large']
    return render_template('user.html', username=username, imgURL=imageURL, login=dict(session).get('access_token', None))


if __name__ == "__main__":
    app.run(debug=True)
