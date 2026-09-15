import DocumentUpload from "./components/DocumentUpload";
import Chat from "./components/chat";

function App() {
    return (
        <div>
            <h1>InterviewPrep RAG</h1>

            <DocumentUpload />

            <hr />

            <Chat />
        </div>
    );
}

export default App;