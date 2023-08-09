"""
Created on Mon Aug  2 22:03:07 2023

@author: ridhs
"""

import streamlit as st
import requests


def send_data_to_backend(endpoint, data):
    url = 'http://127.0.0.1:5000/'  
    files = {f'cv_{i}': (cv.name, cv, cv.type) for i, cv in enumerate(data.get('cvs', []))}
    response = requests.post(f"{url}/{endpoint}", data=data, files=files)
    return response.json()

def process_cvs(cvs):
    if cvs:
        ranked_cvs = [cv.name for cv in cvs]
        return ranked_cvs
    else:
        return []
    

def main():
    st.set_page_config(page_title='HR Optimization', page_icon='📊', layout='wide')
   


    st.header("Registration")
    register_username = st.text_input("Username")
    register_password = st.text_input("Password", type="password")
    if st.button("Register"):
        register_data = {"username": register_username, "password": register_password}
        response = requests.post("http://localhost:5000/register", json=register_data)
    st.write(response.json()["message"])

    st.header("Login")
    login_username = st.text_input("Username")
    login_password = st.text_input("Password", type="password")
    if st.button("Login"):
        login_data = {"username": login_username, "password": login_password}
        response = requests.post("http://localhost:5000/login", json=login_data)
        if response.status_code == 200:
            access_token = response.json()["access_token"]
            st.success("Login successful!")
            st.write(f"Access Token: {access_token}")
        else:
            st.error("Login failed. Check your credentials.")


    st.header("Protected Content")
    access_token = st.text_input("Enter Access Token")
    if st.button("Access Protected Content"):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("http://localhost:5000/protected", headers=headers)
        if response.status_code == 200:
            st.success(response.json()["message"])
        else:
            st.error("Access denied. Make sure you're logged in and provide a valid access token.")

    

   
    st.sidebar.title('Select HR Tasks')
    page_options = {
        'Job Description Evaluation': evaluate_job_description,
        'CV Ranking': rank_cvs,
        'Email':email_notification,
        'Screening Question':Screening,
        'Shortlisted Candiate':Shortlist_Candidates,
        'Interview': interview,
        'Communication':communication,
    }
    selected_page = st.sidebar.radio('Select HR Task:', list(page_options.keys()))
    page_function = page_options[selected_page]
    page_function()


def evaluate_job_description():
    st.title('Job Description Evaluation')
    col1, col2,col3 = st.columns(3)
    col4,col5 = st.columns(2)
    with col1:
        candidate_id = st.text_input('Candidate Id')
    with col4:
        Tittle = st.text_input('Job Title')
    with col2:
        Experience = st.text_input('Experience')
    with col5:
        Comapany = st.text_input('Company')
    with col3:
        Annoucement = st.text_input('Annoucement')
    job_description = st.text_area('Job Description', height=150)
    cvs = st.file_uploader('Upload CVs (PDF or Text)', accept_multiple_files=False)
    submit_button = st.button('Submit')

    if submit_button and job_description and cvs:
        data = {
            'job_description': job_description,
            'cvs': cvs
        }
        ranked_candidates = send_data_to_backend('get_ranked_candidates', data)

        st.header('Ranked CVs')
        for candidate in ranked_candidates:
            st.subheader('Email: {}'.format(candidate['email']))
            st.write('Similarity Score: {:.2f}%'.format(candidate['similarity_score'] * 100))
            st.download_button('Download CV', candidate['cv_path'], candidate['email'])

        st.success('Candidates ranked successfully!')
    elif submit_button:
        st.warning('Please provide both Job Description and CVs to proceed.')

    if not submit_button or not (job_description and cvs):
        st.write('Please provide the Job Description and upload CVs to proceed.')


def rank_cvs():
    st.header('CV Ranking')
    ccvs = st.file_uploader("Upload CVs", type=["pdf", "docx"], accept_multiple_files=True)
    if st.button("Rank CVs"):
        data = {
            "ccvs": [cv.read() for cv in ccvs]  
        }
        response = send_data_to_backend("rank_cvs", data)
        if response['ranked_cvs']:
            st.write("Ranked CVs:")
            for rank, cv in enumerate(response['ranked_cvs'], 1):
                st.write(f"{rank}. {cv}")
        else:
            st.write("No CVs uploaded.")
            

def email_notification():
    st.header("Email Notifications")
    recipient_email = st.text_input("Recipient Email")
    email_subject = st.text_input("Email Subject")
    email_message = st.text_area("Email Message")
    if st.button("Send Email"):
        email_data = {"to": recipient_email, "subject": email_subject, "message": email_message}
        email_result = send_data_to_backend("send_email", email_data)
        st.write(email_result["message"])

def Shortlist_Candidates():
    st.header("Shortlist Candidates")
    ranked_candidates = process_cvs(st.session_state.cvs)
    shortlisted_candidates = st.multiselect("Select candidates to shortlist:", ranked_candidates)
    if st.button("Shortlist Candidates"):
        email_notification(shortlisted_candidates)
        st.success("Emails sent to shortlisted candidates.")


def Screening():
    st.title("Screening Questions")

    st.header("Candidate ID")
    candidate_id = st.text_input("Enter Candidate ID")


    st.header("Screening Questions")


    questions = [
        {"question": "Tell us about your relevant experience.", "importance": "High"},
        {"question": "How do you handle challenges in a team setting?", "importance": "Medium"},
        {"question": "Describe a situation where you demonstrated leadership skills.", "importance": "High"},
        {"question": "What interests you most about this role?", "importance": "Low"},
        ]

    
    for i, q in enumerate(questions, start=1):
        st.subheader(f"Question {i} ({q['importance']} Importance):")
        st.write(q["question"])
        response = st.text_area(f"Response for Question {i}", key=f"response_{i}")



def interview():
    st.title("First-Round Interview")
    st.header("Candidate ID")
    candidate_id = st.text_input("Enter Candidate ID")
    st.header("Interview Questions")
    interview_questions = [
        "Tell us about your work experience.",
        "How do you handle challenging situations in a team?",
        "What technical skills do you bring to this role?",
        ]   
    candidate_responses = []
    for i, question in enumerate(interview_questions, start=1):
        st.subheader(f"Question {i}:")
        st.write(question)
        response = st.text_area(f"Response for Question {i}", key=f"response_{i}")
        candidate_responses.append(response)

    if st.button("Submit Interview"):
        data = {
            "candidate_id": candidate_id,
            "interview_questions": interview_questions,
            "candidate_responses": candidate_responses
            }
        response = requests.post("http://127.0.0.1:5000/submit_interview", json=data)

    if response.status_code == 201:
        st.success("Interview data submitted successfully!")
        interview_performance = response.json()["interview_performance"]
        st.write(f"Interview Performance: {interview_performance}")
    else:
        st.error("Interview data submission failed. Please check your input and try again.")



def communication():
    st.header("HR Communication")
    hr_subject = st.text_input("HR Notification Subject")
    hr_message = st.text_area("HR Notification Message")
    if st.button("Notify HR"):
        hr_notification_data = {"subject": hr_subject, "message": hr_message}
        hr_notification_result = send_data_to_backend("notify_hr", hr_notification_data)
        st.write(hr_notification_result["message"])
    

if __name__ == '__main__':
    main()
