from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import json
import config

application = app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://" + config.username+":"+config.password+"@"+config.host1+":"+config.port+","+config.host2+":"+config.port+","+config.host3+":"+config.port+"/"+config.database+"?"+config.params

mongo = PyMongo(app)

def encode(obj):
	for key, value in obj.items():
		if isinstance(value, ObjectId):
			obj[key] = str(value)
	return obj

def insert_match(data):
	ids = mongo.db.matches.find({},{'match_id':1}).sort('match_id',-1).limit(1)
	if ids.count() > 0:
		new_id = ids[0]['match_id'] + 1
	else:
		new_id = 1
	data['match_id'] = new_id
	matches = mongo.db.matches.insert_one(data)
	return mongo.db.matches.find_one({'match_id':new_id})

@app.route("/players/<id>", methods=['GET'])
def get_player(id):
	players = mongo.db.player_statistics.find({'id':int(id)})
	return jsonify({"response":[encode(player) for player in players]})

@app.route("/players", methods=['GET','POST'])
def get_all_players():
	if 'type' in request.args:
		type = request.args.get('type')
		if type == 'bat':
			players = mongo.db.player_statistics.find().sort('runs', -1).limit(5)
		elif type == 'bowl':
			players = mongo.db.player_statistics.find().sort('wickets', -1).limit(5)
	else:
		players = mongo.db.player_statistics.find()
	return jsonify({"response":[encode(player) for player in players]})

@app.route("/teams/<id>", methods=['GET'])
def get_team(id):
	teams = mongo.db.teams.find({'id':int(id)})
	return jsonify({"response":[encode(team) for team in teams]})

@app.route("/teams", methods=['GET'])
def get_all_teams():
	teams = mongo.db.teams.find().sort('points',-1)
	return jsonify({"response":[encode(team) for team in teams]})

@app.route("/matches", methods=['GET','POST'])
def matches():
	if request.method == "POST":
		data = request.get_json()
		return jsonify({"response":{"inserted_match":encode(insert_match(data))}})
	elif request.method == "GET":
		matches = mongo.db.matches.find()
		return jsonify({"response":[encode(match) for match in matches]})
	return ""

@app.route("/matches/<id>", methods=['GET'])
def get_match(id):
	matches = mongo.db.matches.find({'id':int(id)})
	return jsonify({"response":[encode(match) for match in matches]})

if __name__ == '__main__':
    app.run(debug=True)