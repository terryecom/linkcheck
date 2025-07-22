import { useEffect, useState } from "react";

export default function App() {
  const [url, setUrl] = useState("");
  const [logs, setLogs] = useState<string[]>([]);
  const [progress, setProgress] = useState(0);
  const [scanned, setScanned] = useState(0);
  const [downloadUrl, setDownloadUrl] = useState("");

  const handleStart = async () => {
    setLogs([]);
    setProgress(0);
    setScanned(0);
    setDownloadUrl("");

    const res = await fetch("/api/crawl", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
    });

    const reader = res.body?.getReader();
    const decoder = new TextDecoder("utf-8");

    if (reader) {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean);

        for (const line of lines) {
          try {
            const data = JSON.parse(line);
            if (data.log) setLogs((prev) => [...prev, data.log]);
            if (data.progress) setProgress(data.progress);
            if (data.scanned) setScanned(data.scanned);
            if (data.download) setDownloadUrl(data.download);
          } catch {
            setLogs((prev) => [...prev, line]);
          }
        }
      }
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold">🔍 Terry Ecom Link Checker</h1>
      <div className="flex gap-2">
        <input
          type="text"
          className="flex-1 border rounded px-3 py-2"
          placeholder="https://yourstore.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button
          onClick={handleStart}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          Start Crawl
        </button>
      </div>

      <div className="border rounded p-4 bg-white h-[300px] overflow-y-auto text-sm">
        {logs.map((line, idx) => {
          const isError = line.includes("❌") || line.includes("📧 Mailto:");
          return (
            <div
              key={idx}
              style={{
                backgroundColor: isError ? "#ffe6e6" : "transparent",
                padding: "2px 6px",
                borderRadius: "4px",
                marginBottom: "2px",
                whiteSpace: "pre-wrap",
                fontFamily: "monospace",
              }}
            >
              {line}
            </div>
          );
        })}
      </div>

      <div className="flex justify-between items-center">
        <span>Pages Scanned: {scanned}</span>
        <progress value={progress} max={100} className="w-full ml-4" />
      </div>

      {downloadUrl && (
        <a
          href={downloadUrl}
          className="inline-block mt-4 bg-green-600 text-white px-4 py-2 rounded"
        >
          📥 Download PDF Report
        </a>
      )}

      <footer className="pt-6 border-t mt-6 text-sm text-gray-500 space-x-3">
        <a href="https://www.terryecom.com" target="_blank">🌐 Website</a>
        <a href="mailto:terry@terryecom.com">✉️ Email</a>
        <a href="https://www.instagram.com/terryecom/" target="_blank">📷 Instagram</a>
        <a href="https://x.com/TerryEcom" target="_blank">𝕏 Twitter</a>
      </footer>
    </div>
  );
}
