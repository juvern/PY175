from flask import Flask, render_template, g, redirect
import yaml

app = Flask(__name__) # creates an instance of the Flask class


@app.before_request # done before every request
def load_content():
    with open('users.yaml', 'r') as file:
        g.data = yaml.safe_load(file) # converts to a Python object

@app.route('/')
def index():
    return render_template('index.html', 
                            data=g.data,
                            total_interests=total_interests())

@app.route('/user/<name>/')
def user(name):
    result = []
    if name in g.data:
        result = g.data[name]
    else:
        return redirect("/")         

    return render_template('user.html',
                            name=name,
                            result=result,
                            data=g.data)


def total_interests():
    count = 0
    for user in g.data.values():
        count += len(user['interests'])

    return count


@app.errorhandler(404)
def page_not_found(_error):
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True, port=5003)

'''
{
    'jamy': {
        'email': 'jamy.rustenburg@gmail.com', 
        'interests': ['woodworking', 'cooking', 'reading']
        }, 
    'nora': {
        'email': 'nora.alnes@yahoo.com',
        'interests': ['cycling', 'basketball', 'economics']
        },
     'hiroko':{
        'email': 'hiroko.ohara@hotmail.com', 'interests': []}
        }
'''    