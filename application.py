from flask import Flask, render_template, request, url_for, redirect, session
from string import Template
from authlib.integrations.flask_client import OAuth
import requests
import json
import numpy as np
import random

# for videos
import urllib.request
import re

# for auth
from datetime import timedelta
from auth_decorator import login_required

# the app
application = app = Flask(__name__)
# Session config
app.config['SESSION_COOKIE_NAME'] = 'anilist-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

# Auth setup
oauth = OAuth(app)
anilist = oauth.register(
    name='anilist',
    client_id='4320',
    access_token_url='https://anilist.co/api/v2/oauth/token',
    access_token_params=None,
    authorize_url='https://anilist.co/api/v2/oauth/authorize',
    authorize_params=None,
    api_base_url='https://anilist.co/api/v2/oauth/',
)
# Start webpage
@app.route("/")
def home_view():
    url = "https://graphql.anilist.co"
    query = '''
        query{
            GenreCollection
        }
    '''
    response = requests.post(url, json={"query": query}).json()
    genre_list = response['data']['GenreCollection']
    format_list = ['TV', 'Movie', 'TV Short', 'Special', 'OVA', 'ONA', 'Music']
    return render_template('home.html', genre_list = genre_list, format_list = format_list, title="Home", login=dict(session).get('access_token', None))

# Search webpage
@app.route("/search")
def search_view():
    return render_template('search.html', title="Search", login=dict(session).get('access_token', None))

# About webpage
@app.route("/about")
def about_view():
    return render_template('about.html', title="About", login=dict(session).get('access_token', None))

@app.route("/animeResults")
def anime_results_view():
    anime_name = request.args.get('search')
    page_num = request.args.get('page')
    query = '''
        query ($page: Int, $perPage: Int, $search: String) {
            Page (page: $page, perPage: $perPage) {
                pageInfo {
                    lastPage
                }
                media (search: $search, type: ANIME) {
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
                description(asHtml: true)
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
                description(asHtml: true)
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
    try: 
        anime_info['source'] = response_data['source'].title()
    except AttributeError:
        anime_info['source'] = None
    try:
        anime_info['season'] = response_data['season'].title() + ' ' + str(response_data['startDate']['year'])
        anime_info['studio'] = response_data['studios']['nodes'][0]['name']
    except AttributeError:
        anime_info['season'] = None
    except IndexError:
        anime_info['studio'] = None
    finally:
        anime_info['img_URL'] = response_data['coverImage']['large']
        anime_info['romaji'] = response_data['title']['romaji']
        anime_info['english'] = response_data['title']['english']
        anime_info['start_date'] = str(response_data['startDate']['month']) + '/' + str(response_data['startDate']['day']) + '/' + str(response_data['startDate']['year'])
        anime_info['end_date'] = str(response_data['endDate']['month']) + '/' + str(response_data['endDate']['day']) + '/' + str(response_data['endDate']['year'])
        anime_info['episodes'] = response_data['episodes']
        anime_info['score'] = response_data['averageScore']
        anime_info['description'] = response_data['description']
        anime_info['id'] = response_data['id']
        anime_info['genres'] = response_data['genres']
        anime_info['format'] = response_data['format'].title()
        anime_info['anime_status'] = response_data['status'].title()
    #Use while try and catch if catch knows what line is bad
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
    
    try:
        #gets rid of unicode
        string_encode = anime_info['english'].replace(" ", "+").encode("ascii", "ignore")
        string_decode = string_encode.decode()

        op_search_keyword = "official+" + string_decode + "+opening"
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + op_search_keyword)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        anime_info['OP'] = "https://www.youtube.com/embed/" + video_ids[0]

        ed_search_keyword = "official+" + string_decode + "+ending"
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + ed_search_keyword)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        anime_info['ED'] = "https://www.youtube.com/embed/" + video_ids[0]
    except AttributeError:
        # gets rid of unicode
        string_encode = anime_info['romaji'].replace(" ", "+").encode("ascii", "ignore")
        string_decode = string_encode.decode()

        op_search_keyword = "official+" + string_decode + "+opening"
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + op_search_keyword)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        anime_info['OP'] = "https://www.youtube.com/embed/" + video_ids[0]

        ed_search_keyword = "official+" + string_decode + "+ending"
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + ed_search_keyword)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        anime_info['ED'] = "https://www.youtube.com/embed/" + video_ids[0]
    # except UnicodeEncodeError:
    #     anime_info['OP'] = "https://www.youtube.com/embed/dQw4w9WgXcQ"
    #     anime_info['ED'] = "https://www.youtube.com/embed/dQw4w9WgXcQ"

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
                status
            }
        }
    }
    '''
    variables = {
        'id': session['userID']
    }
    response = requests.post(url, json={'query': query, 'variables': variables}).json()


    list_info = {}
    for i in range(len(response['data']['MediaListCollection']['lists'])):
        anime_list = response['data']['MediaListCollection']['lists'][i]['entries']

        anime_info = {}
        for anime in anime_list:
            #ANIME NAME = (SCORE, IMAGE, ID)
            anime_info[anime['media']['title']['romaji']] = (anime['score'], anime['media']['coverImage']['medium'], anime['media']['id'])

        list_info[response['data']['MediaListCollection']['lists'][i]['status']] = dict(sorted(anime_info.items(), 
        key=lambda item: item[1], reverse=True))

    return render_template('user.html', user_info = user_info, list_info = list_info, login=dict(session).get('access_token', None))

