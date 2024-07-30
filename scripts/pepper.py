# -*- coding: utf-8 -*-

from pattern.en import parse, Sentence, parsetree, lemma
from naoqi import ALProxy
import math
import time
import string
import re
import sys
import os

try:
    sys.path.insert(0, os.getenv('MODIM_HOME')+'/src/GUI')
except Exception as e:
    print "Please set MODIM_HOME environment variable to MODIM folder."
    sys.exit(1)

import ws_client
from ws_client import *


keywords = {
    'hello': "Hello! Welcome to the DIAG!",
    'thank': "You're welcome! I am here if you need more help",
    'hi': "Hi there!",
    'good morning': "Good morning! I hope you have a great day here at the DIAG. Any questions?",
    'good afternoon': "Good afternoon! Looking for any specific information?",
    'good evening': "Good evening! How can I make your visit more pleasant?",
    'how are you': "I'm a robot, so I don't have feelings, but thanks for asking! How can I assist you?",
    'nice to meet you': "Nice to meet you too!",    
    'what time is it': "let me check... -Time displayed-",
    'developed you': "I have been developed by Softbanks Robotics",
    'what are you doing today': "I am helping the guests of this Building to find rooms and services",
    'call 112': "I am calling 112... please wait outside.",
    'where is room b2': "Room B2 is on the first floor on the right.",
    'where is room b101': "Room B101 is on the second floor on the right.",
    'where is room a3': "Room A3 is on the first floor on the left.",
    'where is room a4': "Room A4 is on the first floor on the left.",
    'where is room a5': "Room A5 is on the first floor on the left.",
    'where is room a6': "Room A6 is on the first floor on the left.",
    'where is room a7': "Room A7 is on the first floor on the left.",
    'show me the map': "I can show you the map of the building from here.",
    'how do i go upstairs': "you can take the stairs from this floor on both sides",
    'how do i go downstairs': "you can take the stairs from this floor on both sides",
    'diag open': "DIAG will open at 8AM.",
    'diag close': "DIAG will close at 8PM.",
    'robotics2 start': "Robotics2 is at 6PM on tuesdays and at 10AM on fridays.",
    'robotics1 start': "Robotics1 is at 2PM on mondays and at 4PM on thursdays.",
}

text_corpus = """
    The toilet is located in each floor at the end of both the corridors. 
    The restrooms are located in each floor at the end of both the corridors.
    All the professors offices are located in the second floor.
    Aula Magna is at the second floor on the right.
    The secretary office is here at your left, you can find everything you need.
    There is a parking lot behind the building, but is only for the professors and staff.
    Free wifi is available throughout the venue, the networks name are 'Eduroam' or 'sapienza' and you will only need to log with your institude credentials.
    The stairs are on this floor in both the directions.
    The elevator is on this floor on the right.
    If you need any further assistance, please approach any of our staff members or come to the information desk. 
    The labs are located downstairs on the left.
    I can show you the map of the building from here. 
    Coffee machines are here on the right. 
    If you are hungry you can eat some snacks here on the right.
    If you've lost any items, please report to the security desk for lost and found. 
    If you've lost your wallet or mobile phone, please report to the security desk for lost and found. 
    The security desk is at the main entrance on the left.
    In case of emergency, exits are clearly marked throughout the venue, please follow the signs. 
    Robotics1 is at 2PM on mondays and at 4PM on thursdays.
    Robotics2 is at 6PM on tuesdays and at 10AM on fridays.
    Elective in AI is at 5PM on mondays and at 3PM on thursdays.
    Natural Language Processing is at 8AM on thursdays and at 10AM on fridays at SPV.
    Deep Learning is at 2PM on tuesdays and at 8AM on fridays.
    Vision and Perception is at 1PM on wednesday and at 4PM on fridays.
"""


