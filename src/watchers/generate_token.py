# generate_token.py
# Run this script ONCE to generate token.json from gmail_credentials.json
# Place this file in the same folder as gmail_credentials.json

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    creds = None
    token_path = 'token.json'  # Will be created in the current folder

    # The file token.json stores the user's access and refresh tokens.
    
    # If there are no (valid) credentials available, let the user log in.
    
    print("Token generated successfully!")
    print(f"token.json has been created in: {os.path.abspath(token_path)}")
    print("You can now use this token in your gmail_watcher.py script.")

    # Optional: Quick test to verify access
    
        print(f"Test connection failed: {e}")

if __name__ == '__main__':
    main()