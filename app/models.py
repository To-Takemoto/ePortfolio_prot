from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, password, role, full_name=None, student_number=None, seminar=None):
        self.id = id
        self.username = username
        self.password = password
        self.role = role
        self.full_name = full_name
        self.student_number = student_number
        self.seminar = seminar

class Comment:
    def __init__(self, id, portfolio_id, user_id, content, timestamp):
        self.id = id
        self.portfolio_id = portfolio_id
        self.user_id = user_id
        self.content = content
        self.timestamp = timestamp

class ProgressUpdate:
    def __init__(self, id, portfolio_id, progress_number, content, timestamp):
        self.id = id
        self.portfolio_id = portfolio_id
        self.progress_number = progress_number
        self.content = content
        self.timestamp = timestamp
