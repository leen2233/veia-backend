from lib import db
from datetime import datetime, timedelta
from getpass import getpass

def seed_chat():
    """
    Seeds the database with a sample conversation between two users.
    """
    print("This script will insert a sample conversation into the database.")
    
    # 1. Get or create users
    user1_username = "test"
    user2_username = "user1"

    user1 = db.users.get(username=user1_username)
    user2 = db.users.get(username=user2_username)

    if not user1:
        print(f"User '{user1_username}' not found.")
        password = getpass(f"Enter password for new user '{user1_username}': ")
        user1 = db.users.create(db.User(username=user1_username, email=f"{user1_username}@example.com", password=password))
        print(f"Created user '{user1_username}'")

    if not user2:
        print(f"User '{user2_username}' not found.")
        password = getpass(f"Enter password for new user '{user2_username}': ")
        user2 = db.users.create(db.User(username=user2_username, email=f"{user2_username}@example.com", password=password))
        print(f"Created user '{user2_username}'")

    # 2. Get or create chat
    chat = db.chats.check_exists(user1._id, user2._id)
    if not chat:
        chat = db.chats.create(db.Chat(user1=str(user1._id), user2=str(user2._id)))
        print(f"Created chat between {user1.username} and {user2.username}")
    
    chat_id = str(chat._id)
    user1_id = str(user1._id)
    user2_id = str(user2._id)

    # 3. Create messages
    messages_to_insert = [
        {"sender": user1_id, "text": "Hey, you there?"},
        {"sender": user2_id, "text": "Yep, what's up?"},
        {"sender": user1_id, "text": "Just running into a weird bug and wanted to see if you'd seen anything like it."},
        {"sender": user2_id, "text": "Shoot. I've got a few minutes."},
        {"sender": user1_id, "text": "It's with the WebSocket connection state. Sometimes, when the client reconnects after a brief network drop, the server doesn't seem to recognize the new connection properly. It's like the old session is stuck."},
        {"sender": user2_id, "text": "Hmm, that sounds familiar. Are you cleaning up the connection state properly on disconnect?"},
        {"sender": user1_id, "text": "I thought so. I have a `finally` block in my main handler loop that removes the connection from the active client list."},
        {"sender": user2_id, "text": "Is it possible the `remove_conn` function is erroring out silently? Or maybe the `ConnectionClosed` exception isn't being caught as you expect?"},
        {"sender": user1_id, "text": "That's a good point. I should add some more aggressive logging there to see what's happening. It's just so intermittent, it's a pain to reproduce reliably."},
        {"sender": user2_id, "text": "The joys of async programming, right? You could also implement a heartbeat/ping-pong mechanism to check for dead connections proactively, rather than just relying on the close exception."},
        {"sender": user1_id, "text": "Yeah, I was thinking about that. The `websockets` library has that built-in, I just need to enable it and handle the pings. That's probably the more robust solution."},
        {"sender": user2_id, "text": "Definitely. It saved me a lot of headaches on a previous project. What's the timeout you have set on the connection?"},
        {"sender": user1_id, "text": "I think it's the default. I haven't explicitly set one."},
        {"sender": user2_id, "text": "Check the docs for that. The default might be longer than you think, which could explain the 'stuck' session."},
        {"sender": user1_id, "text": "Will do. Thanks for the pointers, man. Super helpful."},
        {"sender": user2_id, "text": "No problem at all! Glad I could help."},
        {"sender": user1_id, "text": "So, enough about code. Got any plans for the weekend?"},
        {"sender": user2_id, "text": "Not really. Probably just relax, maybe catch up on some shows. The new season of 'The Expanse' just dropped."},
        {"sender": user1_id, "text": "Oh nice! I've been meaning to start that series. I hear it's amazing."},
        {"sender": user2_id, "text": "It's incredible. The first season is a bit of a slow burn, but once it gets going, it's one of the best sci-fi shows ever made. The physics are so realistic."},
        {"sender": user1_id, "text": "You've sold me. I'll add it to the list. I was thinking of going for a hike on Saturday if the weather holds up."},
        {"sender": user2_id, "text": "Where are you thinking of going?"},
        {"sender": user1_id, "text": "Probably up to the national park. There's a trail there with a great view at the summit."},
        {"sender": user2_id, "text": "Sounds awesome. Send pics if you go!"},
        {"sender": user1_id, "text": "Haha, will do. Assuming I make it to the top."},
        {"sender": user2_id, "text": "lol"},
        {"sender": user1_id, "text": "Anyway, I'm gonna go add that logging and look into the heartbeat stuff. Thanks again."},
        {"sender": user2_id, "text": "Anytime. Let me know how it goes."},
        {"sender": user1_id, "text": "Quick update: you were right. The `remove_conn` function was indeed throwing an exception in a specific edge case where the user object on the connection was `None`."},
        {"sender": user2_id, "text": "Aha! Knew it might be something like that. Easy fix?"},
        {"sender": user1_id, "text": "Yep, just added a check to make sure `connection.user` exists before trying to access its properties. The connection is now closing cleanly every time."},
        {"sender": user2_id, "text": "Nice! Glad it was simple."},
        {"sender": user1_id, "text": "Me too. I was not looking forward to a deep dive into the library's source code."},
        {"sender": user2_id, "text": "That's a rabbit hole you want to avoid if at all possible."},
        {"sender": user1_id, "text": "For sure. So, I'm working on the frontend for this now. React."},
        {"sender": user2_id, "text": "Cool. What are you using for state management?"},
        {"sender": user1_id, "text": "Just React Context for now. It's a small app, so I don't think I need Redux or Zustand or anything heavy."},
        {"sender": user2_id, "text": "Yeah, Context is probably fine for a simple chat app. Are you using a component library?"},
        {"sender": user1_id, "text": "Nah, just writing my own CSS. I find it's faster for smaller projects than fighting with a big library like Material-UI."},
        {"sender": user2_id, "text": "I can respect that. Sometimes it's just easier to write it from scratch."},
        {"sender": user1_id, "text": "Exactly. Total control."},
        {"sender": user2_id, "text": "How are you handling the message list virtualization? Or are you just rendering all of them?"},
        {"sender": user1_id, "text": "For now, just rendering all of them, but I know I'll need to add virtualization soon. Once a chat gets a few hundred messages, the performance is going to tank."},
        {"sender": user2_id, "text": "Yeah, `react-window` or `react-virtualized` are great for that. A little tricky to set up with dynamic message heights, but worth it."},
        {"sender": user1_id, "text": "That's on my TODO list for next week. First, just get the basic functionality working."},
        {"sender": user2_id, "text": "The classic MVP approach. I like it."},
        {"sender": user1_id, "text": "It's the only way to stay sane."},
        {"sender": user2_id, "text": "True that. Hey, I gotta run to a meeting. I'll be back online in an hour or so."},
        {"sender": user1_id, "text": "Alright, catch you later."},
        {"sender": user2_id, "text": "I'm back. Meeting was as boring as expected."},
        {"sender": user1_id, "text": "Aren't they all?"},
        {"sender": user2_id, "text": "Pretty much. So, did you see that new trailer for the Dune movie?"},
        {"sender": user1_id, "text": "The one that dropped yesterday? Yeah, it looks epic! The visuals are insane."},
        {"sender": user2_id, "text": "Right? I'm so hyped for it. I hope it's better than the last one."},
        {"sender": user1_id, "text": "I actually liked the last one, but I agree it had some pacing issues."},
        {"sender": user2_id, "text": "This one looks like it's going to be all-out war. Should be good."},
        {"sender": user1_id, "text": "Fingers crossed. Well, I think I've got this WebSocket issue sorted for now. I'm gonna call it a day."},
        {"sender": user2_id, "text": "Alright man. Have a good one."},
        {"sender": user1_id, "text": "You too. Talk to you tomorrow."},
        {"sender": user2_id, "text": "Later."}
    ]

    # 4. Insert messages with sequential timestamps
    now = datetime.now()
    for i, msg_data in enumerate(messages_to_insert):
        message = db.Message(
            chat=chat_id,
            sender=msg_data["sender"],
            text=msg_data["text"],
            time=now - timedelta(minutes=len(messages_to_insert) - i)
        )
        db.messages.create(message)

    print(f"Inserted {len(messages_to_insert)} messages into chat {chat_id}")

if __name__ == "__main__":
    seed_chat()
