const http = require("http");
const fs = require("fs");
const path = require("path");

const port = Number(process.env.PORT || 8787);
const root = process.cwd();
const baseUrl = process.env.ROUTERAI_BASE_URL || "https://routerai.ru/api/v1";
const apiKey = process.env.ROUTERAI_API_KEY || "";

const indexPath = path.join(root, "routerai_recorder.html");
const modelsPath = path.join(root, "routerai_models.json");
const requestAudioDir = path.join(root, "request_audio");
const responseAudioDir = path.join(root, "response_audio");
const outputsDir = path.join(root, "routerai_outputs");

fs.mkdirSync(requestAudioDir, { recursive: true });
fs.mkdirSync(responseAudioDir, { recursive: true });
fs.mkdirSync(outputsDir, { recursive: true });

function sendText(res, status, body, headers = {}) {
  res.writeHead(status, {
    "Content-Type": "text/plain; charset=utf-8",
    ...headers,
  });
  res.end(body);
}

function sendJson(res, status, value) {
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(value, null, 2));
}

function contentType(fileName) {
  if (/\.wav$/i.test(fileName)) return "audio/wav";
  if (/\.mp3$/i.test(fileName)) return "audio/mpeg";
  if (/\.flac$/i.test(fileName)) return "audio/flac";
  if (/\.m4a$/i.test(fileName)) return "audio/mp4";
  if (/\.ogg$/i.test(fileName)) return "audio/ogg";
  if (/\.aac$/i.test(fileName)) return "audio/aac";
  if (/\.aiff$/i.test(fileName)) return "audio/aiff";
  return "application/octet-stream";
}

function serveFile(req, res, fullPath, fileName) {
  const stat = fs.statSync(fullPath);
  const range = req.headers.range;
  const type = contentType(fileName);
  const commonHeaders = {
    "Accept-Ranges": "bytes",
    "Content-Type": type,
  };

  if (!range) {
    res.writeHead(200, {
      ...commonHeaders,
      "Content-Length": stat.size,
    });
    if (req.method === "HEAD") {
      res.end();
      return;
    }
    fs.createReadStream(fullPath).pipe(res);
    return;
  }

  const match = range.match(/^bytes=(\d*)-(\d*)$/);
  if (!match) {
    res.writeHead(416, {
      ...commonHeaders,
      "Content-Range": `bytes */${stat.size}`,
    });
    res.end();
    return;
  }

  let start = match[1] ? Number(match[1]) : 0;
  let end = match[2] ? Number(match[2]) : stat.size - 1;

  if (!match[1] && match[2]) {
    start = Math.max(0, stat.size - Number(match[2]));
    end = stat.size - 1;
  }

  if (start >= stat.size || end >= stat.size || start > end) {
    res.writeHead(416, {
      ...commonHeaders,
      "Content-Range": `bytes */${stat.size}`,
    });
    res.end();
    return;
  }

  res.writeHead(206, {
    ...commonHeaders,
    "Content-Length": end - start + 1,
    "Content-Range": `bytes ${start}-${end}/${stat.size}`,
  });
  if (req.method === "HEAD") {
    res.end();
    return;
  }
  fs.createReadStream(fullPath, { start, end }).pipe(res);
}

