from bottle import route, run, request, static_file, error, get, post, response, template


@route('/')
def index():
    return '<h1>Hellow world<h1>'

@route('/second')
def second():
    name = request.query.get("name", default='')
    return f'<h1>Hi "{name}"<h1>'

@route('/picture')
def second():
    return static_file('testik.jpg', 'C:\\Users\\Кирилл Кравченя\\Desktop\\test')

# @route('/second/<name>')
# def second(name):
#     return f'<h1>Hi "{name}"<h1>'
@route('/second/<id:re:[0-9]+>')
def second(id):
    return f'<h1>Hi "{id}"<h1>'


@get('/login') # or @route('/login')
def login():
    return '''
        <form action="/login" method="post">
            Username: <input name="username" type="text" />
            Password: <input name="password" type="password" />
            <input value="Login" type="submit" />
        </form>
    '''

@post('/login') # or @route('/login', method='POST')
def do_login():
    username = request.forms.get('username')
    password = request.forms.get('password')
    if username == "admin" and password == 'admin':
        response.set_cookie("account", username, secret=password)
        return template("<p>Welcome {{name}}! You are now logged in.</p>", name=username)
    else:
        return "<p>Login failed.</p>"


@error(404)
def error404(error):
    return "Page not found!"

run(host='localhost', port=8080)