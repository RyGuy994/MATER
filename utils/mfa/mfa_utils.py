#/src/utils/mfa/mfa_utils.py
from flask import current_app
from models.mfa import MFA
from models.otp import OTP  # Import your OTP model
import pyotp, random, string, uuid
from datetime import datetime, timedelta

def get_user_mfa_methods(user_id):
    session = current_app.config["current_db"].session
    return session.query(MFA).filter_by(user_id=user_id).all()

def add_mfa_method(user_id, mfa_method, mfa_secret):
    session = current_app.config["current_db"].session
    new_mfa = MFA(user_id=user_id, mfa_method=mfa_method, mfa_secret=mfa_secret)
    session.add(new_mfa)
    session.commit()
    return new_mfa

def update_mfa_method(mfa_id, enabled):
    session = current_app.config["current_db"].session
    mfa_method = session.query(MFA).filter_by(id=mfa_id).first()
    if mfa_method:
        mfa_method.enabled = enabled
        session.commit()
        return mfa_method
    return None

def delete_mfa_method(mfa_id):
    session = current_app.config["current_db"].session
    mfa_method = session.query(MFA).filter_by(id=mfa_id).first()
    if mfa_method:
        session.delete(mfa_method)
        session.commit()
        return True
    return False

def verify_mfa_code(user_id, mfa_method, code):
    session = current_app.config["current_db"].session
    mfa = session.query(MFA).filter_by(user_id=user_id, mfa_method=mfa_method).first()
    
    if mfa:
        if mfa_method == "totp":
            return verify_totp_code(mfa.mfa_secret, code)
        elif mfa_method == "email":
            return verify_email_code(user_id, code)  # Call your email verification function here
        elif mfa_method == "sms":
            return verify_sms_code(user_id, code)  # Call your SMS verification function here

    return False

def generate_totp_secret():
    """
    Generates a new TOTP secret using the pyotp library.
    """
    return pyotp.random_base32()

def generate_backup_codes(count=10, length=8):
    """
    Generates a list of backup codes for TOTP.
    """
    return [
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        for _ in range(count)
    ]

def verify_otp(user_id, otp_code):
    """
    Verifies an OTP for the user.
    Args:
        user_id (int): The user's ID.
        otp_code (str): The OTP code to verify.

    Returns:
        bool: True if OTP is valid, False otherwise.
    """
    session = current_app.config["current_db"].session
    try:
        otp_entry = session.query(OTP).filter_by(user_id=user_id, otp_code=otp_code).first()

        # Check if the OTP has expired
        if datetime.utcnow() > otp_entry.expires_at:
            session.delete(otp_entry)
            session.commit()
            # Optional: log that the OTP was expired.
            return False

        # OTP is valid, delete it after verification
        session.delete(otp_entry)
        session.commit()
        # Optional: log successful OTP verification.
        return True
    except Exception as e:
        session.rollback()
        # Optional: log the exception for debugging
        return False
    finally:
        session.close()

def create_otp_entry(user_id, otp_code, expiration_minutes=5):
    """
    Creates a new OTP entry in the database.
    """
    session = current_app.config["current_db"].session
    otp_entry = OTP(
        id=str(uuid.uuid4()),
        user_id=user_id,
        otp_code=otp_code,
        expires_at=datetime.utcnow() + timedelta(minutes=expiration_minutes)
    )
    session.add(otp_entry)
    session.commit()
    return otp_entry

def generate_otp_code(length=6):
    """
    Generates a random OTP code.
    """
    return ''.join(random.choices(string.digits, k=length))

def cleanup_expired_otps():
    """
    Deletes expired OTPs from the database.
    """
    session = current_app.config["current_db"].session
    expired_otps = session.query(OTP).filter(OTP.expires_at < datetime.utcnow()).all()

    for otp_entry in expired_otps:
        session.delete(otp_entry)
    
    session.commit()
    return len(expired_otps)