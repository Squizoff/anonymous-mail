import socket
import json

SERVER_HOST = 'localhost'
SERVER_PORT = 55555
key_file_path = None
user_email = None

def send_request(request_data):
    global key_file_path, user_email

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        client_socket.send(json.dumps(request_data).encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
        response_data = json.loads(response)

        return response_data

# Example of using the client
if __name__ == "__main__":
    while True:
        print("1. Register a new user")
        print("2. Log in")
        print("3. Send an email")
        print("4. Retrieve emails")
        print("5. Exit")

        choice = input("Select an action: ")

        if choice == '1':
            request_data = {'action': 'REGISTER'}
            response = send_request(request_data)
            print(response['message'])

        elif choice == '2':
            key_file_path = input("Enter the path to your key file: ")
            request_data = {'action': 'LOGIN', 'key_file_path': key_file_path}
            response = send_request(request_data)
            print(response['message'])
            if response['success']:
                user_email = response['message'].split('email: ')[1]

        elif choice == '3':
            if user_email:
                recipient = input("Recipient: ")
                subject = input("Subject: ")
                body = input("Email body: ")
                request_data = {'action': 'SEND', 'sender_email': user_email, 'recipient': recipient, 'subject': subject, 'body': body}
                response = send_request(request_data)
                print(response['message'])
            else:
                print("Please register or log in first.")

        elif choice == '4':
            if user_email:
                request_data = {'action': 'RETRIEVE', 'recipient_email': user_email}
                response = send_request(request_data)
                if response and response['success']:
                    emails = response['message']
                    if emails:
                        print("Emails:")
                        for email in emails:
                            print(f"Sender: {email[1]}")
                            print(f"Subject: {email[3]}")
                            print(f"Body: {email[4]}")
                            print("--------------------------")
                    else:
                        print("You have no emails.")
                else:
                    print("Failed to retrieve emails.")
            else:
                print("Please register or log in first.")

        elif choice == '5':
            print("Exiting the program.")
            break

        else:
            print("Invalid choice. Please try again.")