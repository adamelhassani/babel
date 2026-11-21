import { useEffect } from "react";

export default function Toast({msg, onDone}) {
  useEffect(() => {
    if (!msg) return;
    const t = setTimeout(onDone, 5000);
    return () => clearTimeout(t);
  }, [msg, onDone]);

  if (!msg) return null;
  return <div id="toast">{msg}</div>;
}
