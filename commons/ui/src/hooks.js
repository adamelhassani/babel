import { useRef, useState } from "react";
import { api } from "./api";

export function useMic(notify, onTranscript) {
  const [micOn, setMicOn] = useState(false);
  const [micStatus, setMicStatus] = useState("");
  const recorder = useRef(null);
  const chunks = useRef([]);

  const toggle = async () => {
    if (recorder.current && recorder.current.state !== "inactive") {
      recorder.current.stop();
      return;
    }
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({audio: true});
    } catch (e) {
      notify("mic error: " + e.message);
      return;
    }
    chunks.current = [];
    const mr = new MediaRecorder(stream);
    mr.ondataavailable = (e) => { if (e.data.size) chunks.current.push(e.data); };
    mr.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      setMicOn(false);
      setMicStatus("transcribing…");
      try {
        const blob = new Blob(chunks.current, {type: mr.mimeType || "audio/webm"});
        const data = await api.transcribe(await blob.arrayBuffer());
        onTranscript(data.text);
        setMicStatus("transcript in rule box");
      } catch (e) {
        setMicStatus("");
        notify("transcribe failed: " + e.message);
      }
    };
    recorder.current = mr;
    mr.start();
    setMicOn(true);
    setMicStatus("recording… click again to stop");
  };

  return {micOn, micStatus, toggle};
}
