import bcrypt

def gen_pass(password):
    bytes_str = password.encode('utf-8')

    # generate salt
    salt = bcrypt.gensalt()

    # generate hash
    hashed = bcrypt.hashpw(bytes_str, salt)

    print(hashed)
