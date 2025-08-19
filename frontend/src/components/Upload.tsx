// src/components/Upload.tsx
import { useMemo, useState } from "react";
import Uppy from "@uppy/core";
import { Dashboard } from "@uppy/react";
import XHRUpload from "@uppy/xhr-upload";

// Uppy styles (needed for the built-in progress/UI)
import "@uppy/core/dist/style.min.css";
import "@uppy/dashboard/dist/style.min.css";

export default function Upload() {
  const [msg, setMsg] = useState("");

  const uppy = useMemo(() => {
    const u = new Uppy({
      autoProceed: false,                 // click Upload to start
      restrictions: {
        maxNumberOfFiles: 20,
        maxFileSize: 20 * 1024 * 1024,    // 20MB to match your backend
      },
    })
    .use(XHRUpload, {
      endpoint: "/api/v1/upload",         // your FastAPI route
      method: "POST",
      fieldName: "files",                 // FastAPI expects "files"
      formData: true,
      bundle: true,                       // send all files in ONE request
      withCredentials: false,
    });

    u.on("complete", (result) => {
      setMsg(`${result?.successful?.length} uploaded, ${result?.failed?.length} failed`);
    });
    u.on("error", (err) => setMsg(`Upload error: ${err}`));
    return u;
  }, []);

  return (
    <div style={{ padding: 12 }}>
      <Dashboard
        uppy={uppy}
        proudlyDisplayPoweredByUppy={false}
        height={320}
        note="Max 20MB per file"
        hideUploadButton={false}
        showProgressDetails
      />
      {msg && <p style={{marginTop:8}}>{msg}</p>}
    </div>
  );
}
