import pygame
import time
import os
import sys

def play_track(track_path, fade_out_ms=5000):
    try:
        # Initialize pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        
        # Check if the file exists
        if not os.path.exists(track_path):
            print(f"Error: The file '{track_path}' does not exist.")
            return False
        
        print(f"Playing {track_path}...")
        print("Press Ctrl+C to schedule fade-out at the end of the track")
        
        # Load and play the sound
        pygame.mixer.music.load(track_path)
        pygame.mixer.music.play()
        
        # Get the track length
        track_length = pygame.mixer.Sound(track_path).get_length()
        fade_out_start_time = track_length - (fade_out_ms / 1000)
        
        # Wait for the sound to finish or for keyboard interrupt
        while pygame.mixer.music.get_busy():
            try:
                current_pos = pygame.mixer.music.get_pos() / 1000  # Get current position in seconds
                if current_pos >= fade_out_start_time:
                    print("\nTrack is nearing the end. Starting fade-out...")
                    pygame.mixer.music.fadeout(fade_out_ms)
                    time.sleep(fade_out_ms / 1000)  # Wait for fade-out to complete
                    break
                time.sleep(0.1)
            except KeyboardInterrupt:
                # Handle Ctrl+C: schedule fade-out at the end of the track
                print("\nFade-out scheduled for the end of the track...")
                while pygame.mixer.music.get_busy():
                    current_pos = pygame.mixer.music.get_pos() / 1000
                    if current_pos >= fade_out_start_time:
                        print("\nTrack is nearing the end. Starting fade-out...")
                        pygame.mixer.music.fadeout(fade_out_ms)
                        time.sleep(fade_out_ms / 1000)
                        break
                break
        
        print("\nPlayback complete!")
        return True
        
    except Exception as e:
        print(f"Error during playback: {e}")
        return False
        
    finally:
        # Clean up pygame resources
        pygame.mixer.quit()

if __name__ == "__main__":
    # Set the music directory and filename
    music_dir = "../music"
    track_name = "night_sunny.mp3"
    
    # Get current directory and construct full path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    track_path = os.path.join(current_dir, music_dir, track_name)
    
    # Play the first track
    if play_track(track_path):
        # Switch to another track after the first one finishes
        track_name = "night_rainy.mp3"
        track_path = os.path.join(current_dir, music_dir, track_name)
        play_track(track_path)