from flask import Flask, jsonify, request , abort ,send_file ,render_template
from flask_restful import Api, Resource ,reqparse
from pymongo import MongoClient
from bson import ObjectId
from gridfs import GridFS
from gridfs import errors as gridfs_errors
# import json
# import base64
import io

app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
tasks_collection = db['tasks']
images_collection = db['images']
collection = db['formatted_text_collection']
fs = GridFS(db)


# a simple curd 
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
        


# post image throh postman
# class ImageUpload(Resource):
#     def post(self):
#         parser = reqparse.RequestParser()
#         parser.add_argument('image_data', type=str, required=True, help='Base64 encoded image data is required')
#         args = parser.parse_args()
#         return {'message': 'Image uploaded successfully'}, 201

# class ImageView(Resource):
#     def get(self, image_id):
#         # Retrieve the image from MongoDB based on the image_id
#         image_data = b'' # Get image data from MongoDB
#         if image_data:
#             return send_file(io.BytesIO(image_data), mimetype='image/jpeg')
#         else:
#             return {'message': 'Image not found'}, 404



# for storing and retreiving images
@app.route('/image')
def upload_form():
    return render_template('image.html')

class ImageUpload(Resource):
    def post(self):
        image_file = request.files['image']
        image_id = fs.put(image_file)
        images_collection.insert_one({'_id': image_id, 'filename': image_file.filename})
        return {'message': 'Image uploaded successfully', 'image_id': str(image_id)}
class Image(Resource):
    def get(self, image_id):
        try:
            image_data = fs.get(ObjectId(image_id))
            return send_file(image_data, mimetype='image/jpeg')
        except gridfs_errors.NoFile:
            return {'error': 'Image not found'}, 404


api.add_resource(TaskResource, '/tasks', '/tasks/<string:task_id>')
# api.add_resource(ImageView, '/images/<string:image_id>')
# api.add_resource(ImageUpload, '/images')
api.add_resource(ImageUpload, '/upload')
api.add_resource(Image, '/image/<string:image_id>')





# to add forammetedtext
@app.route('/')
def indexs():
    return render_template('text.html')


@app.route('/save_text', methods=['POST'])
def save_text():
    if request.method == 'POST':
        text = request.form.get('text')  
        print("Received text:", text)   
        if text is not None:
            print(text,'inside if ')
            inserted_text = collection.insert_one({'text': text})
            print("Inserted text ID:", inserted_text.inserted_id)   
            if inserted_text.inserted_id:
                return jsonify({'message': 'Text saved successfully'})
            else:
                return jsonify({'error': 'Failed to save text'}), 500
        else:
            return jsonify({'error': 'No text provided'}), 400
    else:
        return jsonify({'error': 'Method Not Allowed'}), 405



from bson import ObjectId
@app.route('/get_text/<text_id>', methods=['GET'])
def get_text(text_id):
    # Convert text_id to ObjectId
    try:
        object_id = ObjectId(text_id)
    except:
        return jsonify({'error': 'Invalid text ID format'}), 400

    stored_text = collection.find_one({'_id': object_id})
    if stored_text:
        print(stored_text)
        return render_template('dispaly.html',stored_text=stored_text)
    else:
        return jsonify({'message': 'No text found for the given ID'}), 404


if __name__ == '__main__':
    app.run(debug=True)
