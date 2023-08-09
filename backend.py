"""
Created on Tue Aug  8 20:00:49 2023

@author: ridhs
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from pymongo import MongoClient
import hashlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "your-secret-key"  
jwt = JWTManager(app)
CORS(app)

nltk.download('punkt')
nltk.download('stopwords')

auth_bp = Blueprint('auth', __name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["hr_optimization_db"]
users_collection = db["users"]
job_descriptions_collection = db["job_descriptions"]
cv_data_collection = db["cv_data"]
screening_collection = db["screening_data"]
interviews_collection = db["interviews"]
communication_collection = db["communication_data"]
hr_communication_collection = db["hr_communication_data"]


SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587  
EMAIL_USERNAME = "your-email@example.com"  
EMAIL_PASSWORD = "your-email-password"


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    if users_collection.find_one({"username": username}):
        return jsonify({"message": "Username already exists"}), 400

    users_collection.insert_one({"username": username, "password": hashed_password})
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    user = users_collection.find_one({"username": username, "password": hashed_password})

    if user:
        access_token = create_access_token(identity=username)
        return jsonify({"access_token": access_token}), 200

    return jsonify({"message": "Invalid credentials"}), 401


@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({"message": f"Protected content for user: {current_user}"}), 200


nlp = spacy.load("en_core_web_sm")


@app.route('/submit_job_description', methods=['POST'])
@jwt_required()
def submit_job_description():
    data = request.json
    candidate_id = data.get('candidate_id')
    Experience= data.get('Experience')
    Annoucement = data.get('Annoucement')
    job_title = data.get('job_title')
    company = data.get('company')
    description = data.get('description')

    if not candidate_id or not Experience or not Annoucement or not job_title or not company :
        return jsonify({"message": "Job title and description are required"}), 400

    job_descriptions_collection.insert_one({"job_title": job_title, "description": description})
    return jsonify({"message": "Job description submitted successfully"}), 201

@app.route('/upload_cv', methods=['POST'])
@jwt_required()
def upload_cv():
    data = request.json
    candidate_name = data.get('candidate_name')
    cv_data = data.get('cv_data')

    if not candidate_name or not cv_data:
        return jsonify({"message": "Candidate name and CV data are required"}), 400

    cv_data_collection.insert_one({"candidate_name": candidate_name, "cv_data": cv_data})
    return jsonify({"message": "CV uploaded successfully"}), 201


app.route('/rank_cvs', methods=['POST'])
@jwt_required()
def rank_cvs():
    data = request.json
    job_description = data.get("job_description")
    cvs = data.get("cvs")

    if not job_description or not cvs:
        return jsonify({"message": "Job description and CVs are required"}), 400
    job_desc_tokens = nlp(job_description.lower())
    cv_scores = []
    for cv in cvs:
        cv_content = cv.lower()
        cv_tokens = nlp(cv_content)
        alignment_score = job_desc_tokens.similarity(cv_tokens)
        cv_scores.append({"cv": cv, "score": alignment_score})
    ranked_cvs = sorted(cv_scores, key=lambda x: x["score"], reverse=True)
    shortlisted_candidates = [cv for cv in ranked_cvs if cv["score"] >= 0.7]
    shortlisted_with_info = []
    for candidate in shortlisted_candidates:
        cv_info = {"cv": candidate["cv"], "score": candidate["score"], "additional_info": "Placeholder info"}
        shortlisted_with_info.append(cv_info)

    return jsonify({"ranked_cvs": ranked_cvs, "shortlisted_candidates": shortlisted_with_info}), 200


@app.route('/send_email', methods=['POST'])
@jwt_required()
def send_email():
    data = request.json
    to_email = data.get('to_email')
    subject = data.get('subject')
    message = data.get('message')

    if not to_email or not subject or not message:
        return jsonify({"message": "To email, subject, and message are required"}), 400
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USERNAME, to_email, msg.as_string())
        return jsonify({"message": "Email sent successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Error sending email: {str(e)}"}), 500



@app.route('/submit_screening', methods=['POST'])
@jwt_required()
def submit_screening():
    data = request.json
    candidate_id = data.get("candidate_id")
    responses = data.get("responses")

    if not candidate_id or not responses:
        return jsonify({"message": "Candidate ID and responses are required"}), 400

    
    screening_data = {"candidate_id": candidate_id, "responses": responses}
    screening_collection.insert_one(screening_data)

    return jsonify({"message": "Screening responses submitted successfully"}), 201

@app.route('/submit_interview', methods=['POST'])
@jwt_required()
def submit_interview():
    data = request.json
    candidate_id = data.get("candidate_id")
    interview_questions = data.get("interview_questions")
    candidate_responses = data.get("candidate_responses")

    if not candidate_id or not interview_questions or not candidate_responses:
        return jsonify({"message": "Candidate ID, interview questions, and responses are required"}), 400
    interview_performance = sum([1 for q, r in zip(interview_questions, candidate_responses) if len(r) > 0])
    interview_data = {
        "candidate_id": candidate_id,
        "interview_questions": interview_questions,
        "candidate_responses": candidate_responses,
        "interview_performance": interview_performance
    }
    interviews_collection.insert_one(interview_data)

    return jsonify({"message": "Interview data submitted successfully"}), 201



@app.route('/send_hr_communication', methods=['POST'])
@jwt_required()
def send_hr_communication():
    data = request.json
    recipient_email = data.get('recipient_email')
    subject = data.get('subject')
    message = data.get('message')

    if not recipient_email or not subject or not message:
        return jsonify({"message": "Recipient email, subject, and message are required"}), 400

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USERNAME, recipient_email, msg.as_string())
        
    
        hr_communication_data = {"recipient_email": recipient_email, "subject": subject, "message": message}
        hr_communication_collection.insert_one(hr_communication_data)

        return jsonify({"message": "HR communication sent and saved successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Error sending HR communication: {str(e)}"}), 500



if __name__ == '__main__':
    app.run(debug=True)

