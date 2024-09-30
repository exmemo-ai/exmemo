import librosa
import numpy as np
import matplotlib.pyplot as plt


def analysis_audio(path, debug=True):
    """
    Load audio files and compute features such as volume
    """
    audio_data, sample_rate = librosa.load(path)

    volume = np.abs(audio_data)
    base_length = len(volume)

    if debug:
        print("length", round(len(volume) / sample_rate, 1))
        print("frame", len(volume))
        print("p50", round(np.percentile(volume, 50), 3), round(np.mean(volume), 3))

    volume = volume[
        volume > np.percentile(volume, 10)
    ]  # Remove parts with volume lower than 10%
    if debug:
        print(
            "remove 10 percentile，frame",
            len(volume),
            round(len(volume) / base_length, 3),
        )
        print("p50", round(np.percentile(volume, 50), 3), round(np.mean(volume), 3))
        print("\n")
    return np.mean(volume), volume


# analysis_audio('/tmp/谢彦_new.mp3')


def test_volume():
    m_xunfei, v_xunfei = analysis_audio("/tmp/test_xunfei.mp3")
    m_nan1, v_nan1 = analysis_audio("/tmp/test_nan1.mp3")
    print("base", m_xunfei)
    plt.hist(v_nan1, bins=100, range=(0, 0.2), density=True)
    plt.hist(v_xunfei, bins=100, range=(0, 0.2), density=True, alpha=0.5)
    plt.show()


# test_volume()
