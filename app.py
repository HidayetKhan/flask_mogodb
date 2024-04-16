from flask import Flask, jsonify, request , abort
from flask_restful import Api, Resource
from pymongo import MongoClient
from bson import ObjectId
import json

app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
tasks_collection = db['tasks']


class TaskResource(Resource):
    def get(self, task_id=None):
        if task_id:
            task = tasks_collection.find_one({'_id': ObjectId(task_id)})
            if task:
                task['_id'] = str(task['_id'])
                return jsonify(task)
            else:
                abort(404, description="Task not found")
        else:
            tasks = tasks_collection.find()
            tasks = [{'_id': str(task['_id']), **task} for task in tasks]
            return jsonify({'tasks': tasks})

    def post(self):
        task_data = request.json
        task_id = tasks_collection.insert_one(task_data).inserted_id
        return {'message': 'Task created successfully', 'task_id': str(task_id)}, 201


    def put(self, task_id):
        task_data = request.json
        result = tasks_collection.update_one({'_id': ObjectId(task_id)}, {'$set': task_data})
        if result.modified_count == 1:
            return jsonify({'message': 'Task updated successfully'})
        else:
            return jsonify({'error': 'Task not found'}), 404

    def delete(self, task_id):
        result = tasks_collection.delete_one({'_id': ObjectId(task_id)})
        if result.deleted_count == 1:
            return jsonify({'message': 'Task deleted successfully'})
        else:
            return jsonify({'error': 'Task not found'}), 404

api.add_resource(TaskResource, '/tasks', '/tasks/<string:task_id>')

if __name__ == '__main__':
    app.run(debug=True)
