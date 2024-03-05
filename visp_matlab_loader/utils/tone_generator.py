import random

import numpy as np
from scipy.io.wavfile import write


class ToneGenerator:
    """
    Generates a tone with a given fundamental frequency and harmonics.

    We use it to avoid adding real human speech to the repository.

    We may try a more sophisticated approach in the future.
    """

    def __init__(self, sample_rate=44100, duration=5, base_freq=440, harmonics=(1, 2, 3), seed=0):
        self.sample_rate = sample_rate
        self.duration = duration
        self.base_freq = base_freq
        self.harmonics = harmonics
        self.seed = seed
        random.seed(self.seed)

    def generate_tone(self):
        t = np.linspace(0, self.duration, self.sample_rate * self.duration, False)
        signal = np.sin(2 * np.pi * self.base_freq * t)
        for harmonic in self.harmonics:
            freq = self.base_freq * harmonic
            random_amplitude = random.uniform(0.1, 1.0)
            signal += random_amplitude * np.sin(2 * np.pi * freq * t)
        return signal

    def normalize(self, signal):
        return np.int16((signal / signal.max()) * 32767)

    def save_to_file(self, filename):
        signal = self.generate_tone()
        normalized_signal = self.normalize(signal)
        write(filename, self.sample_rate, normalized_signal)


def main():
    # Fundamental frequency set to 120 Hz, which is within the range of a typical male voice.
    # The harmonics are set to the first three formant frequencies for the 'a' sound.
    generator = ToneGenerator(base_freq=120, harmonics=(730 / 120, 1090 / 120, 2440 / 120), seed=0)
    generator.save_to_file("test_tone.wav")


if __name__ == "__main__":
    main()
