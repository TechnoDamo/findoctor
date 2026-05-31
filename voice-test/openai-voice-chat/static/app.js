const messages = document.getElementById("messages");
const input = document.getElementById("input");
const send = document.getElementById("send");
const record = document.getElementById("record");
const statusEl = document.getElementById("status");
const voiceMode = document.getElementById("voiceMode");

let config = null;
let conversationId = null;
let recording = false;
let audioContext = null;
let source = null;
let processor = null;
let mediaStream = null;
let chunks = [];
let sampleRate = 48000;

function addMessage(role, text, meta = "") {
  const node = document.createElement("div");
  node.className = `message ${role}`;
  if (meta) {
    const metaNode = document.createElement("div");
    metaNode.className = "meta";
    metaNode.textContent = meta;
    node.appendChild(metaNode);
  }
  const body = document.createElement("div");
  body.textContent = text;
  node.appendChild(body);
  messages.appendChild(node);
  messages.scrollTop = messages.scrollHeight;
  return body;
}

function addAudio(url) {
  const audio = document.createElement("audio");
  audio.controls = true;
  audio.autoplay = true;
  audio.src = url;
  messages.lastElementChild?.appendChild(audio);
}

async function loadConfig() {
  config = await fetch("/config").then((response) => response.json());
  statusEl.textContent = config.hasApiKey
    ? `LLM ${config.defaults.llm} · STT ${config.defaults.stt} · TTS ${config.defaults.tts}`
    : "API key missing";
}

async function sendText() {
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  addMessage("user", text);
  const assistantBody = addMessage("assistant", "", "streaming");

  const response = await fetch("/ai/chat/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      conversationId,
      input: [{ type: "text", text }],
      responseModalities: ["text"],
    }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    assistantBody.textContent += decoder.decode(value, { stream: true });
    messages.scrollTop = messages.scrollHeight;
  }
}

async function startRecording() {
  mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  chunks = [];
  audioContext = new AudioContext();
  sampleRate = audioContext.sampleRate;
  source = audioContext.createMediaStreamSource(mediaStream);
  processor = audioContext.createScriptProcessor(4096, 1, 1);
  processor.onaudioprocess = (event) => {
    chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
  };
  source.connect(processor);
  processor.connect(audioContext.destination);
  recording = true;
  record.textContent = "Stop";
  record.classList.add("recording");
}

async function stopRecording() {
  processor.disconnect();
  source.disconnect();
  mediaStream.getTracks().forEach((track) => track.stop());
  await audioContext.close();
  const wav = encodeWav(mergeChunks(chunks), sampleRate);
  await sendAudio(wav);
  recording = false;
  record.textContent = "Record";
  record.classList.remove("recording");
}

function mergeChunks(items) {
  const length = items.reduce((sum, item) => sum + item.length, 0);
  const merged = new Float32Array(length);
  let offset = 0;
  for (const item of items) {
    merged.set(item, offset);
    offset += item.length;
  }
  return merged;
}

function encodeWav(samples, rate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeString = (offset, value) => {
    for (let i = 0; i < value.length; i += 1) view.setUint8(offset + i, value.charCodeAt(i));
  };
  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, rate, true);
  view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, samples.length * 2, true);
  let offset = 44;
  for (const item of samples) {
    const sample = Math.max(-1, Math.min(1, item));
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
    offset += 2;
  }
  return new Blob([view], { type: "audio/wav" });
}

async function sendAudio(blob) {
  addMessage("user", "Voice message");
  const form = new FormData();
  form.append("audio", blob, "voice.wav");
  form.append("audioFormat", "wav");
  form.append("responseModalities", "text");
  form.append("responseModalities", "audio");

  const response = await fetch("/ai/chat/audio", {
    method: "POST",
    body: form,
  });
  const data = await response.json();
  conversationId = data.conversationId || conversationId;
  addMessage("assistant", data.output.text || "", data.output.transcript ? `transcript: ${data.output.transcript}` : "");
  if (data.output.audio?.url) {
    addAudio(data.output.audio.url);
  }
}

send.addEventListener("click", sendText);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendText();
  }
});
record.addEventListener("click", () => {
  if (recording) stopRecording();
  else startRecording();
});
voiceMode.addEventListener("click", () => {
  document.body.classList.toggle("voice-mode");
  input.focus();
});

loadConfig().catch((error) => {
  statusEl.textContent = error.message;
});
