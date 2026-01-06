using System;
using System.Linq;
using NAudio.Wave;
using ProjectMaelstrom.Models;

namespace ProjectMaelstrom.Utilities;

/// <summary>
/// Lightweight audio recognizer that listens to system audio (loopback) and emits coarse cues for SmartPlay.
/// This uses simple amplitude-based detection; it can be expanded to frequency-based templates as we gather data.
/// </summary>
internal sealed class AudioRecognizer : IDisposable
{
    public event Action<GameAudioCue>? CueDetected;

    private WasapiLoopbackCapture? _loopback;
    private WaveInEvent? _waveIn;
    private readonly object _lock = new();
    private bool _started;
    private bool _disposing;
    private DateTime _lastCueUtc = DateTime.MinValue;

    // Tunables
    // Baseline/filters to ignore background music hum.
    private const double AbsoluteThreshold = 0.12; // hard floor to ignore very low ambience
    private readonly double _transientDelta;    // how much the window peak must exceed the running baseline
    private const double BaselineDecay = 0.90;     // exponential decay for baseline (closer to 1 = slower)
    private static readonly TimeSpan CueCooldown = TimeSpan.FromSeconds(2);
    private double _baseline = 0;

    public AudioRecognizer(double? transientDelta = null)
    {
        _transientDelta = transientDelta.HasValue
            ? Math.Clamp(transientDelta.Value, 0.05, 0.5)
            : 0.12;
    }

    public void Start()
    {
        lock (_lock)
        {
            if (_started) return;
            _started = true;

            try
            {
                _loopback = new WasapiLoopbackCapture();
                _loopback.DataAvailable += OnDataAvailable;
                _loopback.RecordingStopped += OnStopped;
                _loopback.StartRecording();
                Logger.Log("[AudioRecognizer] Started WASAPI loopback capture.");
                return;
            }
            catch (Exception ex)
            {
                Logger.LogError("[AudioRecognizer] Loopback capture unavailable, falling back to WaveIn", ex);
            }

            try
            {
                _waveIn = new WaveInEvent
                {
                    WaveFormat = new WaveFormat(44100, 16, 1)
                };
                _waveIn.DataAvailable += OnDataAvailable;
                _waveIn.RecordingStopped += OnStopped;
                _waveIn.StartRecording();
                Logger.Log("[AudioRecognizer] Started microphone capture (WaveIn).");
            }
            catch (Exception ex)
            {
                Logger.LogError("[AudioRecognizer] Unable to start any audio capture device", ex);
                _started = false;
            }
        }
    }

    public void Stop()
    {
        lock (_lock)
        {
            if (!_started) return;
            _started = false;
            try { _loopback?.StopRecording(); } catch { }
            try { _waveIn?.StopRecording(); } catch { }
        }
    }

    private void OnDataAvailable(object? sender, WaveInEventArgs e)
    {
        if (_disposing) return;
        if (e?.Buffer == null || e.BytesRecorded == 0) return;

        // Convert 16-bit PCM samples to normalized amplitude
        double max = 0;
        for (int i = 0; i < e.BytesRecorded; i += 2)
        {
            short sample = (short)(e.Buffer[i] | (e.Buffer[i + 1] << 8));
            double norm = Math.Abs(sample / 32768.0);
            if (norm > max) max = norm;
        }

        // Update baseline (exponential moving average) to model background music bed.
        _baseline = (_baseline * BaselineDecay) + (max * (1 - BaselineDecay));

        var dynamicThreshold = Math.Max(AbsoluteThreshold, _baseline + _transientDelta);

        if (max >= dynamicThreshold)
        {
            var now = DateTime.UtcNow;
            if (now - _lastCueUtc < CueCooldown) return;
            _lastCueUtc = now;

            CueDetected?.Invoke(new GameAudioCue
            {
                Type = "audio_peak",
                Confidence = Math.Min(1.0, max),
                CapturedUtc = now,
                Metadata = $"peak={max:0.000};baseline={_baseline:0.000};threshold={dynamicThreshold:0.000}"
            });
        }
    }

    private void OnStopped(object? sender, StoppedEventArgs e)
    {
        if (_disposing) return;
        if (e.Exception != null)
        {
            Logger.LogError("[AudioRecognizer] Capture stopped with error", e.Exception);
        }
    }

    public void Dispose()
    {
        _disposing = true;
        Stop();
        _loopback?.Dispose();
        _waveIn?.Dispose();
        _loopback = null;
        _waveIn = null;
    }
}