function readBody(req, limitBytes = 25 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;
    req.on("data", (chunk) => {
      total += chunk.length;
      if (total > limitBytes) {
        reject(new Error("Request body too large"));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

async function readJson(req, limitBytes = 2 * 1024 * 1024) {
  const body = await readBody(req, limitBytes);
  return body.length ? JSON.parse(body.toString("utf8")) : {};
}

function safeName(value, fallback) {
  const stem = String(value || fallback)
    .trim()
    .replace(/\.[^.]+$/, "")
    .replace(/[^a-zA-Z0-9а-яА-ЯёЁ._-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
  return stem || fallback;
}

function safeFile(value) {
  const name = path.basename(String(value || ""));
  if (!name || name.includes("..")) {
    throw new Error("Invalid file name");
  }
  return name;
}

function slug(value) {
  return String(value).replace(/[^a-zA-Z0-9._-]+/g, "_").slice(0, 120);
}

function timestamp() {
  return new Date().toISOString().replace(/[:.]/g, "-");
}

function audioFormat(fileName) {
  const ext = path.extname(fileName).slice(1).toLowerCase();
  return ext || "wav";
}

function wavFromPcm16(pcmBuffer, sampleRate = 24000, channels = 1) {
  const header = Buffer.alloc(44);
  const byteRate = sampleRate * channels * 2;
  header.write("RIFF", 0);
  header.writeUInt32LE(36 + pcmBuffer.length, 4);
  header.write("WAVE", 8);
  header.write("fmt ", 12);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(channels, 22);
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(byteRate, 28);
  header.writeUInt16LE(channels * 2, 32);
  header.writeUInt16LE(16, 34);
  header.write("data", 36);
  header.writeUInt32LE(pcmBuffer.length, 40);
  return Buffer.concat([header, pcmBuffer]);
}

function audioItem(dir, source, route, name) {
  const fullPath = path.join(dir, name);
  const stat = fs.statSync(fullPath);
  return {
    id: `${source}:${name}`,
    name,
    source,
    bytes: stat.size,
    modified: stat.mtime.toISOString(),
    url: `/${route}/${encodeURIComponent(name)}`,
  };
}

function listAudioFiles() {
  const requests = fs
    .readdirSync(requestAudioDir)
    .filter((name) => /\.(wav|mp3|flac|m4a|ogg|aac|aiff)$/i.test(name))
    .map((name) => audioItem(requestAudioDir, "request", "request-audio", name));

  const responses = fs
    .readdirSync(responseAudioDir)
    .filter((name) => /\.wav$/i.test(name))
    .map((name) => audioItem(responseAudioDir, "response", "response-audio", name));

  return requests.concat(responses).sort((a, b) => b.modified.localeCompare(a.modified));
}

function resolveAudioRef(value) {
  const raw = String(value || "");
  const separator = raw.indexOf(":");
  if (separator > 0) {
    const source = raw.slice(0, separator);
    const name = safeFile(raw.slice(separator + 1));
    if (source === "request") {
      return { source, name, fullPath: path.join(requestAudioDir, name) };
    }
    if (source === "response") {
      return { source, name, fullPath: path.join(responseAudioDir, name) };
    }
  }

  const name = safeFile(raw);
  const requestPath = path.join(requestAudioDir, name);
  const responsePath = path.join(responseAudioDir, name);
  if (fs.existsSync(requestPath)) {
    return { source: "request", name, fullPath: requestPath };
  }
  return { source: "response", name, fullPath: responsePath };
}

function extractText(responseJson) {
  const message = responseJson?.choices?.[0]?.message;
  if (typeof message?.content === "string") {
    return message.content;
  }
  if (Array.isArray(message?.content)) {
    return message.content
      .map((part) => part.text || part.content || "")
      .filter(Boolean)
      .join("\n");
  }
  return "";
}

async function callRouterAi(payload, stream = false) {
  if (!apiKey) {
    throw new Error("ROUTERAI_API_KEY is not set in the server environment");
  }

  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`RouterAI ${response.status}: ${detail}`);
  }

  if (stream) {
    return response.text();
  }

  return response.json();
}

function applyTokenLimit(payload, maxTokens) {
  const parsed = Number(maxTokens);
  if (Number.isFinite(parsed) && parsed > 0) {
    payload.max_tokens = Math.floor(parsed);
    payload.max_completion_tokens = Math.floor(parsed);
  }
}

function languageInstruction(language) {
  const value = String(language || "auto").trim();
  if (!value || value.toLowerCase() === "auto") {
    return "";
  }
  return `Use ${value} as the target language.`;
}

async function runTts({ model, voice, text, systemPrompt, language, maxTokens }) {
  const languageHint = languageInstruction(language);
  const defaultSystemPrompt = [
    "You are a text-to-speech voiceover engine. Speak exactly the user's text verbatim.",
    "Do not answer, rewrite, summarize, translate, add introductions, or add closing remarks.",
  ].join(" ");
  const finalSystemPrompt = [String(systemPrompt || defaultSystemPrompt).trim(), languageHint].filter(Boolean).join(" ");
  const payload = {
    model,
    modalities: ["text", "audio"],
    messages: [
      {
        role: "system",
        content: finalSystemPrompt,
      },
      {
        role: "user",
        content: `Voice over this exact text:\n\n${text}`,
      },
    ],
    audio: {
      voice: voice || "alloy",
      format: "pcm16",
    },
    stream: true,
  };
  applyTokenLimit(payload, maxTokens);

  const sse = await callRouterAi(payload, true);
  const chunks = [];
  const textParts = [];

  for (const line of sse.split(/\r?\n/)) {
    if (!line.startsWith("data: ")) {
      continue;
    }
    const data = line.slice(6);
    if (data === "[DONE]") {
      break;
    }
    try {
      const event = JSON.parse(data);
      const delta = event?.choices?.[0]?.delta || {};
      if (delta.audio?.data) {
        chunks.push(Buffer.from(delta.audio.data, "base64"));
      }
      if (typeof delta.content === "string") {
        textParts.push(delta.content);
      }
    } catch {
      // Ignore malformed SSE keepalive lines.
    }
  }

  const pcm = Buffer.concat(chunks);
  const baseName = `${timestamp()}_${slug(model)}_${safeName(voice || "alloy", "voice")}`;
  const sseFile = `${baseName}.sse.jsonl`;
  const pcmFile = `${baseName}.pcm`;
  const wavFile = `${baseName}.wav`;

  fs.writeFileSync(path.join(outputsDir, sseFile), sse);
  fs.writeFileSync(path.join(responseAudioDir, pcmFile), pcm);
  fs.writeFileSync(path.join(responseAudioDir, wavFile), wavFromPcm16(pcm));

  return {
    model,
    voice,
    text: textParts.join(""),
    audioBytes: pcm.length,
    files: {
      sse: sseFile,
      pcm: pcmFile,
      wav: wavFile,
      wavRef: `response:${wavFile}`,
      wavUrl: `/response-audio/${encodeURIComponent(wavFile)}`,
    },
  };
}

async function runStt({ model, audioFile, prompt, language, maxTokens }) {
  const { source, name, fullPath } = resolveAudioRef(audioFile);
  if (!fs.existsSync(fullPath)) {
    throw new Error(`Audio file not found: ${audioFile}`);
  }

  const languageHint = languageInstruction(language);
  const sttPrompt = [prompt || "Transcribe this audio exactly. Return only the transcript text.", languageHint]
    .filter(Boolean)
    .join(" ");

  const payload = {
    model,
    messages: [
      {
        role: "user",
        content: [
          {
            type: "text",
            text: sttPrompt,
          },
          {
            type: "input_audio",
            input_audio: {
              data: fs.readFileSync(fullPath).toString("base64"),
              format: audioFormat(name),
            },
          },
        ],
      },
    ],
  };
  applyTokenLimit(payload, maxTokens);

  const responseJson = await callRouterAi(payload, false);
  const baseName = `${timestamp()}_${slug(model)}_${safeName(name, "audio")}`;
  const jsonFile = `${baseName}.json`;
  fs.writeFileSync(path.join(outputsDir, jsonFile), JSON.stringify(responseJson, null, 2));

  return {
    model,
    audioFile: name,
    audioSource: source,
    transcript: extractText(responseJson),
    response: responseJson,
    files: {
      json: jsonFile,
    },
  };
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);

    if (req.method === "GET" && (url.pathname === "/" || url.pathname === "/index.html")) {
      const html = fs.readFileSync(indexPath);
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(html);
      return;
    }

    if (req.method === "GET" && url.pathname === "/models") {
      sendJson(res, 200, JSON.parse(fs.readFileSync(modelsPath, "utf8")));
      return;
    }

    if (req.method === "GET" && url.pathname === "/recordings") {
      sendJson(res, 200, listAudioFiles());
      return;
    }

    if ((req.method === "GET" || req.method === "HEAD") && url.pathname.startsWith("/request-audio/")) {
      const name = safeFile(decodeURIComponent(url.pathname.replace("/request-audio/", "")));
      const fullPath = path.join(requestAudioDir, name);
      if (!fs.existsSync(fullPath)) {
        sendText(res, 404, "Request audio not found\n");
        return;
      }
      serveFile(req, res, fullPath, name);
      return;
    }

    if ((req.method === "GET" || req.method === "HEAD") && url.pathname.startsWith("/response-audio/")) {
      const name = safeFile(decodeURIComponent(url.pathname.replace("/response-audio/", "")));
      const fullPath = path.join(responseAudioDir, name);
      if (!fs.existsSync(fullPath)) {
        sendText(res, 404, "Response audio not found\n");
        return;
      }
      serveFile(req, res, fullPath, name);
      return;
    }

    if (req.method === "GET" && url.pathname === "/status") {
      sendJson(res, 200, {
        server: `http://localhost:${port}`,
        hasApiKey: Boolean(apiKey),
        modelFile: "routerai_models.json",
        requestAudioDir: "request_audio",
        responseAudioDir: "response_audio",
        outputsDir: "routerai_outputs",
        recordings: listAudioFiles(),
      });
      return;
    }

    if (req.method === "POST" && url.pathname === "/recordings") {
      const body = await readBody(req);
      const requested = url.searchParams.get("name") || `recording-${timestamp()}`;
      const fileName = `${safeName(requested, "recording")}.wav`;
      fs.writeFileSync(path.join(requestAudioDir, fileName), body);
      sendJson(res, 200, {
        id: `request:${fileName}`,
        name: fileName,
        source: "request",
        bytes: body.length,
        url: `/request-audio/${encodeURIComponent(fileName)}`,
      });
      return;
    }

    if (req.method === "POST" && url.pathname === "/routerai/tts") {
      sendJson(res, 200, await runTts(await readJson(req)));
      return;
    }

    if (req.method === "POST" && url.pathname === "/routerai/stt") {
      sendJson(res, 200, await runStt(await readJson(req)));
      return;
    }

    sendText(res, 404, "Not found\n");
  } catch (error) {
    sendJson(res, 500, { error: error.message });
  }
});

server.listen(port, () => {
  console.log(`RouterAI audio console running at http://localhost:${port}`);
  console.log(`Request audio: ${requestAudioDir}`);
  console.log(`Response audio: ${responseAudioDir}`);
  console.log(`Response bodies: ${outputsDir}`);
  console.log(`API key loaded: ${apiKey ? "yes" : "no"}`);
});
