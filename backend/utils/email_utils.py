import os
from flask import current_app
from flask_mail import Message

def send_booking_confirmation_email(username, user_email, service_name, provider_name, booking_date, booking_id, time_slot=None, booking_charge=None):
    """
    Send a confirmation email to the user after they book a service.
    
    Args:
        username (str): The user's name
        user_email (str): The user's email address
        service_name (str): The name of the service booked
        provider_name (str): The name of the service provider
        booking_date (str): The date of the booking
        booking_id (str): The booking ID
        time_slot (str, optional): The time slot for the booking
        booking_charge (float, optional): The total charge for the booking
    
    Returns:
        bool: True if email sent successfully, else False
    """
    try:
        # Create message
        msg = Message(
            subject="Service Booking Confirmation – Local Community Service Platform",
            sender=os.getenv('MAIL_USERNAME', 'your-email@gmail.com'),
            recipients=[user_email]
        )
        
        # Create email body with additional details
        email_body = f"""Hello {username},

Your service booking has been successfully registered on the Local Community Service Platform.

Here are your booking details:

• Service Name: {service_name}
• Provider: {provider_name}
• Booking Date: {booking_date}
• Booking ID: {booking_id}
• Status: Confirmed"""
        
        # Add time slot if provided
        if time_slot:
            email_body += f"\n• Time Slot: {time_slot}"
        
        # Add booking charge if provided
        if booking_charge is not None:
            email_body += f"\n• Total Charge: ₹{booking_charge:.2f}"
        
        email_body += """

Our service provider will contact you shortly with the next steps.

Thank you for choosing our platform!

Regards,
Local Community Service Platform"""
        
        msg.body = email_body
        
        # Send email using Flask-Mail
        mail = current_app.extensions['mail']
        mail.send(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def send_booking_status_update_email(username, user_email, service_name, provider_name, booking_date, booking_id, time_slot, new_status, reason=None):
    """
    Send a status update email to the user when their booking status changes.
    
    Args:
        username (str): The user's name
        user_email (str): The user's email address
        service_name (str): The name of the service booked
        provider_name (str): The name of the service provider
        booking_date (str): The date of the booking
        booking_id (str): The booking ID
        time_slot (str): The time slot for the booking
        new_status (str): The new status of the booking
        reason (str, optional): Reason for status change (for cancellations)
    
    Returns:
        bool: True if email sent successfully, else False
    """
    try:
        # Determine subject based on status
        if new_status == 'Approved':
            subject = "Booking Approved – Local Community Service Platform"
        elif new_status == 'Cancelled':
            subject = "Booking Cancelled – Local Community Service Platform"
        else:
            subject = f"Booking Status Updated – Local Community Service Platform"
        
        # Create message
        msg = Message(
            subject=subject,
            sender=os.getenv('MAIL_USERNAME', 'your-email@gmail.com'),
            recipients=[user_email]
        )
        
        # Create email body
        email_body = f"""Hello {username},

The status of your service booking has been updated on the Local Community Service Platform.

Here are your booking details:

• Service Name: {service_name}
• Provider: {provider_name}
• Booking Date: {booking_date}
• Time Slot: {time_slot}
• Booking ID: {booking_id}
• New Status: {new_status}"""
        
        # Add reason if provided (especially for cancellations)
        if reason:
            email_body += f"\n• Reason: {reason}"
        
        # Add appropriate message based on status
        if new_status == 'Approved':
            email_body += """

Great news! Your booking has been approved by the administrator. The service provider will contact you shortly to confirm the details and proceed with the service.

If you have any questions, please don't hesitate to reach out to us.

Thank you for choosing our platform!
"""
        elif new_status == 'Cancelled':
            email_body += """

We regret to inform you that your booking has been cancelled by the administrator.

If you have any questions or would like to book another service, please don't hesitate to reach out to us.

Thank you for your understanding.
"""
        else:
            email_body += f"""

Your booking status has been updated to: {new_status}

If you have any questions about this update, please don't hesitate to reach out to us.

Thank you for choosing our platform!
"""
        
        email_body += """
Regards,
Local Community Service Platform"""
        
        msg.body = email_body
        
        # Send email using Flask-Mail
        mail = current_app.extensions['mail']
        mail.send(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False