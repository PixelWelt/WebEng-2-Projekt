from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)

class Hasher():
    """
    A class to handle password hashing and verification.
    """
    @staticmethod
    def verify_password(plain_password, hashed_password):
        """ Verifies a plain password against a hashed password.
        args:
            plain_password (str): The plain text password to verify.
            hashed_password (str): The hashed password to compare against.
        returns:
            bool: True if the plain password matches the hashed password, False otherwise.
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password):
        """Hashes a plain password using bcrypt.
        args:
            password (str): The plain text password to hash.
        Returns:
            str: The hashed password.
        """
        return pwd_context.hash(password)