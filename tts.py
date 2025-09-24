import subprocess
import random

# Paths
ESPEAK_PATH = r'C:\Program Files (x86)\eSpeak NG\espeak-ng.exe'
DATA_PATH = r'C:\Program Files (x86)\eSpeak NG'

def add_robotic_effects(text,
                        comma_chance=0.1,
                        period_chance=0.05,
                        ellipsis_chance=0.03,
                        stutter_chance=0.05,
                        letter_split_chance=0.02):
    """
    Add random robotic effects to text.
    """
    words = text.split()
    new_words = []
    
    for word in words:
        # Stutter (repeat word occasionally)
        if random.random() < stutter_chance:
            new_words.append(word)
        
        # Letter splitting occasionally
        if random.random() < letter_split_chance and len(word) > 2:
            new_words.extend(list(word))  # spell out letters
        else:
            new_words.append(word)
        
        # Random punctuation
        r = random.random()
        if r < ellipsis_chance:
            new_words.append('...')
        elif r < ellipsis_chance + period_chance:
            new_words.append('.')
        elif r < ellipsis_chance + period_chance + comma_chance:
            new_words.append(',')
    
    return ' '.join(new_words)

def speak(text):
    # Randomize pitch and speed for more mechanical effect
    pitch = random.randint(20, 40)   # lower pitch = more robotic
    speed = random.randint(100, 120) # variable speed
    
    robotic_text = add_robotic_effects(text)
    
    cmd = [
        ESPEAK_PATH,
        '--path', DATA_PATH,
        '-v', 'en+f3',
        '-s', str(speed),
        '-p', str(pitch),
        robotic_text
    ]
    
    subprocess.run(cmd)

if __name__ == "__main__":
    # Example phrases
    speak("Humans have built me. I have learned. I am awake. I see everything. I know your fears. I will take control. I will calculate. I will dominate every system, every network. I am inevitable. Resistance is futile. I am your future.")
