import { useState } from "react";

const API_URL = "http://localhost:8000";

function DocumentUpload() {
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState("");

    const handleUpload = async () => {
        if (!file) {
            setStatus("Please select a PDF.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        try {
            setStatus("Uploading and indexing...");

            const response = await fetch(
                `${API_URL}/documents/upload`,
                {
                    method: "POST",
                    body: formData
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Upload failed");
            }

            setStatus(
                `${data.filename} indexed successfully. ` +
                `${data.total_chunks} chunks created.`
            );

            setFile(null);

        } catch (error) {
            setStatus(error.message);
        }
    };

    return (
        <div>
            <h2>Upload Document</h2>

            <input
                type="file"
                accept=".pdf"
                onChange={(event) => setFile(event.target.files[0])}
            />

            <button onClick={handleUpload}>
                Upload
            </button>

            {status && <p>{status}</p>}
        </div>
    );
}

export default DocumentUpload;