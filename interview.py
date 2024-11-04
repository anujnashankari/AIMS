import streamlit as st
import mysql.connector
import hashlib

# Hashing function for passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Connect to MySQL with error handling
def connect_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="anujna@2004", 
            database="interview_schedule"  
        )
    except mysql.connector.Error as err:
        st.error(f"Error connecting to the database: {err}")
        return None

# Execute a query
def execute_query(query, data=None):
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        try:
            if data:
                cursor.execute(query, data)
            else:
                cursor.execute(query)
            connection.commit()
        except mysql.connector.Error as err:
            st.error(f"Error executing query: {err}")
        finally:
            cursor.close()
            connection.close()

# Fetch data from a query
def fetch_query(query, data=None):
    connection = connect_db()
    result = []
    if connection:
        cursor = connection.cursor()
        try:
            if data:
                cursor.execute(query, data)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
        except mysql.connector.Error as err:
            st.error(f"Error fetching data: {err}")
        finally:
            cursor.close()
            connection.close()
    return result

# Candidate login logic (updated to set user_id in session state)
def candidate_login(email, password):
    hashed_password = hash_password(password)
    query = "SELECT candidate_id, name FROM candidates WHERE email = %s AND password = %s"
    data = (email, hashed_password)
    result = fetch_query(query, data)
    if result:
        st.session_state.logged_in = True
        st.session_state.user_type = "Candidate"
        st.session_state.user_id = result[0][0]  # Set user_id (candidate_id) in session state
        st.session_state.user_name = result[0][1]  # Assume name is in the second column
    return result

# Interviewer login logic (updated to set user_id in session state)
def interviewer_login(email, password):
    hashed_password = hash_password(password)
    query = "SELECT interviewer_id, name FROM interviewers WHERE email = %s AND password = %s"
    data = (email, hashed_password)
    result = fetch_query(query, data)
    if result:
        st.session_state.logged_in = True
        st.session_state.user_type = "Interviewer"
        st.session_state.user_id = result[0][0]  # Set user_id (interviewer_id) in session state
        st.session_state.user_name = result[0][1]
    return result

# Registration functions
def candidate_register(name, email, phone, skills, password):
    hashed_password = hash_password(password)
    query = "INSERT INTO candidates (name, email, phone, skills, password) VALUES (%s, %s, %s, %s, %s)"
    data = (name, email, phone, skills, hashed_password)
    execute_query(query, data)

def interviewer_register(name, email, phone, password):
    hashed_password = hash_password(password)
    query = "INSERT INTO interviewers (name, email, phone, password) VALUES (%s, %s, %s, %s)"
    data = (name, email, phone, hashed_password)
    execute_query(query, data)

# Function for candidate to apply for a job
def apply_for_job(job_id, candidate_id):
    query = "INSERT INTO job_applications (job_id, candidate_id, status) VALUES (%s, %s, 'Applied')"
    data = (job_id, candidate_id)
    execute_query(query, data)

# Home Page After Login
def homepage():
    st.title(f"Welcome {st.session_state.user_name}!")

    # Add Logout Button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_type = ""
        st.session_state.user_id = None  # Clear user_id on logout
        st.success("Logged out successfully!")
        
    # Candidate functionality
    if st.session_state.user_type == "Candidate":
        st.subheader("Job Postings")

        # Fetch and display jobs for candidates
        jobs = fetch_query("SELECT job_id, job_title, description, requirements FROM job_postings")
        for job in jobs:
            job_id, title, description, requirements = job
            st.write(f"**Job Title:** {title}")
            st.write(f"**Description:** {description}")
            st.write(f"**Requirements:** {requirements}")

            # Apply button for each job
            if st.button(f"Apply for {title}", key=f"apply_{job_id}"):
                candidate_id = st.session_state.user_id  # Use user_id from session state
                apply_for_job(job_id, candidate_id)
                st.success(f"Applied successfully for {title}!")
            st.write("---")

        # Section to view applied job status
        st.subheader("Your Applied Job Status")
        view_applied_jobs()

def view_applied_jobs():
    # Fetch applied jobs for the logged-in candidate
    query = """
        SELECT job_postings.job_title, job_applications.status, 
               interviews.scheduled_date, interviews.scheduled_time
        FROM job_applications
        JOIN job_postings ON job_applications.job_id = job_postings.job_id
        LEFT JOIN interviews ON job_applications.application_id = interviews.application_id
        WHERE job_applications.candidate_id = %s
    """
    applications = fetch_query(query, (st.session_state.user_id,))
    
    if applications:
        for application in applications:
            job_title, status, scheduled_date, scheduled_time = application
            st.write(f"**Job Title:** {job_title}")
            st.write(f"**Application Status:** {status}")
            if scheduled_date and scheduled_time:
                st.write(f"**Interview Scheduled On:** {scheduled_date} at {scheduled_time}")
            else:
                st.write("**Interview Status:** No interview scheduled.")
            st.write("---")
    else:
        st.write("You have not applied for any jobs yet.")


