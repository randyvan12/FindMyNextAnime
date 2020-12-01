from flask import Flask, render_template, request, url_for, redirect, session
from string import Template
from authlib.integrations.flask_client import OAuth
import requests
import json
import random

# for videos
import urllib.request
import re

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

        return render_template('error.html', title='Error', msgs=messages, login=dict(session).get('access_token', None))

    anime_list = json_data['data']['Page']['media']
    total_pages = json_data['data']['Page']['pageInfo']['lastPage']
    romaji_names = []
    url_list = []
    id_list = []
    for anime in anime_list:
        romaji_names.append(anime['title']['romaji'])
        url_list.append(anime['coverImage']['medium'])
        id_list.append(anime['id'])
    return render_template('resultPage.html', titles=romaji_names, imgURLs=url_list, n=len(romaji_names),
                           currentPage=int(page_num), numPages=total_pages, name=anime_name, ids = id_list, login=dict(session).get('access_token', None))


@app.route('/anime')
def anime_view():
    anime_id = request.args.get("anime_id")
    user_id = None
    if dict(session).get('access_token', None):
        user_id = session['userID']
        query = '''
        query ($id: Int, $userId: Int, $page: Int, $perPage: Int) {
            Media (id: $id, type: ANIME) {
                title{
                    romaji
                    english
                }
                coverImage{
                    large
                }
                startDate{
                    year
                    month
                    day
                }
                endDate{
                    year
                    month
                    day
                }
                studios(isMain: true){
                    nodes{
                        name
                    }
                }
                characters(role: MAIN, page: $page, perPage: $perPage){
                    nodes{
                        name{
                            full
                        }
                        image{
                            medium
                        }
                    }
                }
                idMal
                id
                episodes
                averageScore
                description
                genres
                format
                status
                season
                source
            }
            MediaListCollection(userId: $userId, type: ANIME status_in: [COMPLETED, CURRENT, DROPPED, PLANNING, PAUSED]){
                lists{
                    entries{
                        media{
                            id
                        }
                        status
                        mediaId
                    }
                }
            }
        }
        '''
    else:
        query = '''
        query ($id: Int, $page: Int, $perPage: Int) {
            Media (id: $id, type: ANIME) {
                title{
                    romaji
                    english
                }
                coverImage{
                    large
                }
                startDate{
                    year
                    month
                    day
                }
                endDate{
                    year
                    month
                    day
                }
                studios(isMain: true){
                    nodes{
                        name
                    }
                }
                characters(role: MAIN, page: $page, perPage: $perPage){
                    nodes{
                        name{
                            full
                        }
                        image{
                            medium
                        }
                    }
                }
                idMal
                id
                episodes
                averageScore
                description
                genres
                format
                status
                season
                source
            }
        }
        '''
    variables = {
        'id': anime_id,
        'userId': user_id,
        'page': 1,
        'perPage': 4
    }

    url = 'https://graphql.anilist.co'

    response = requests.post(
        url, json={'query': query, 'variables': variables}).json()
    #retrieval of information for the first column
    anime_info = {}
    response_data = response['data']['Media']

    anime_info['img_URL'] = response_data['coverImage']['large']
    anime_info['romaji'] = response_data['title']['romaji']
    anime_info['english'] = response_data['title']['english']
    anime_info['start_date'] = str(response_data['startDate']['month']) + '/' + str(response_data['startDate']['day']) + '/' + str(response_data['startDate']['year'])
    anime_info['end_date'] = str(response_data['endDate']['month']) + '/' + str(response_data['endDate']['day']) + '/' + str(response_data['endDate']['year'])
    anime_info['episodes'] = response_data['episodes']
    anime_info['score'] = response_data['averageScore']
    anime_info['studio'] = response_data['studios']['nodes'][0]['name']
    anime_info['description'] = response_data['description']
    anime_info['id'] = response_data['id']
    anime_info['genres'] = response_data['genres']
    anime_info['format'] = response_data['format']
    anime_info['status'] = response_data['status'].title()
    anime_info['season'] = response_data['season'].title() + ' ' + str(response_data['startDate']['year'])
    anime_info['source'] = response_data['source'].title()

    # NEED TO FIX IF THE QUERY RETURNS NULL ON DICTONARY KEYS
    # THIS IS AN EXAMPLE BUT DOES NOT FIX ALL
    # for key in anime_info.keys():
    #     if anime_info[key] is None:
    #         anime_info[key] = 'Missing'

    #Checks if the anime is in your list and sets the drop down accordingly
    inList = False
    if dict(session).get('access_token', None):
        anime_list = []
        for item in response['data']['MediaListCollection']['lists']:
            anime_list += item['entries']
        for anime in anime_list:
            if anime['media']['id'] == anime_info['id']:
                inList = True
                anime_info['status'] = anime['status']
                break

    #if anime is in list then we change the drop down options    
    if inList:
        media_query = '''
            query($id: Int, $mediaId: Int){
                MediaList(userId: $id, mediaId: $mediaId){
                    id
                }
            }
        '''
        variables = {
            'id': session['userID'],
            'mediaId': anime_info['id']
        }
        response = requests.post(url, json={'query': media_query, 'variables': variables}).json()
        anime_info['media_list_id'] = response['data']['MediaList']['id']
    
    #Gets the OP/ED videos for the second column

    op_search_keyword = "official+" + anime_info['english'].replace(" ", "+") + "+opening"
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + op_search_keyword)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    anime_info['OP'] = "https://www.youtube.com/embed/" + video_ids[0]

    ed_search_keyword = "official+" +anime_info['english'].replace(" ", "+") + "+ending"
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + ed_search_keyword)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    anime_info['ED'] = "https://www.youtube.com/embed/" + video_ids[0]

    #Gets actors and character for the third column
    character_images = []
    character_names = []
    for characters in response_data['characters']['nodes']:
        character_names.append(characters['name']['full'])
        character_images.append(characters['image']['medium'])
    anime_info['character_names'] = character_names
    anime_info['character_images'] = character_images

    return render_template('anime.html', anime_info = anime_info, inList = inList, login=dict(session).get('access_token', None))

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
    return redirect('/')

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
            id
            about
        }
    }
    '''
    response = requests.post(url, headers=headers, json={"query": query}).json()
    response_data = response['data']['Viewer']
    #add to session cookie
    session['userID'] = response_data['id']
    session['username'] = response_data['name']

    #gets information about the user from the query
    user_info = {}
    user_info['username'] = response_data['name']
    user_info['img_URL'] = response_data['avatar']['large']
    user_info['about'] = response_data['about']
    
    #second query to get list
    query = '''
    query($id: Int){
        MediaListCollection(userId: $id, type: ANIME, status_in: [COMPLETED, CURRENT, PLANNING, DROPPED, PAUSED]){
            lists{
                entries{
                    media{
                        title{
                            romaji
                        }
                        coverImage{
                            medium
                        }
                        id
                    }
                    score(format: POINT_10)
                }
            }
        }
    }
    '''
    variables = {
        'id': session['userID']
    }
    response = requests.post(url, json={'query': query, 'variables': variables}).json()

    list_info = []
    for i in range(len(response['data']['MediaListCollection']['lists'])):
        anime_list = response['data']['MediaListCollection']['lists'][i]['entries']

        anime_info = {}
        for anime in anime_list:
            #ANIME NAME = (SCORE, IMAGE, ID)
            anime_info[anime['media']['title']['romaji']] = (anime['score'], anime['media']['coverImage']['medium'], anime['media']['id'])
        list_info.append(dict(sorted(anime_info.items(), key=lambda item: item[1], reverse=True)))
    #COMPELTED = 0, PLANNING = 1, DROPPED = 2, HOLD = 3, DROPPED = 4
    return render_template('user.html', user_info = user_info, list_info = list_info, login=dict(session).get('access_token', None))

@app.route("/random")
def random_anime():
    anime_info = {}
    while True:
        randint = random.randint(0, 100000)
        query = '''
        query ($id: Int) {
            Media (id: $id, type: ANIME) {
                title{
                    romaji
                    english
                }
                coverImage{
                    large
                }
                startDate{
                    year
                    month
                    day
                }
                endDate{
                    year
                    month
                    day
                }
                studios(isMain: true){
                    nodes{
                        name
                    }
                }
                episodes
                averageScore
            }
        }
        '''
        variables = {
            'id': randint
        }
        url = 'https://graphql.anilist.co'

        response = requests.post(url, json={'query': query, 'variables': variables}).json()
        try:
            response_data = response['data']['Media']
            anime_info['img_URL'] = response_data['coverImage']['large']
            anime_info['romaji'] = response_data['title']['romaji']
            anime_info['english'] = response_data['title']['english']
            anime_info['start_date'] = str(response_data['startDate']['month']) + '/' + str(response_data['startDate']['day']) + '/' + str(response_data['startDate']['year'])
            anime_info['end_date'] = str(response_data['endDate']['month']) + '/' + str(response_data['endDate']['day']) + '/' + str(response_data['endDate']['year'])
            anime_info['episodes'] = response_data['episodes']
            anime_info['score'] = response_data['averageScore']
            anime_info['studio'] = response_data['studios']['nodes'][0]['name']
            break
        except:
            continue
    return render_template('anime.html', anime_info = anime_info, login=dict(session).get('access_token', None))

@app.route("/change")
def change():
    if not dict(session).get('access_token', None):
        return render_template('error.html', title='Error', msgs=['Please login'], login=dict(session).get('access_token', None))

    anime_id = request.args.get('anime_id')
    media_action = request.args.get('change')
    accessToken = session['access_token']
    media_list_id = request.args.get('media_list_id')

    headers = {
        "Authorization": f"Bearer {accessToken}"
    }

    if media_action == 'DELETE':
        query = '''
        mutation ($media_list_id: Int){
            DeleteMediaListEntry (id: $media_list_id) {
                deleted
            }
        }
        '''
    else:
        query = '''
        mutation ($id: Int, $status: MediaListStatus) {
            SaveMediaListEntry (mediaId: $id, status: $status) {
                id
                status
            }
        }
        '''
    variables = {
        'id': anime_id,
        'status': media_action,
        'media_list_id': media_list_id
    }

    url = 'https://graphql.anilist.co'
    requests.post(url, headers=headers, json={'query': query, 'variables': variables})
    redirect_url = url_for('anime_view', anime_id = anime_id)
    return redirect(redirect_url)
if __name__ == "__main__":
    app.run(debug=True)
