from pymongo import MongoClient
from flask import Flask, jsonify, render_template, request
import redis
import json
import jinja2
from bson.objectid import ObjectId
import datetime



app = Flask(__name__)
r = redis.Redis(host = 'localhost', port = 6379 )

client = MongoClient('localhost', 27017)
db  = client.postdb
collection = db.post_collection

comms = collection.find()


# https://stackoverflow.com/questions/16586180/typeerror-objectid-is-not-json-serializable

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


@app.route('/index')
def index():
    return render_template('index.html', comms = comms)


@app.route('/<_id>')
def find_one_post(_id):
    try:

        post = json.loads(r.get(_id))
        return render_template('find_one_post.html', post=post)

    except TypeError:

        post = collection.find_one({'_id': ObjectId(_id)})
        post_json = JSONEncoder().encode(post)
        r.set(_id, post_json)

        return render_template('find_one_post.html', post=post)


@app.route('/<_id>/statistic')
def stat(_id):
    try:

        post = json.loads(r.get(_id))
        statistic_tags = len(post['tags'])
        statistic_comments = len(post['comment'])
        return render_template('statistic.html', post=post, statistic_tags=statistic_tags, statistic_comments=statistic_comments)

    except TypeError:

        post = collection.find_one({'_id': ObjectId(_id)})
        statistic_tags = len(post['tags'])
        statistic_comments = len(post['comment'])

        return render_template('statistic.html', post=post, statistic_tags=statistic_tags, statistic_comments=statistic_comments)


@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        author = request.form['name']
        tags = request.form['tags'].split(',')
        text = request.form['message']
        comments = []
        new_post = {
            'author': author,
            'tags': tags,
            'text': text,
            'pub_date': datetime.datetime.today().isoformat(),
            'comments': comments
        }
        collection.insert_one(new_post)
        return render_template('index.html', comms = comms)
    else:
        return render_template('new_post.html')


@app.route('/tags', methods=['GET', 'POST'])
def tags():
    if request.method == 'GET':
        return render_template('tags.html')
    else:
        _id = request.form['id']
        if len(_id) != 24 or collection.find_one({'_id': ObjectId(_id)}) == None:
            error = 'ID отсутствует'
            return render_template('tags.html', error=error)
        else:
            r.delete(_id)
            tags = request.form['tags'].split(',')
            post = collection.find_one({'_id': ObjectId(_id)})
            new_tags = post['tags']
            for _ in tags:
                new_tags.append(_)
            collection.update_one({'_id': ObjectId(_id)}, {
                '$set': {'tags': new_tags}})
            return render_template('index.html', comms = comms)


@app.route('/comments', methods=['GET', 'POST'])
def comments():
    if request.method == 'GET':
        return render_template('comments.html')
    else:
        _id = request.form['id']
        if len(_id) != 24 or collection.find_one({'_id': ObjectId(_id)}) == None:
            error = 'ID отсутствует'
            return render_template('comments.html', error=error)
        else:
            r.delete(_id)
            author = request.form['name']
            comment = request.form['comment']
            post = collection.find_one({'_id': ObjectId(_id)})
            new_comment = post['comment']
            new_comment.append({'author': author, 'comment': comment})
            collection.update_one({'_id': ObjectId(_id)}, {
                '$set': {'comments': new_comment}})
            return find_one_post(_id)
            

if __name__ == '__main__':
    app.run(debug=False)

