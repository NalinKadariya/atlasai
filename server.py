# Imports
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Create the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Create the User model
class User(db.Model):
    # Store username, password, gmail, openai_key, assemblyai_key and eleven_ai_key.
    username = db.Column(db.String(50), primary_key=True, nullable=False, unique=True)
    password_hash = db.Column(db.String(100), nullable=False)
    openai_key = db.Column(db.String(100), nullable=False, unique=False)

    # method to save
    def save_openai_key(self, openai_key): # Save the openai key
        self.openai_key = openai_key

    def save_pas(self, password): # Save the password
        self.password_hash = generate_password_hash(password)

    # method to check if the password is correct
    def check_password(self, password): # Check if the password is correct
        return check_password_hash(self.password_hash, password)

@app.route('/signup', methods=['POST'])
def signup():
    with app.app_context():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        openai_key = data.get('openai_key')

    
        # Check if username and password are empty, make sure gmail and openai_key are not empty
        if not username or not password:
            return jsonify({'error': 'Invalid.'}), 400
        
        # Check if the user or gmail already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists.'}), 400
        
        # make a new user
        user = User(username=username)
        user.save_pas(password)
        user.save_openai_key(openai_key)
        db.session.add(user)
        db.session.commit()

        return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    with app.app_context():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username=username).first()
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Get the user from the database
        user = User.query.filter_by(username=username).first()
        if user is None:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if the password is correct
        if not user.check_password(password):
            return jsonify({'error': 'Invalid password'}), 401
        
        # Send a success message with openai key
        return jsonify({'message': 'Logged in successfully. ', 'openai_key': user.openai_key}), 200


# Run the server
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0',port=5000,debug=True)