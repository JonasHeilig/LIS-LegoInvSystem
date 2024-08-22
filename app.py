from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime
import config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lis.db'
db = SQLAlchemy(app)


class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_id = db.Column(db.Integer, unique=True, nullable=False)
    ls_id = db.Column(db.String(80), unique=True, nullable=False)
    title = db.Column(db.String(120), unique=True, nullable=False)
    ean = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.String(120), nullable=True)
    part_numbers = db.Column(db.String(120), nullable=True)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


def get_user_hash():
    url = 'https://brickset.com/api/v3.asmx/login'
    params = {
        'apiKey': config.api_key,
        'username': config.username,
        'password': config.password
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('hash')
    else:
        return None


def get_set_data(query):
    user_hash = get_user_hash()
    if not user_hash:
        return None

    url = 'https://brickset.com/api/v3.asmx/getSets'
    params = {
        'apiKey': config.api_key,
        'userHash': user_hash,
        'query': query,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'sets' in data and data['sets']:
            return data['sets'][0]
    return None


def get_price(data):
    lego_com = data.get('LEGOCom', {})
    if 'DE' in lego_com:
        return f"{lego_com['DE']['retailPrice']}€"
    elif 'US' in lego_com:
        return f"${lego_com['US']['retailPrice']}"
    return None


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            result = Search.query.filter((Search.ean == query) | (Search.ls_id == query)).first()
            if result:
                data = get_set_data(result.ls_id)
                if data:
                    result.title = data['name']
                    result.part_numbers = ','.join([part['partNumber'] for part in data.get('minifigs', [])])
                    result.price = get_price(data)
                    result.last_updated = datetime.utcnow()
                    db.session.commit()
                    return render_template('result.html', result=result)
                else:
                    return "Set not found on Brickset API.", 404
            else:
                data = get_set_data(query)
                if data:
                    new_search = Search(
                        api_id=data['setID'],
                        ls_id=data['number'],
                        title=data['name'],
                        ean=query if query.isdigit() else '',
                        price=get_price(data),
                        part_numbers=','.join([part['partNumber'] for part in data.get('minifigs', [])]),
                        last_updated=datetime.utcnow()
                    )
                    db.session.add(new_search)
                    db.session.commit()
                    return render_template('result.html', result=new_search)
                else:
                    return "Set not found on Brickset API.", 404

    return render_template('search.html')


@app.route('/')
def home():
    return redirect(url_for('search'))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
