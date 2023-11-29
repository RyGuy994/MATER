import os
from flask import request

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # allowed file extensions
def allowed_file(filename): # allowed file function
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS # checks the file extention

def delete_attachment_from_storage(attachment_path):
    # Assuming your attachments are stored in a folder named 'attachments'
    attachment_full_path = os.path.join('attachments', attachment_path)
    try:
        # Attempt to delete the file
        os.remove(attachment_full_path)
        print(attachment_full_path)
    except FileNotFoundError:
        # Handle the case where the file does not exist
        pass
    except Exception as e:
        # Handle other exceptions as needed
        print(f"Error deleting attachment: {e}")

def delete_attachment_from_storage(attachment_path):
    # Assuming your attachments are stored in a folder named 'attachments'
    attachment_full_path = os.path.join('attachments', attachment_path)

    try:
        # Attempt to delete the file
        os.remove(attachment_full_path)
        print(attachment_full_path)
    except FileNotFoundError:
        # Handle the case where the file does not exist
        pass
    except Exception as e:
        # Handle other exceptions as needed
        print(f"Error deleting attachment: {e}")

def retrieve_username_jwt():
    jwt = request.cookies.get('access_token')
    decoded_data = jwt.decode(jwt=jwt,
                              key=os.environ.get("SECRET_KEY"),
                              algorithms=["HS256"])
    return decoded_data.get('id')

