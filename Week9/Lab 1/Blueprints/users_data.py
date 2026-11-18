USERS = {
    1: {"first_name": "Văn", "last_name": "Nguyễn", "email": "a@vnu.vn"},
    2: {"first_name": "Trang", "last_name": "Trần", "email": "b@vnu.vn"}}
def get_user(uid): return USERS.get(uid)
def create_user(data):
    uid = max(USERS.keys(), default=0) + 1
    USERS[uid] = {
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "email": data["email"]
    }
    return uid, USERS[uid]