from flask import request, Blueprint, current_app, flash, redirect, url_for
from blueprints.utilities import delete_attachment_from_storage
from models.serviceattachment import ServiceAttachment


service_attachment_blueprint = Blueprint(
    "service_attachment", __name__, template_folder="../templates"
)


# Route to delete selected attachments
@service_attachment_blueprint.route("/delete_selected_attachments", methods=["POST"])
def delete_selected_attachments():
    try:  # Iterate through selected_attachments, which contains the IDs of selected attachments to delete
        selected_attachments = request.form.getlist("selected_attachments[]")

        service_id = None  # Initialize service_id to None

        for (
            attachment_id
        ) in (
            selected_attachments
        ):  # Retrieve the ServiceAttachment record based on the attachment_id
            attachment = ServiceAttachment.query.get(attachment_id)
            if attachment:
                delete_attachment_from_storage(
                    attachment.attachment_path
                )  # Call a function to delete the associated file from storage
                service_id = attachment.service_id  # stored in service_id
                # Retrieve the service_id associated with the attachment for potential redirection
                current_app.config["current_db"].session.delete(
                    attachment
                )  # Delete the ServiceAttachment record from the database

        current_app.config[
            "current_db"
        ].session.commit()  # Commit the changes to the database after deleting selected attachments
        flash("Selected attachments deleted successfully.", "success")
    except Exception as e:
        # Handle exceptions appropriately (e.g., log the error, display an error message)
        flash("An error occurred during the deletion of attachments.", "error")
        print(f"Error: {e}")

    if service_id is not None:
        # Redirect to the service_edit page with the obtained service_id
        return redirect(url_for("service.service_edit", service_id=service_id))

    else:
        # If service_id is not obtained, redirect to a default page or handle it accordingly
        return redirect("/services/service_all")
