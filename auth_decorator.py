
from flask import session, render_template
from functools import wraps

# checks if there is the session has an access token


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('access_token', None)
        if user:
            return f(*args, **kwargs)
        return render_template('user.html', username="no user", imgURL="", login=dict(session).get('access_token', None))
    return decorated_function
