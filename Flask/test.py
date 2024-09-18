from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Path to store the coordinates data
DATA_FOLDER = 'data'
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Route to handle the POST request from the client
@app.route('/save-coordinates', methods=['POST'])
def save_coordinates():
    username = session['username']
    data = request.get_json()  # Get the JSON data from the request
    image_name = data.get('imageName')
    coordinates = data.get('coordinates')
    if not image_name or not coordinates:
        return jsonify({'error': 'Invalid data'}), 400
    # Create a filename based on the image name
    filename = f'Flask/image_user_rectangle/username{image_name}_coordinates.txt'
    if not os.path.exists(filename):
        os.makedirs(filename)
    # Prepare the text content to save
    with open(filename, 'w') as f:
        for i, coord in enumerate(coordinates):
            f.write(f"Rectangle {i + 1}:\n")
            f.write(f"  Start point: (x1: {coord['x1']}, y1: {coord['y1']})\n")
            f.write(f"  End point: (x2: {coord['x2']}, y2: {coord['y2']})\n")
            f.write("\n")  # Add an extra line between rectangles
    return jsonify({'message': 'Coordinates saved successfully!'}), 200

if __name__ == '__main__':
    app.run(debug=True)