# Function to display the interviewer's homepage
def interviewer_homepage():
    st.title(f"Welcome {st.session_state.user_name} (Interviewer)!")
    
    # Add Logout Button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_type = ""
        st.session_state.user_id = None  # Clear user_id on logout
        st.success("Logged out successfully!")
        return

    st.subheader("Interviewer Dashboard")
    
    # Section to view job applications
    st.header("Job Applications")
    applications = fetch_query("""
        SELECT ja.application_id, jp.job_title, c.name, ja.status
        FROM job_applications ja
        JOIN job_postings jp ON ja.job_id = jp.job_id
        JOIN candidates c ON ja.candidate_id = c.candidate_id
        WHERE jp.interviewer_id = %s
    """, (st.session_state.user_id,))

    if applications:
        for app in applications:
            application_id, job_title, candidate_name, status = app
            st.write(f"**Job Title:** {job_title}")
            st.write(f"**Candidate Name:** {candidate_name}")
            st.write(f"**Application Status:** {status}")

            # Option to schedule an interview
            if status == "Applied":
                with st.form(f"interview_form_{application_id}"):
                    scheduled_date = st.date_input("Select Interview Date")
                    scheduled_time = st.time_input("Select Interview Time")
                    submit_interview = st.form_submit_button("Schedule Interview")

                    if submit_interview:
                        # Schedule interview in the database
                        query = """
                            INSERT INTO interviews (application_id, scheduled_date, scheduled_time)
                            VALUES (%s, %s, %s)
                        """
                        data = (application_id, scheduled_date, scheduled_time)
                        execute_query(query, data)
                        st.success(f"Interview scheduled for {candidate_name} on {scheduled_date} at {scheduled_time}.")

            st.write("---")
    else:
        st.write("No job applications available for you.")

    # Section to add a new job posting
    st.header("Add Job Posting")
    with st.form("job_posting_form"):
        job_title = st.text_input("Job Title")
        job_description = st.text_area("Job Description")
        job_requirements = st.text_area("Job Requirements")
        submit_job = st.form_submit_button("Add Job Posting")
    
        if submit_job:
            # Insert job posting into the job_postings table
            query = """
                INSERT INTO job_postings (job_title, description, requirements, interviewer_id)
                VALUES (%s, %s, %s, %s)
            """
            data = (job_title, job_description, job_requirements, st.session_state.user_id)
            execute_query(query, data)
            st.success("Job posting added successfully!")

    # Section to view scheduled interviews
    st.header("Scheduled Interviews")
    scheduled_interviews = fetch_query("""
        SELECT i.interview_id, ja.application_id, jp.job_title, c.name, i.scheduled_date, i.scheduled_time
        FROM interviews i
        JOIN job_applications ja ON i.application_id = ja.application_id
        JOIN job_postings jp ON ja.job_id = jp.job_id
        JOIN candidates c ON ja.candidate_id = c.candidate_id
        WHERE jp.interviewer_id = %s
    """, (st.session_state.user_id,))

    if scheduled_interviews:
        for interview in scheduled_interviews:
            interview_id, application_id, job_title, candidate_name, scheduled_date, scheduled_time = interview
            st.write(f"**Interview for Job Title:** {job_title}")
            st.write(f"**Candidate Name:** {candidate_name}")
            st.write(f"**Scheduled Date:** {scheduled_date}")
            st.write(f"**Scheduled Time:** {scheduled_time}")

            # Option to mark interview as completed
            if st.button(f"Mark Interview {interview_id} as Completed"):
                query = "UPDATE job_applications SET status = 'Completed' WHERE application_id = %s"
                execute_query(query, (application_id,))
                st.success(f"Interview for {candidate_name} marked as completed.")
            st.write("---")
    else:
        st.write("No scheduled interviews.")

# Updating the main function to direct to the interviewer's homepage
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_type = ""
        st.session_state.user_id = None  # Initialize user_id

    if st.session_state.logged_in:
        if st.session_state.user_type == "Interviewer":
            interviewer_homepage()
        else:
            homepage()  # Assuming you have a separate homepage function for candidates
    else:
        login_register_page()


# Login and Registration Page
def login_register_page():
    st.sidebar.title("Login/Register")
    user_type = st.sidebar.selectbox("User Type", ["Candidate", "Interviewer"])
    
    tab = st.sidebar.radio("Choose Action", ["Login", "Register"])

    # Centered input form for login/register
    col1, col2, col3 = st.columns([1, 2, 1])  # This centers the form
    with col2:
        if tab == "Login":
            st.header("Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                if user_type == "Candidate":
                    result = candidate_login(email, password)
                    if result:
                        st.success(f"Welcome {st.session_state.user_name}!")
                    else:
                        st.error("Invalid credentials")
                elif user_type == "Interviewer":
                    result = interviewer_login(email, password)
                    if result:
                        st.success(f"Welcome {st.session_state.user_name}!")
                    else:
                        st.error("Invalid credentials")

        elif tab == "Register":
            st.header("Register")
            name = st.text_input("Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            skills = st.text_input("Skills (for Candidates only)", "")
            password = st.text_input("Password", type="password")

            if st.button("Register"):
                if user_type == "Candidate":
                    candidate_register(name, email, phone, skills, password)
                    st.success("Registration successful!")
                elif user_type == "Interviewer":
                    interviewer_register(name, email, phone, password)
                    st.success("Registration successful!")

# Run the app
if __name__ == "__main__":
    main()