class Pepper:
    def __init__(
            self, 
            ip = "127.0.0.1", 
            port = 9559):
        
        # Set the IP and port of the robot
        self.ip = ip
        self.port = port

        # Define the proxies
        self.tts_proxy = ALProxy("ALTextToSpeech", ip, port)
        self.posture_proxy = ALProxy("ALRobotPosture", ip, port)
        self.motion_proxy = ALProxy("ALMotion", ip, port)

        # Initialize the posture
        self.posture_proxy.goToPosture("StandInit", 1.0)

        # Set votes file path
        self.votes_file_path = "votes.txt"   

        # Modim WS client
        self.mws = ModimWSClient()
        self.mws.setDemoPathAuto(__file__)  

    
    ###########################
    # ------ MAIN LOOP ------ #
    ###########################

    def run(self):
        
        # Welcome message
        self.mws.run_interaction(self.display_welcome)
        print("Hello, I'm Pepper and I am here to help you ask me anything.")

        while True:
            # Keyboard input
            user_input = raw_input("You: ").strip().lower()

            # Check if the user wants to access the private section
            if user_input.lower() == 'personal access':
                self.password_check()

            # Check if the user wants to check available events
            if user_input.lower() == 'which events can i join?':
                self.main_events()

            # Check if the user wants to leave
            if user_input.lower() == 'bye' or user_input.lower() == 'goodbye':
                self.posture_proxy.goToPosture("StandInit", 1.0)
                self.point_screen()
                self.mws.run_interaction(self.display_survey) 
                self.mws.run_interaction(self.display_survey_2)  

                self.tts_proxy.say("Do you want to know the current avarage grades? (yes/no): ")
                print("Bot: Do you want to know the current avarage grades? (yes/no): ")
                risposta = raw_input("Answer: ").lower()
                if risposta == 'yes':
                    self.compute_avg_score()
                self.tts_proxy.say("Thank you for your time! Goodbye!")
                self.wave_hand_hello()
                self.posture_proxy.goToPosture("StandInit", 1.0)
                break

            # C
            response = self.find_answer(user_input, text_corpus)

            # If the response is not found in the corpus, try to respond to the query
            if response=="Sorry, I can't find an answer to your question.":
                response = self.respond_to_query(user_input)
            self.tts_proxy.say(response)
            
            # Actions based on the response

            if response=="I can show you the map of the building from here.":
                self.posture_proxy.goToPosture("StandInit", 1.0)
                self.point_screen()
                self.mws.run_interaction(self.display_map_complete)
                self.posture_proxy.goToPosture("StandInit", 1.0)
                
            if response=="Coffee machines are here on the right" or response=="If you are hungry you can eat some snacks here on the right" or response=="The elevator is on this floor on the right":
                self.arm_head_direction(dir='L')	
                self.posture_proxy.goToPosture("StandInit", 1.0)

            if response=="Room B2 is on the first floor on the right.":
                self.arm_head_direction(dir='L')	
                self.posture_proxy.goToPosture("StandInit", 1.0)
                self.point_screen()
                self.mws.run_interaction(self.display_map_B2)
                self.posture_proxy.goToPosture("StandInit", 1.0)
            
            if response=="Room B101 is on the second floor on the right.":
                self.arm_head_direction(dir='L')	
                self.posture_proxy.goToPosture("StandInit", 1.0)
                self.point_screen()
                self.mws.run_interaction(self.display_map_B2)
                self.posture_proxy.goToPosture("StandInit", 1.0)

            if response=="Room A3 is on the first floor on the left.":
                self.arm_head_direction(dir='R')	
                self.posture_proxy.goToPosture("StandInit", 1.0)
                self.point_screen()
                self.mws.run_interaction(self.display_map_A3)
                self.posture_proxy.goToPosture("StandInit", 1.0)
            
            if response=="Room A4 is on the first floor on the left.":
                self.arm_head_direction(dir='R')	
                self.posture_proxy.goToPosture("StandInit", 1.0)
                self.point_screen()
                self.mws.run_interaction(self.display_map_A4)
                self.posture_proxy.goToPosture("StandInit", 1.0)
                
            if response=="Room A5 is on the first floor on the left.":
                self.arm_head_direction(dir='R')
                self.posture_proxy.goToPosture("StandInit", 1.0)	
                self.point_screen()
                self.mws.run_interaction(self.display_map_A5)
                self.posture_proxy.goToPosture("StandInit", 1.0)
            
            if response=="Room A6 is on the first floor on the left.":
                self.arm_head_direction(dir='R')	
                self.posture_proxy.goToPosture("StandInit", 1.0)
                self.point_screen()
                self.mws.run_interaction(self.display_map_A6)
                self.posture_proxy.goToPosture("StandInit", 1.0)
            
            if response=="Room A7 is on the first floor on the left.":
                self.arm_head_direction(dir='R')	
                self.posture_proxy.goToPosture("StandInit", 1.0)
                self.point_screen()
                self.mws.run_interaction(self.display_map_A7)
                self.posture_proxy.goToPosture("StandInit", 1.0)

            if response=="The secretary office is here at your left, you can find everything you need" or response=="If you need any further assistance, please approach any of our staff members or come to the information desk" or response=="The security desk is at the main entrance on the left" or response=="The labs are located downstairs on the left":
                self.arm_head_direction(dir='R')	
                self.posture_proxy.goToPosture("StandInit", 1.0)
                
            if response=="Hi there!" or response=="Hello! Welcome to the DIAG!" or response=="Good morning! I hope you have a great day here at the DIAG. Any questions?" or response=="Good afternoon! Looking for any specific information?" or response=="Good evening! How can I make your visit more pleasant?":
                self.wave_hand_hello()	
                self.posture_proxy.goToPosture("StandInit", 1.0)
                
            if response=="You're welcome! I am here if you need more help":
                self.greeting()	
                self.posture_proxy.goToPosture("StandInit", 1.0)
                
            if response=="All the professors offices are located in the second floor":
                self.raise_arm(dir='R')
                self.posture_proxy.goToPosture("StandInit", 1.0)
                
            if response=="Aula Magna is at the second floor on the right":
                self.raise_arm(dir='L')
                self.arm_head_direction(dir='L')
                self.posture_proxy.goToPosture("StandInit", 1.0)
                
            if response=="The toilet is located in each floor at the end of both the corridors" or response=="The restrooms are located in each floor at the end of both the corridors":
                self.arm_head_direction(dir='R')
                self.posture_proxy.goToPosture("StandInit", 1.0)
                self.arm_head_direction(dir='L')
                self.posture_proxy.goToPosture("StandInit", 1.0)
                
            print("Bot: " + response)
    

    ###########################
    # ------ MOVEMENTS ------ #
    ###########################

    # Function to wave hand and say hello
    def wave_hand_hello(self):
        self.motion_proxy.setAngles(
            ["RElbowRoll", "RElbowYaw", "RHand", "RShoulderPitch", "RShoulderRoll", "RWristYaw"],
            [math.radians(38), math.radians(70), 1.0, math.radians(-10), math.radians(-60), math.radians(-22)],
            0.3)
        time.sleep(1)
        self.motion_proxy.setAngles(
            ["RElbowRoll"],
            [math.radians(88)],
            0.3)
        time.sleep(.5)
        self.motion_proxy.setAngles(
            ["RElbowRoll"],
            [math.radians(38)],
            0.3)
        time.sleep(.5)
        self.motion_proxy.setAngles(
            ["RElbowRoll"],
            [math.radians(88)],
            0.3)
        time.sleep(.5)

    # Function to raise arm and look in specific direction
    def arm_head_direction(self, dir='L'):
        if dir == 'R':
            self.motion_proxy.setAngles(
                ["RElbowRoll", "RElbowYaw", "RHand", "RShoulderPitch", "RShoulderRoll", "RWristYaw", "HeadYaw"],
                [math.radians(0.5), math.radians(22), 1.0, math.radians(-30), math.radians(-89.5), math.radians(72), math.radians(-80)],
                0.2)
        elif dir == 'L':
            self.motion_proxy.setAngles(
                ["LElbowRoll", "LElbowYaw", "LHand", "LShoulderPitch", "LShoulderRoll", "LWristYaw", "HeadYaw"],
                [math.radians(-0.5), math.radians(-22), 1.0, math.radians(-30), math.radians(89.5), math.radians(-72), math.radians(80)],
                0.2)
        time.sleep(1)

    # Function to raise arm
    def raise_arm(self, dir='L'):
        if dir == 'R':
            self.motion_proxy.setAngles(
                ["RElbowRoll", "RElbowYaw", "RHand", "RShoulderPitch", "RShoulderRoll", "RWristYaw"],
                [math.radians(35), math.radians(22), 1.0, math.radians(-50), math.radians(-25), math.radians(72)],
                1)
        elif dir == 'L':
            self.motion_proxy.setAngles(
                ["LElbowRoll", "LElbowYaw", "LHand", "LShoulderPitch", "LShoulderRoll", "LWristYaw"],
                [math.radians(-35), math.radians(-22), 1.0, math.radians(-50), math.radians(25), math.radians(-72)],
                1)
        time.sleep(1)

    # Function to point at the screen
    def point_screen(self):
        self.motion_proxy.setAngles(
            ["RElbowRoll", "RElbowYaw", "RHand", "RShoulderPitch", "RShoulderRoll", "RWristYaw"],
            [math.radians(75), math.radians(22), .5, math.radians(50), math.radians(-30), math.radians(72)],
            1)
        time.sleep(1)

    # Function to greet the user
    def greeting(self):
        self.motion_proxy.setAngles(
            ['HipPitch', 'HeadPitch'],
            [math.radians(-59.5), math.radians(15)],
            0.5)
        time.sleep(1)

    ###########################
    # ------- DISPLAY ------- #
    ###########################

    def display_welcome(self):
        im.init()
        response = im.ask(actionname='welcome',timeout=4,audio=True)

    def display_map_complete():
        im.ask(actionname='complete',timeout=4,audio=True)

    def display_map_A3():
        im.ask(actionname='A3',timeout=4,audio=True)

    def display_map_A4():
        im.ask(actionname='A4',timeout=4,audio=True)

    def display_map_A5():
        im.ask(actionname='A5',timeout=4,audio=True)

    def display_map_A6():
        im.ask(actionname='A6',timeout=4,audio=True)

    def display_map_A7():
        im.ask(actionname='A7',timeout=4,audio=True)

    def display_map_B2():
        im.ask(actionname='B2',timeout=4,audio=True)

    def display_map_B101():
        im.ask(actionname='B101',timeout=4,audio=True)

    def display_events_carrer_days():
        a = im.ask(actionname='carrer_days',timeout=4,audio=True)

    def display_events_hri_conference():
        a = im.ask(actionname='hri_conference',timeout=4,audio=True)

    def display_events_robocup():
        a = im.ask(actionname='robocup',timeout=4,audio=True)

    def display_events_seinars_ai():
        a = im.ask(actionname='seminars_ai',timeout=4,audio=True)

    def display_events_seminars_rob():
        a = im.ask(actionname='seminars_rob',timeout=4,audio=True)

    def display_events_startup():
        a = im.ask(actionname='startup',timeout=4,audio=True)

    def display_survey():
        im.ask(actionname='survey',timeout=40,audio=True)

    def display_survey_2():
        vote = im.ask(actionname='survey_2',timeout=40,audio=True)
        try:
            with open('votes.txt', "a") as file:
                file.write(str(vote) + "\n")
        except Exception as e:
            print("An error occurred:", e)



    ###########################
    # ------- SURVEYS ------- #
    ###########################


    def compute_avg_score(self):
        try:
            with open(self.votes_file_path, "r") as file:
                voti = [int(line.strip()) for line in file.readlines()]
            
            if voti:
                media = sum(voti) / len(voti)
                self.tts_proxy.say("The current avarage grades is {:.2f}".format(media))
                print("Bot: The current avarage grades is {:.2f}".format(media))
            else:
                self.tts_proxy.say("No grades to calculate.")
                print("Bot: No grades to calculate.")
        except FileNotFoundError:
            self.tts_proxy.say("No grades to calculate.")
            print("Bot: No grades to calculate.")


    ###########################
    # ------- EVENTS -------- #
    ###########################

    # Function to manage the event registration
    def manage_event(self, evento):
        # Ask the user to enter his name
        self.tts_proxy.say("Enter your name to register for the event " + evento)
        username = raw_input("Enter your name to register for the event " + evento + ": ")
        # Save the username in the file
        with open(evento + ".txt", "a") as file:
            file.write(username + "\n")
        # Confirm the registration
        self.tts_proxy.say("Thanks, " + username + ". You have been registered for the event " + evento)

    # Main events function
    def main_events(self):
        # Available events
        avail_events = {
            "Seminars in AI": self.display_events_seinars_ai, 
            "Seminars in Robotics": self.display_events_seminars_rob, 
            "Carreer Days": self.display_events_carrer_days, 
            "Startups meeting": self.display_events_startup, 
            "RoboCup conference": self.display_events_robocup, 
            "HRI conference": self.display_events_hri_conference
        }
        # Ask the user to choose an event
        self.tts_proxy.say("Here are the available events:")
        for evento in avail_events:
            time.sleep(1)
            self.tts_proxy.say(evento)
        # Ask the user to choose an event
        self.tts_proxy.say("Which event would you like to register for? ")
        evento_scelto = raw_input("Which event would you like to register for? ")
        # Check if the event is available and manage the registration
        if evento_scelto in avail_events:
            self.manage_event(evento_scelto)
            self.posture_proxy.goToPosture("StandInit", 1.0)
            self.point_screen()
            self.mws.run_interaction(avail_events[evento_scelto])
            self.posture_proxy.goToPosture("StandInit", 1.0)
        else:
            self.tts_proxy.say("Sorry, the specified event could not be found.")       
        


    ###########################
    # ------- ACCESS -------- #
    ###########################

    def password_check(self):

        self.tts_proxy.say("you are in the private section, input personal password")
        print("Bot: you are in the private section, input personal password")

        password = raw_input("input password: ")

        if password == "alberorosso":
            self.tts_proxy.say("Access allowed.")
            print("Bot: Access allowed.")
            time.sleep(2)
            
            self.tts_proxy.say("waiting for command...")
            print("Bot: waiting for command...")
            comando = raw_input("Waiting for command: ")

            if comando.lower() == "pulisci media":
                self.tts_proxy.say("I reset the average of the votes")
                print("Bot: I reset the average of the votes")
                with open("voti.txt", "w") as file:
                    file.write("")

            else:
                self.tts_proxy.say("command not recognized.")
                print("Bot: command not recognized.")
        else:
            self.tts_proxy.say("Wrong password. Access denied.")
            print("Bot: Wrong password. Access denied.")
    

    ###########################
    # -------- EXTRA -------- #
    ###########################

    def preprocess_text(self, text):
        text = text.lower()
        text = text.translate(string.maketrans("", ""), string.punctuation)
        return text

    def find_answer(self, question, corpus):
        question = self.preprocess_text(question)
        question_tree = parsetree(question, lemmata=True)
        keywords = [lemma(word.string) for sentence in question_tree for word in sentence.words if word.pos in ['NN', 'NNS', 'VB', 'JJ']]
        
        corpus_sentences = [sentence.strip() for sentence in corpus.split('.') if sentence]
        sentence_scores = {}
        for sentence in corpus_sentences:
            parsed_sentence = parse(sentence, lemmata=True)
            parsed_words = [lemma(word.string) for word in Sentence(parsed_sentence).words]
            score = sum(parsed_words.count(keyword) for keyword in keywords)
            sentence_scores[sentence] = score

        best_sentences = [s for s in sorted(sentence_scores, key=sentence_scores.get, reverse=True) if sentence_scores[s] > 0]
        
        return ' '.join(best_sentences[:1]) if best_sentences else "Sorry, I can't find an answer to your question."


    def respond_to_query(self, query):
        normalized_query = re.sub(r'[^\w\s]', '', query.lower())

        found_keywords = {}

        for keyword in keywords:
            if keyword in normalized_query:
                position = normalized_query.find(keyword)
                found_keywords[position] = keywords[keyword]

        ordered_responses = [found_keywords[key] for key in sorted(found_keywords)]
        if not ordered_responses:
            self.tts_proxy.say("I'm not sure how to answer that. Can you ask something else?")
            return "I'm not sure how to answer that. Can you ask something else?"
        return " ".join(ordered_responses)