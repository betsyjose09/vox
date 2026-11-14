// Robust AudioRecorder for microphone capture, validation, and 16 kHz mono WAV encoding for speech recognition.
export class AudioRecorder {
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private processor: ScriptProcessorNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private pcmChunks: Float32Array[] = [];
  private isRecording = false;

  private readonly targetHighRate = 48000;

  async start(): Promise<boolean> {
    try {
      this.pcmChunks = [];
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      this.audioContext = new AudioCtx();
      this.source = this.audioContext.createMediaStreamSource(this.mediaStream);
      
      // Buffer size 4096 mono
      this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
      this.processor.onaudioprocess = (e) => {
        if (!this.isRecording) return;
        const inputData = e.inputBuffer.getChannelData(0);
        this.pcmChunks.push(new Float32Array(inputData));
      };

      this.source.connect(this.processor);
      this.processor.connect(this.audioContext.destination);
      this.isRecording = true;
      return true;
    } catch (err) {
      console.error("Microphone access failed:", err);
      return false;
    }
  }

  async stop(): Promise<{
    highQuality: Blob | null;
    lowQuality: Blob | null;
    validation: { ok: boolean; warnings: string[]; errors: string[] };
  }> {
    this.isRecording = false;

    if (this.processor && this.source) {
      try {
        this.processor.disconnect();
        this.source.disconnect();
      } catch (e) {}
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
    }

    if (!this.audioContext || this.pcmChunks.length === 0) {
      return {
        highQuality: null,
        lowQuality: null,
        validation: { ok: false, warnings: [], errors: ["No audio data captured"] }
      };
    }

    const origSampleRate = this.audioContext.sampleRate;
    try {
      await this.audioContext.close();
    } catch (e) {}

    // Merge chunks
    const totalLength = this.pcmChunks.reduce((acc, curr) => acc + curr.length, 0);
    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of this.pcmChunks) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }

    // 1. Validation
    const validation = this.validateAudio(merged, origSampleRate);

    // 2. DC offset removal
    const dcRemoved = this.removeDCOffset(merged);

    // 3. High-pass filter ~80Hz
    const filtered = this.highPassFilter(dcRemoved, origSampleRate);

    // 4. Encode master WAV (native sample rate)
    const highQualityBlob = this.encodeWAV(filtered, origSampleRate);

    // 5. 16 kHz resampled WAV for ASR
    const lowQualityBlob = await this.resampleAndEncode(filtered, origSampleRate, 16000);

    return { highQuality: highQualityBlob, lowQuality: lowQualityBlob, validation };
  }

  private validateAudio(buffer: Float32Array, sampleRate: number): { ok: boolean; warnings: string[]; errors: string[] } {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (buffer.length === 0) {
      errors.push("Empty recording");
      return { ok: false, warnings, errors };
    }

    const durationSec = buffer.length / sampleRate;
    if (durationSec < 0.25) {
      errors.push("Recording too short (< 0.25s)");
      return { ok: false, warnings, errors };
    }

    let sumSq = 0;
    let clipCount = 0;
    for (let i = 0; i < buffer.length; i++) {
      const v = buffer[i];
      sumSq += v * v;
      if (Math.abs(v) >= 0.98) clipCount++;
    }
    const rms = Math.sqrt(sumSq / buffer.length);

    if (rms < 0.002) {
      warnings.push("Low audio volume; please speak closer to microphone");
    }
    if (clipCount > buffer.length * 0.05) {
      warnings.push("High audio clipping detected");
    }

    return { ok: errors.length === 0, warnings, errors };
  }

  private removeDCOffset(buffer: Float32Array): Float32Array {
    let sum = 0;
    for (let i = 0; i < buffer.length; i++) sum += buffer[i];
    const mean = sum / buffer.length;
    if (Math.abs(mean) < 1e-5) return buffer;
    const out = new Float32Array(buffer.length);
    for (let i = 0; i < buffer.length; i++) {
      out[i] = buffer[i] - mean;
    }
    return out;
  }

  private highPassFilter(buffer: Float32Array, sampleRate: number): Float32Array {
    const rc = 1.0 / (2 * Math.PI * 80);
    const dt = 1.0 / sampleRate;
    const alpha = rc / (rc + dt);
    const out = new Float32Array(buffer.length);
    out[0] = buffer[0];
    for (let i = 1; i < buffer.length; i++) {
      out[i] = alpha * (out[i - 1] + buffer[i] - buffer[i - 1]);
    }
    return out;
  }

  private encodeWAV(samples: Float32Array, sampleRate: number): Blob {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);
    const writeString = (offset: number, str: string) => {
      for (let i = 0; i < str.length; i++) {
        view.setUint8(offset + i, str.charCodeAt(i));
      }
    };
    writeString(0, "RIFF");
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(8, "WAVE");
    writeString(12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, "data");
    view.setUint32(40, samples.length * 2, true);

    let offset = 44;
    for (let i = 0; i < samples.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return new Blob([view], { type: "audio/wav" });
  }

  private async resampleAndEncode(buffer: Float32Array, fromRate: number, toRate: number): Promise<Blob> {
    if (fromRate === toRate) {
      return this.encodeWAV(buffer, toRate);
    }
    const targetLength = Math.round(buffer.length * toRate / fromRate);
    const offlineCtx = new OfflineAudioContext(1, targetLength, toRate);
    const audioBuf = offlineCtx.createBuffer(1, buffer.length, fromRate);
    audioBuf.copyToChannel(buffer as any, 0);

    const source = offlineCtx.createBufferSource();
    source.buffer = audioBuf;
    source.connect(offlineCtx.destination);
    source.start(0);

    const resampled = await offlineCtx.startRendering();
    const channelData = resampled.getChannelData(0);
    const resampledData = new Float32Array(channelData.length);
    resampledData.set(channelData);
    return this.encodeWAV(resampledData, toRate);
  }
}

export function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const res = reader.result as string;
      const base64 = res.split(",")[1] || res;
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}
