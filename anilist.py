from flask import Flask, render_template, request, url_for, redirect, session
from string import Template
from authlib.integrations.flask_client import OAuth
import requests
import json
import numpy as np

#for auth
import os
from datetime import timedelta
from auth_decorator import login_required

#the app
app = Flask(__name__)
#Session config
app.secret_key = "739b8f5167d69c5ded99a055d73c52ac"
app.config['SESSION_COOKIE_NAME'] = 'anilist-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

#Auth setup
oauth = OAuth(app)
anilist = oauth.register(
    name='anilist',
    client_id= '4320',
    client_secret = 'PvdcI16xxNlq11QVR7F1ZA0ykH66rPyhJA8VcR4h',
    access_token_url= 'https://anilist.co/api/v2/oauth/token',
    access_token_params=None,
    authorize_url= 'https://anilist.co/api/v2/oauth/authorize',
    authorize_params=None,
    api_base_url='https://anilist.co/api/v2/oauth/',
)
#Start webpage
@app.route("/")
def home_view():
    return render_template('home.html', title="Home", login=dict(session).get('access_token', None))
#About webpage
@app.route("/about")
def about_view():
    return render_template('about.html', title ="About", login=dict(session).get('access_token', None))

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
    currentPage = int(page_num), numPages = total_pages, name = anime_name, login=dict(session).get('access_token', None))

#login webpage
@app.route('/login')
def login():
    anilist = oauth.create_client('anilist') 
    redirect_uri = url_for('authorize', _external=True)
    return anilist.authorize_redirect(redirect_uri)

#safe redirect to authorize then redirects to another page
@app.route('/authorize')
def authorize():
    anilist = oauth.create_client('anilist')  
    token = anilist.authorize_access_token()
    #print(token)
    #print(session['access_token'])
    session['access_token'] = token['access_token']
    session.permanent = True  
    return redirect('/user')

#gets rid of the session cookie
@app.route("/logout")
def logout():
    session.clear()
    return redirect('/user')

#user webpage
@app.route("/user")
@login_required
def user_view():
    # EXAMPLE CODE FOR USING ACCESS CODE
    # body = {
    #     'grant_type': 'authorization_code',
    #     'client_id': client_id,
    #     'client_secret': client_secret,
    #     'redirect_uri': redirect_uri,
    #     'code': code
    # }

    # accessToken = requests.post("https://anilist.co/api/v2/oauth/token", json=body).json().get("access_token")
    # res = requests.post("https://graphql.anilist.co",
    #                     headers={"Authorization": f"Bearer {accessToken}"}, json={"query": "{Viewer{name}}"}).json()
    # print(res)
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
        }
    }
    '''

    response = requests.post(url, headers=headers, json={"query": query}).json()
    username = response['data']['Viewer']['name']
    imageURL = response['data']['Viewer']['avatar']['large']
    session['userID'] = response['data']['Viewer']['id']

    return render_template('user.html', username=username, imgURL=imageURL, login=dict(session).get('access_token', None))

@app.route("/recommendation")
def recommendation():
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
    query($page: Int){
        Page(perPage: 50 page: $page){
                pageInfo{
                    lastPage
                }
            media(onList: false, type: ANIME, isAdult: false, format_in: [TV, MOVIE, ONA], status_in: [FINISHED, RELEASING], 
            startDate_greater: 19800101, popularity_greater: 10000, averageScore_greater: 60){
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
    '''
    user_variables = {
        'id': session['userID']
    }

    user_response = requests.post(url, json={'query': user_query, 'variables': user_variables}).json()
    anime_list = user_response['data']['MediaListCollection']['lists'][0]['entries']

    weights = [0] * len(tag_list)
    for anime in anime_list:
        for tag in anime['media']['tags']:
            weights[tag_map[tag['name']]] += anime['score'] * tag['rank']

    for i in range(len(tag_list)):
        print(tag_list[i] + " has weight " + str(weights[i]))

    unseen_list = []
    for i in range(1, 30):
        unseen_variables = {
            'page': i
        }
        unseen_response = requests.post(url, headers = header, json = {'query': unseen_query, 'variables': unseen_variables}).json()
        unseen_list += unseen_response['data']['Page']['media']

    scores = []
    for anime in unseen_list:
        score = 0
        for tag in anime['tags']:
            score += weights[tag_map[tag['name']]] * tag['rank']
        scores.append(score)

    rankings = np.argsort(scores)

    for index in rankings:
        print(unseen_list[index]['title']['romaji'] + " scored " + str(scores[index]))

    return render_template('home.html', title="Home", login=dict(session).get('access_token', None))

if __name__ == "__main__":
    app.run(debug=True)