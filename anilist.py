from flask import Flask, render_template, request, url_for, flash, redirect, session
from string import Template
from authlib.integrations.flask_client import OAuth
import requests
import json

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

#Animeinfo webpage
@app.route("/animeInfo", methods=['POST'])
def anime_page_view():
    anime_name = request.form.get('search-bar')
    query = '''
    query ($anime_name: String) {
        Media (search: $anime_name, type: ANIME) {
            id
            title {
                romaji
                english
                native
            }
            coverImage {
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
    english = json_data['data']['Media']['title']['english']
    romaji = json_data['data']['Media']['title']['romaji']
    imageURL = json_data['data']['Media']['coverImage']['extraLarge']
    return render_template('animePage.html', title = english, imgURL = imageURL, romaji = romaji, login=dict(session).get('access_token', None))

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
        }
    }
    '''
    response = requests.post(url, headers=headers, json={"query": query}).json()
    username = response['data']['Viewer']['name']
    imageURL = response['data']['Viewer']['avatar']['large']
    return render_template('user.html', username=username, imgURL=imageURL, login=dict(session).get('access_token', None))

if __name__ == "__main__":
    app.run(debug=True)