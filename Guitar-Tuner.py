import copy
import os
import numpy as np
import scipy.fftpack
import sounddevice as sd
import time


#THE BELOW CODE IS PART OF A COMMON PITCH DETECTION ALGORITHM IMPLEMENTATION (HARMONIC PRODUCT SPECTRUMS or HPS)
#IT ALLOWS THE COMPUTER TO CONVERT SOUND WAVES INTO A NUMERICAL FREQUENCY.
#NOT STUDENT DEVELOPED.
#THIS SPECIFIC IMPLEMENTATION WAS DONE BY A USER NAMED Chciken
#THE FUNCTIONALITY TO CUSTOMIZE THESE VARIABLES WAS STUDENT DEVELOPED
# General user settings
SAMPLE_FREQUENCY = 48000  # sample frequency in Hz
WINDOW_SIZE = 48000  # window size of the DFT in samples
WINDOW_STEP = 10000  # step size of window
MAX_HPS = 10  # max number of harmonic product spectrums
POWER_THRESH = 1e-5  # tuning is activated if the signal power exceeds this threshold

WINDOW_T_LEN = WINDOW_SIZE / SAMPLE_FREQUENCY  # length of the window in seconds
SAMPLE_T_LENGTH = 1 / SAMPLE_FREQUENCY  # length between two samples in seconds
DELTA_FREQ = SAMPLE_FREQUENCY / WINDOW_SIZE  # frequency step width of the interpolated DFT

HANN_WINDOW = np.hanning(WINDOW_SIZE)


#THE FOLLOWING CODE IS STUDENT DEVELOPED
#USING A ITERATIVE METHOD THAT CHECKS EACH STRING AFTER THE PREVIOUS HAS BEEN TUNED.

GUITAR_NOTE_FREQUENCIES = [330, 247, 196, 147, 110, 82, 0]
GUITAR_STRING_NAMES = ['E4', 'B3', 'G3', 'D3', 'A3', 'E2', '0']
noteIndexer = 0


def find_tuning_direction(current_frequency, goal_frequency):
    global noteIndexer
    if goal_frequency == 0:
        return "Your Guitar has been Tuned! Have a nice day!"
    elif current_frequency - goal_frequency < -0.5:
        result = "Tune Up!"
    elif current_frequency - goal_frequency > 0.5:
        result = "Tune Down!"
    else:
        result = "Successfully Tuned!"
        noteIndexer += 1
    return result

def main_tuner_loop(indata, frames, time, status):

# THE FIRST PART OF THIS LOOP USES THE PITCH DETECTION ALGORITHM TO GET THE PITCH
# AND IS NOT PART OF THE STUDENT DEVELOPED SECTION
    # define static variables
    if not hasattr(main_tuner_loop, "window_samples"):
        main_tuner_loop.window_samples = [0 for _ in range(WINDOW_SIZE)]
    if not hasattr(main_tuner_loop, "noteBuffer"):
        main_tuner_loop.noteBuffer = ["1", "2"]

    if status:
        print(status)
        return
    if any(indata):
        main_tuner_loop.window_samples = np.concatenate((main_tuner_loop.window_samples, indata[:, 0]))  # append new sound sample
        main_tuner_loop.window_samples = main_tuner_loop.window_samples[len(indata[:, 0]):]  # remove old sound sample

        # If the Signal Power is too Low, then Skip The Signal (NOT STUDENT DEVELOPED)
        signal_power = (np.linalg.norm(main_tuner_loop.window_samples, ord=2) ** 2) / len(main_tuner_loop.window_samples)
        if signal_power < POWER_THRESH:
            os.system('cls' if os.name == 'nt' else 'clear')
            return

        # Algorithmic filtering (NOT STUDENT DEVELOPED)
        hann_samples = main_tuner_loop.window_samples * HANN_WINDOW
        magnitude_spec = abs(scipy.fftpack.fft(hann_samples)[:len(hann_samples) // 2])

        # Supress Hum (NOT STUDENT DEVELOPED)
        for i in range(int(60 / DELTA_FREQ)):
            magnitude_spec[i] = 0


        # interpolate spectrum (NOT STUDENT DEVELOPED)
        mag_spec_ipol = np.interp(np.arange(0, len(magnitude_spec), 1 / MAX_HPS), np.arange(0, len(magnitude_spec)),
                                  magnitude_spec)
        mag_spec_ipol = mag_spec_ipol / np.linalg.norm(mag_spec_ipol, ord=2)  # normalize it

        hps_spec = copy.deepcopy(mag_spec_ipol)

        # calculate the HPS (NOT STUDENT DEVELOPED)
        for i in range(MAX_HPS):
            tmp_hps_spec = np.multiply(hps_spec[:int(np.ceil(len(mag_spec_ipol) / (i + 1)))], mag_spec_ipol[::(i + 1)])
            if not any(tmp_hps_spec):
                break
            hps_spec = tmp_hps_spec

        max_ind = np.argmax(hps_spec)
        max_freq = max_ind * (SAMPLE_FREQUENCY / WINDOW_SIZE) / MAX_HPS
        max_freq = round(max_freq, 1)

        main_tuner_loop.noteBuffer.insert(0, max_freq)  # note that this is a ringbuffer
        main_tuner_loop.noteBuffer.pop()

# THE NEXT SECTION DEALS WITH THE ADDED FUNCTIONALITY OF TUNING STRING BY STRING (STUDENT DEVELOPED)
        os.system('cls' if os.name == 'nt' else 'clear')
        if main_tuner_loop.noteBuffer.count(main_tuner_loop.noteBuffer[0]) == len(main_tuner_loop.noteBuffer):
            global noteIndexer
            desired_frequency = float(GUITAR_NOTE_FREQUENCIES[noteIndexer])
            current_string = GUITAR_STRING_NAMES[noteIndexer]
            print()
            print(f"Tuning the {current_string} string: {max_freq}/{desired_frequency}")
            print(find_tuning_direction(max_freq, desired_frequency))
    else:
        print('no input')


# MENU (STUDENT DEVELOPED)
try:
    print("Hello! Welcome to this Guitar Tuner!")

    while True:
        print("\nTo Begin Tuning Your Guitar, Enter 1.")
        print("To Customize the Power Threshold, Enter 2.")
        print("To View the Credits, Enter 3.")
        choice = input("> ")

        if choice == '1':
            print("Starting The Guitar Tuner...")
            with sd.InputStream(channels=1, callback=main_tuner_loop, blocksize=WINDOW_STEP, samplerate=SAMPLE_FREQUENCY):
                while True:
                    time.sleep(0.5)
        elif choice == '2':
            while True:
                try:
                    power_threshold = float(input("Enter a number Greater than 0: "))
                    if 0 < power_threshold:
                        POWER_THRESH = power_threshold
                        print("Power threshold set to ", POWER_THRESH)
                        break
                    else:
                        print("Invalid value. Try again!")
                except ValueError:
                    print("Invalid value. Try again!")
        elif choice == '3':
            print("The Pitch Detection Implementation Was Cited from chciken's Pitch Detection Program in Python!")
            print("He Discusses more about the Math Behind This Tuner at: https://www.chciken.com/digital/signal/processing/2020/05/13/guitar-tuner.html#hps")
        else:
            print("Invalid choice. Try again!")
except Exception as exc:
    print(str(exc))
