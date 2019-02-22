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
	return jsonify({"response":[team for team in teams]})

if __name__ == '__main__':
    app.run(debug=True)