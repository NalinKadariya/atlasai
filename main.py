#Imports
import tkinter
import customtkinter as ctk
from PIL import Image
from info import *
import time
import requests
import openai
import whisper
import pyaudio
import threading
import wave
from pathlib import Path
import pygame
from pydub import AudioSegment
import io


pygame.init()

# Variables
login_button = None
signup_button = None
info_label = None
error_label = None
user_openai_key = None
username_entry = None
password_entry = None
login_label = None
recording = False
frames = []



# recording buttons
start_recording_button = None
stop_recording_button = None


# Main window
root = ctk.CTk() # Create window object
root.geometry(f'{Window_Width}x{Window_Height}') # Geometry of the window
root.resizable(False, False) # Disable resizing of the window
root.title(app_title) # Title of the window
root.iconbitmap(app_icon) # Icon of the window

ctk.set_appearance_mode('dark') # Set the appearance mode to dark
ctk.set_default_color_theme("dark-blue") # Set the default color theme to dark-blue

# Validators
def validate_username(username):
    # Check if the username is not empty
    return len(username.strip()) > 0

def validate_password(password):
    # Check if the password has at least 6 characters
    return len(password) >= 6

def generate_response(text_):
    try:
        # Generate response
        completion = openai.chat.completions.create(
             model="gpt-3.5-turbo",
             messages=[
             {"role": "system", "content": "You are a helpful assistant, with the name: Atlas. You were created by: Nalin Kadariya, Powered by openai. Answer shortly, and precisely with full sentences. Dont make the answer too long."},
             {"role": "user", "content": text_}
    ]
    )
        return completion.choices[0].message.content # Return the response content
    except Exception as e:
        return f"Invalid API key." 

def update_gui_during_recording():
    global recording
    while recording:
        root.update()

def start_recording():
    global recording, frames
    print("Recording started")

    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    frames = []
    recording = True

    # Start a separate thread to update the GUI during recording
    gui_update_thread = threading.Thread(target=update_gui_during_recording)
    gui_update_thread.start()

    # Disable the start recording button and enable the stop recording button
    start_recording_button.configure(state="disabled")
    stop_recording_button.configure(state="normal")
    while recording:
        data = stream.read(1024)
        frames.append(data)
        root.update()

    # Stop the GUI update thread
    gui_update_thread.join()

def text_to_speech(text):
    global start_recording_button

    try:
        response = openai.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )

        # Convert the binary response content to an AudioSegment
        audio_data = AudioSegment.from_file(io.BytesIO(response.content))

        # Play the generated audio
        pygame.mixer.music.load(io.BytesIO(response.content))
        pygame.mixer.music.set_volume(1)
        pygame.mixer.music.play()

    except Exception as e:
        print(f"Error during text-to-speech: {e}")
        error_screen("Error during text-to-speech", 0.5, 0.8, "red")

    finally:
        # Enable the start recording button regardless of success or failure
        start_recording_button.configure(state="normal")



def stop_recording():
    global recording, stop_recording_button, start_recording_button, frames
    if recording:
        try:
            recording = False
            pyaudio.PyAudio().terminate()
            print("Recording stopped")
            stop_recording_button.configure(state="disabled")

            # Save the recorded audio to a file (you can choose a different format based on your requirements)
            wf = wave.open("recorded_audio.wav", 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(frames))
            wf.close()
            print("Audio saved to recorded_audio.wav")
            # Transcribe the recorded audio using whisper
            model = whisper.load_model("base")
            print("Transcribing the audio...")
            result = model.transcribe("recorded_audio.wav")
            transcription_text = result["text"]
            print(f"Transcription: {transcription_text}")
            # Clear the audio data after transcription
            frames = []

            answer = generate_response(transcription_text)
            # Generate a response using the transcribed text
            if answer == "Invalid API key.":
                error_screen("Invalid API key.", 0.5, 0.8, "red")
            else:
                text_to_speech(answer)
            # Enable the start recording button

        except Exception as e:
            print(f"Error during recording termination: {e}")



