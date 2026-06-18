from tools.gmail_tool import send_email

print("Testing Gmail Tool from the Root folder...")
# Make sure to put your actual email address here!
result = send_email("mohammeddanish.reza1@gmail.com", "Root Test", "The folder structure works perfectly!")
print(result)