@app.route("/recommendation")
def recommendation_view():
    genre_list = request.args.getlist('genre_list')
    if not bool(genre_list):
        genre_list = None
    year_filter = request.args.get('year')
    if year_filter:
        year_filter = year_filter + '0101'
    else:
        year_filter = 19800101

    score_filter = request.args.get('score')
    if score_filter:
        score_filter = score_filter + '0'
    else:
        score_filter = 60

    format_list = request.args.getlist('format_list')
    if bool(format_list):
        format_list = [sub.replace(' ', '_') for sub in format_list]
    else:
        format_list = ['TV', 'MOVIE', 'ONA']
    # check if they are logged in
    if not dict(session).get('access_token', None):
        return redirect('/login')

    # check if there is a list already compiled
    # if (dict(session).get('recommendation_list', None)):
    #     recommendation_list = session['recommendation_list']
    #     return render_template('recommendations.html', recommendation_list = recommendation_list, title="Recommendations", login=dict(session).get('access_token', None))
        
    url = "https://graphql.anilist.co"

    accessToken = session['access_token']

    header = {
        "Authorization": f"Bearer {accessToken}"
    }

    tag_query = '''
    query{
        MediaTagCollection{
            name
        }
    }
    '''
    tag_response = requests.post(url, json={'query': tag_query}).json()

    tag_list = []
    for dic in tag_response['data']['MediaTagCollection']:
        tag_list.append(dic['name'])

    tag_map = {k: v for v, k in enumerate(tag_list)}

    user_query = '''
    query($id: Int){
        MediaListCollection(userId: $id, type: ANIME, status_in: [COMPLETED]){
            lists{
                entries{
                    score
                    media{
                        title{
                            romaji
                        }
                        tags{
                            name
                            rank
                        }
                    }
                }
            }
        }
    }
    '''

    unseen_query = '''
    query($page: Int, $year_filter: FuzzyDateInt, $score_filter: Int, $format_list: [MediaFormat], $genre_list: [String]){
        Page(perPage: 50 page: $page){
                pageInfo{
                    lastPage
                }
            media(onList: false, type: ANIME, isAdult: false, format_in: $format_list, status_in: [FINISHED, RELEASING], 
            startDate_greater: $year_filter, popularity_greater: 10000, averageScore_greater: $score_filter, genre_in: $genre_list){
                id
                title{
                    romaji
                }
                coverImage{
                    medium
                }
                tags{
                    name
                    rank
                }
            }
        }
    }
    '''
    user_variables = {
        'id': session['userID']
        # genre, score, year, on friends list, format, 
    }

    user_response = requests.post(url, json={'query': user_query, 'variables': user_variables}).json()
    anime_list = user_response['data']['MediaListCollection']['lists'][0]['entries']

    weights = [0] * len(tag_list)
    for anime in anime_list:
        for tag in anime['media']['tags']:
            weights[tag_map[tag['name']]] += anime['score'] * tag['rank']

    unseen_list = []
    for i in range(1, 30):
        unseen_variables = {
            'page': i,
            'year_filter': year_filter,
            'score_filter': score_filter,
            'format_list': format_list,
            'genre_list': genre_list
        }
        unseen_response = requests.post(url, headers = header, json = {'query': unseen_query, 'variables': unseen_variables}).json()
        if not bool(unseen_response['data']['Page']['media']):
            break
        unseen_list += unseen_response['data']['Page']['media']

    scores = []
    for anime in unseen_list:
        score = 0
        for tag in anime['tags']:
            score += weights[tag_map[tag['name']]] * tag['rank']
        scores.append(score * -1)

    rankings = np.argsort(scores)
    rankings = rankings[:50]
    recommendation_list = []

    for index in rankings:
        anime_info = {}
        anime_info['id'] = unseen_list[index]['id']
        anime_info['img_URL'] = unseen_list[index]['coverImage']['medium']
        anime_info['romaji'] = unseen_list[index]['title']['romaji']
        recommendation_list.append(anime_info)
    # session['recommendation_list'] = recommendation_list
    return render_template('recommendations.html', recommendation_list = recommendation_list, title="Recommendations", login=dict(session).get('access_token', None))

@app.route("/random")
def random_anime():
    url = 'https://graphql.anilist.co'
    #first query to get the total number of anime
    query ='''
    query{
        Page(perPage: 1){
            pageInfo{
                lastPage
            }
            media(type: ANIME){
                id
            }
        }
    }
    '''
    response = requests.post(url, json={'query': query}).json()
    upper_bound = response['data']['Page']['pageInfo']['lastPage']
    random_page = random.randint(1, upper_bound)

    #second query to randomly get an anime id
    query ='''
    query($page: Int){
        Page(perPage: 1 page: $page){
                pageInfo{
                    lastPage
                }
            media(type: ANIME){
                id
            }
        }
    }
    '''
    variables = {
        'page': random_page
    }
    response = requests.post(url, json={'query': query, 'variables': variables}).json()
    random_anime_id = response['data']['Page']['media'][0]['id']
    redirect_url = url_for('anime_view', anime_id = random_anime_id)
    return redirect(redirect_url)

@app.route("/change")
def change():
    if not dict(session).get('access_token', None):
        return redirect('/login')

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
