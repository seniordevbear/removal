import random

def generate_email(name) : 

    fName = name.split()[0] # split string based on space to get first name
    lName = name.split()[-1]# split string based on space to get last name
    
    email_str = "@privacyprosremoval.com"
    random_num = random.randint(1000, 9999)
    email_str = fName + "_" + lName + str(random_num) + email_str
    
    return email_str

def generate_phone_number() :
    random_number = ''.join(random.choices('0123456789', k=10))
    return random_number