def main_menu():
    # Destroy everything
    global user_openai_key, login_button, signup_button, info_label, login_label, username_entry, password_entry, submit_button, error_label, start_recording_button, stop_recording_button
    login_button.destroy()
    signup_button.destroy()
    info_label.destroy()
    login_label.destroy()
    username_entry.destroy()
    password_entry.destroy()
    submit_button.destroy()
    error_label.destroy()
    
    # set the openai key
    openai.api_key = user_openai_key

    # Make a start recording and stop recording button. disable the stop recording button at the start, and record once the start recording button is pressed
    start_recording_button = ctk.CTkButton(master=root,
                                width=50,
                                height=30,
                                border_width=0,
                                corner_radius=8,
                                text="Start Recording",
                                font=ctk.CTkFont(family='Cambria', size=20, weight='bold', underline=0, overstrike=0),
                                anchor='center',
                                command=start_recording
                                )

    start_recording_button.place(relx=0.5, rely=0.4, anchor=tkinter.CENTER) # Place the button in the center of the window

    stop_recording_button = ctk.CTkButton(master=root,
                                width=50,
                                height=30,
                                border_width=0,
                                corner_radius=8,
                                text="Stop Recording",
                                font=ctk.CTkFont(family='Cambria', size=20, weight='bold', underline=0, overstrike=0),
                                anchor='center',
                                command=stop_recording
                                )
    
    stop_recording_button.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER) # Place the button in the center of the window
    stop_recording_button.configure(state="disabled") # Disable the stop recording button

def submit_login(username, password):
    global user_openai_key
    validate_password(password)
    validate_username(username) 

    if validate_username(username) and validate_password(password):
        # Send the username and password to the server
        response = requests.post(f'http://{host}:{port}/login', json={'username': username, 'password': password})

        # Check if the username and password are correct
        if response.status_code == 200:
            if error_label != None:
                error_label.destroy()
            error_screen("Logged in successfully", 0.5, 0.8, "green")
            user_openai_key = response.json().get('openai_key')
            main_menu()
        else:
            # Show error message below the submit button
            if error_label != None:
                error_label.destroy()
            error = response.json().get('error')
            error_screen(error, 0.5, 0.8, "red")
    else:
        # Show error message below the submit button
        if error_label != None:
            error_label.destroy()
        error_screen("Invalid username or password.", 0.5, 0.8, "red")


def splash_screen():
    # Create User Interface for splash screen
    # Logo
    title_x = 0.5
    title_y = 0.4
    title_image = ctk.CTkImage(dark_image=Image.open('IMAGE_TITLE.png'), light_image=Image.open('IMAGE_TITLE.png'), size=(image_size))
    title_label = ctk.CTkLabel(root, text="",image=title_image)
    title_label.place(relx=title_x,rely=title_y, anchor=tkinter.CENTER)

    # Progress bar
    progress = ctk.CTkProgressBar(root, width=250, height=10,orientation='horizontal')
    progress.place(relx=0.5,rely=0.5, anchor=tkinter.CENTER)

    # Animate the progress bar
    progress.set(0)
    progress.start()

    # Update the progress bar until it reaches 98%
    while progress.get() < 0.98:
        root.update()  # Update the Tkinter window

    progress.stop()
    progress.set(1) # Set the progress bar to 100%
    time.sleep(1) # Wait for 1 second
    progress.destroy() # Destroy the progress bar

    sub_title_image = ctk.CTkImage(dark_image=Image.open('IMAGE_SUB.png'), light_image=Image.open('IMAGE_SUB.png'), size=(image_size))
    sub_title_label = ctk.CTkLabel(root, text="",image=sub_title_image)
    sub_x = 0.5
    sub_y = 1.2
    # Animates the sub title label and the logo to move upwards
    while sub_y > 0.8:
        sub_y -= 0.01
        title_y -= 0.005
        sub_title_label.place(relx=sub_x,rely=sub_y, anchor=tkinter.CENTER)
        title_label.place(relx=title_x,rely=title_y, anchor=tkinter.CENTER)
        root.update()

def login_menu():
    # Destroy the login and signup buttons
    global login_button, signup_button, info_label, login_label, username_entry, password_entry, submit_button
    login_button.destroy()
    signup_button.destroy()
    info_label.destroy()

    # Log in text
    login_label = ctk.CTkLabel(root, text="Login Menu", font=ctk.CTkFont(family='Cambria', size=20, weight='bold'))
    login_label.place(relx=0.5, rely=0.3, anchor=tkinter.CENTER)

    # Username input
    username_entry = ctk.CTkEntry(root, width=100, border_width=0, corner_radius=8,
                                  font=ctk.CTkFont(family='Cambria', size=16, weight='bold', underline=0, overstrike=0),
                                  placeholder_text="Username")
    username_entry.place(relx=0.5, rely=0.4, anchor=tkinter.CENTER)

    # Password input
    password_entry = ctk.CTkEntry(root, width=100, border_width=0, corner_radius=8,
                                  font=ctk.CTkFont(family='Cambria', size=16, weight='bold', underline=0, overstrike=0),
                                  placeholder_text="Password", show="*")
    password_entry.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

    # Submit button
    submit_button = ctk.CTkButton(master=root,
                                  width=50,
                                  height=30,
                                  border_width=0,
                                  corner_radius=8,
                                  text="Submit",
                                  font=ctk.CTkFont(family='Cambria', size=20, weight='bold', underline=0, overstrike=0),
                                  anchor='center',
                                  command=lambda: submit_login(username_entry.get(), password_entry.get())
    )
   
    submit_button.place(relx=0.5, rely=0.6, anchor=tkinter.CENTER)  # Place the button in the center of the window

