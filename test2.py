

import openai

# transcript = "Okay, so the splintered bone is basically underground, literally. In every sense it is an underground fighting pit. There's an entrance underneath an archway, a brick archway, we're down by the docks, remember? You can sort of smell the very distinctive and not especially pleasant stench of the docks coming in. And as you pass the security and go through the door..."
transcript = "safely at the base of the tree to discover that three figures have joined Prudence if Prudence you just stayed on the top of the ground. Yeah well they do their tree business I'm an indoorsy type. Is your pick me goats England? No not yet I've not summoned any pick me goats yet. Wait so they've just materialised around me or? No they sort of just sort of walked out of the tree line, they're sort of just stood there and are kind of like, they don't seem threatening but there are three figures, one is seemingly a half elf who's wearing robes that make you seem as if they are either very arrogant or perhaps magically inclined. There is a human wearing a sleeveless top with sort of like leather cuffs and there is a tortle which in case anyone is reminding is a massive tortoise person with a double banded war axe just over his shoulder."
# transcript = "Yeah, you rent a carriage and begin the winding journey up into the hills to the east of Volusport to make your way to Castle Wysomshire. Is it misty? Are we talking...? It's not misty at first, but all of a sudden you look around and gosh, where did this mist roll in from? Did you have the time right? It seems to be getting darker than you thought. There's supposed to be a full moon tonight, but the clouds are crowding in front of it. It's all getting a bit dark and scary, and I'll tell you who can tell it's getting dark and scary is the horses. What do you have horses? You have goats. Goats?! Yeah, goats. You've got the big goats that drive... We arrive three weeks later. Mega goats. Your high stamina mountain and hill goats. This is an all-terrain carriage then? Exactly. It's an ATG terrain goat. Well I get all the oil labs going, all the whale oil labs going to try and calm the goats. But as you get closer you start to see Castle Whizzen cheers looming silhouettes."
def send_to_chatgpt(message_list):
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=message_list
    )

    return response['choices'][0]['message']['content']


role_message = "You are a Dungeons & Dragons dungeon master."
message_list = [
            {"role": "system", "content": role_message},
        ]


message_list.append({"role": "user", "content": transcript + "\n\n List some of the characters, locations, and items in this transcription."})
response = send_to_chatgpt(message_list)
print(response)
message_list.append({"role": "assistant", "content": response})


while True:
    the_input = input("Input prompt: ")
    message_list.append({"role": "user", "content": "Describe the " + the_input + "in second person."})
    response = send_to_chatgpt(message_list)

    #remove the last item from the list
    message_list.pop()

    print(response)
    
