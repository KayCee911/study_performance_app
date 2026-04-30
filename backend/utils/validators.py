from email_validator import validate_email, EmailNotValidError

def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False