def submit_signup(username, password, openai_key):
    username = str(username)
    password = str(password)
    openai_key = str(openai_key)
    # Check if the username and password are valid, check if gmail doesnt end with @gmail.com
    if validate_username(username) and validate_password(password) and len(openai_key) > 0:
        # Send the username and password to the server
        response = requests.post(f'http://{host}:{port}/signup', json={'username': username, 'password': password, 'openai_key': openai_key})

        # Check if the username and password are correct
        if response.status_code == 201:
            if error_label != None:
                error_label.destroy()
            error_screen("Signed up successfully", 0.5, 0.1, "green")
            print("Redirect to the main menu")
        else:
            # Show error message below the submit button
            if error_label != None:
                error_label.destroy()
            error = response.json().get('error')
            error_screen(error, 0.5, 0.1, "red")
    else:
        # Show error message below the submit button
        if error_label != None:
            error_label.destroy()
        error_screen("Invaild.", 0.5, 0.1, "red")

def signup_menu():
    # Destroy the login and signup buttons
    global login_button, signup_button, info_label
    login_button.destroy()
    signup_button.destroy()
    info_label.destroy()

    # get the user info
    signup_label = ctk.CTkLabel(root, text="Signup Menu", font=ctk.CTkFont(family='Cambria', size=20, weight='bold'))
    signup_label.place(relx=0.5, rely=0.3, anchor=tkinter.CENTER)

    username_entry = ctk.CTkEntry(root, width=100, border_width=0, corner_radius=8,
                                    font=ctk.CTkFont(family='Cambria', size=16, weight='bold', underline=0, overstrike=0),
                                    placeholder_text="Username")
    username_entry.place(relx=0.5, rely=0.4, anchor=tkinter.CENTER)

    password_entry = ctk.CTkEntry(root, width=100, border_width=0, corner_radius=8,
                                    font=ctk.CTkFont(family='Cambria', size=16, weight='bold', underline=0, overstrike=0),
                                    placeholder_text="Password", show="*")
    password_entry.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

    openai_key_entry = ctk.CTkEntry(root, width=100, border_width=0, corner_radius=8,
                                    font=ctk.CTkFont(family='Cambria', size=16, weight='bold', underline=0, overstrike=0),
                                    placeholder_text="OpenAI Key", show="#")
    openai_key_entry.place(relx=0.5, rely=0.6, anchor=tkinter.CENTER)

    # Submit button
    submit_button = ctk.CTkButton(master=root,
                                    width=50,
                                    height=30,
                                    border_width=0,
                                    corner_radius=8,
                                    text="Submit",
                                    font=ctk.CTkFont(family='Cambria', size=20, weight='bold', underline=0, overstrike=0),
                                    anchor='center',
                                    command=lambda: submit_signup(username_entry.get(), password_entry.get(), openai_key_entry.get())
        )
    submit_button.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)  # Place the button in the center of the window

def user_info():
    # Ask for login or signup
    global login_button, signup_button, info_label

    # Text info
    info_label = ctk.CTkLabel(root, text="Login or Signup", font=ctk.CTkFont(family='Cambria', size=20, weight='bold'))
    info_label.place(relx=0.5, rely=0.3, anchor=tkinter.CENTER)

    # Login button
    login_button = ctk.CTkButton(master=root,
                                width=50,
                                height=30,
                                border_width=0,
                                corner_radius=8,
                                text="Login",
                                font=ctk.CTkFont(family='Cambria', size=20, weight='bold', underline=0, overstrike=0),
                                anchor='center',
                                command=login_menu
                                )
    
    login_button.place(relx=0.5, rely=0.4, anchor=tkinter.CENTER) # Place the button in the center of the window

    # Signup button
    signup_button = ctk.CTkButton(master=root,
                                width=50,
                                height=30,
                                border_width=0,
                                corner_radius=8,
                                text="Signup",
                                font=ctk.CTkFont(family='Cambria', size=16, weight='bold', underline=0, overstrike=0),
                                anchor='center',
                                command=signup_menu
                                )
    signup_button.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER) # Place the button in the center of the window

# error screen
def error_screen(error_message,x,y,color):
    # Create text with error message
    global error_label
    error_label = ctk.CTkLabel(root, text=error_message, font=ctk.CTkFont(family='Cambria', size=20, weight='bold'), fg_color=color)
    error_label.place(relx=x, rely=y, anchor=tkinter.CENTER)


# Run the program
if __name__ == "__main__":
    splash_screen()
    user_info()        
    root.mainloop() # Keep the window open