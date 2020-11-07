from flask import Flask, render_template, request, url_for, flash, redirect
from string import Template
from forms import LoginForm
import requests
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = '739b8f5167d69c5ded99a055d73c52ac'
@app.route("/")
def home_view():
    return render_template('home.html', title="Home")

@app.route("/about")
def about_view():
    return render_template('about.html', title ="About")

@app.route("/login", methods=['GET', 'POST'])
def login_view():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == 'Rynk' and form.password.data == 'password':
            flash('You have been logged in!', 'success')
            return redirect(url_for('home_view'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

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
    english = json_data['data']['Media']['title']['english']
    romaji = json_data['data']['Media']['title']['romaji']
    imageURL = json_data['data']['Media']['coverImage']['extraLarge']
    return render_template('animePage.html', title = english, imgURL = imageURL, romaji = romaji)

if __name__ == "__main__":
    app.run(debug=True)