/** `ha` Hausa, `dje` Zarma, `fr` French. */
export type Language = "ha" | "dje" | "fr";
/** `nadia` (Hausa; `warm` is the same voice), `mouhamad` (Zarma and Hausa), `fr` (French). */
export type Voice = "nadia" | "warm" | "mouhamad" | "fr";
export type SpeechFormat = "wav" | "mp3" | "opus";
/** Audio to send: any of WAV, MP3, M4A/AAC, OGG/Opus, WebM or FLAC, up to 25 MB and 5 minutes. */
export type AudioInput = Blob | ArrayBuffer | ArrayBufferView;

export interface Transcription {
  model: string;
  /** What was said, in lower case, without punctuation. */
  text: string;
  language: string;
  /** The length of the audio sent: what was counted. */
  audio_seconds: number;
}

export interface Translation {
  model: string;
  source: "ha" | "fr";
  target: "ha" | "fr";
  /** The text sent, or what was heard in the audio. */
  source_text: string;
  /** The translation. */
  text: string;
  /** Text requests: the characters translated. */
  characters?: number;
  /** Audio requests: the length of the audio sent. */
  audio_seconds?: number;
  /** With includeAudio: the translation spoken, base64 WAV. */
  audio?: string | null;
}

export interface ConverseTurn {
  model: string;
  persona: string;
  session_id: string | null;
  /** What the person said, as text. */
  heard: string;
  /** The answer, as text. */
  reply: string;
  /** The answer spoken, base64 WAV. */
  audio: string;
  sample_rate: number;
  /** Audio sent plus the reply: what was counted. */
  audio_seconds: number;
}

export interface Usage {
  month_audio_seconds_used: number;
  month_audio_seconds_limit: number;
}

export interface Model {
  id: string;
  task: string;
  endpoint: string;
  scope: string;
  languages: Language[];
  /** `beta` or `research`. */
  status: string;
}

export interface VoiceInfo {
  id: string;
  languages: Language[];
  /** The voice's first language. */
  language: Language;
  description: string;
}
