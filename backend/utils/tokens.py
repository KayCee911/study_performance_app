from itsdangerous import URLSafeTimedSerializer

SECRET_KEY = "futocsc"  # move to env later

serializer = URLSafeTimedSerializer(SECRET_KEY)


def generate_reset_token(email):
    return serializer.dumps(email, salt="password-reset")


def verify_reset_token(token, expiration=3600):
    try:
        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=expiration
        )
        return email
    except:
        return None