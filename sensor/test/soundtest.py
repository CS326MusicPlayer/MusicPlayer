import pygame
import time
import os
import sys

def play_track(track_path):
    try:
        # Initialize pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        
        # Check if the file exists
        if not os.path.exists(track_path):
            print(f"Error: The file '{track_path}' does not exist.")
            return False
        
        print(f"Playing {track_path}...")
        print("Press Ctrl+C to stop playback")
        
        # Load and play the sound
        pygame.mixer.music.load(track_path)
        pygame.mixer.music.play()
        
        # Wait for the sound to finish or for keyboard interrupt
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        print("\nPlayback complete!")
        return True
        
    except KeyboardInterrupt:
        # Handle Ctrl+C
        pygame.mixer.music.stop()
        print("\nPlayback stopped by user")
        return True
        
    except Exception as e:
        print(f"Error during playback: {e}")
        return False
        
    finally:
        # Clean up pygame resources
        pygame.mixer.quit()

if __name__ == "__main__":
    # Set the music directory and filename
    music_dir = "music"
    track_name = "morning_base.mp3"
    
    # Get current directory and construct full path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    track_path = os.path.join(current_dir, music_dir, track_name)
    
    # Play the track
    play_track(track_path)
