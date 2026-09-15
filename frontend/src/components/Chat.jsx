import { useState } from "react";
import ReactMarkdown from "react-markdown";

const API_URL = "http://localhost:8000";

function Chat() {
    const [question, setQuestion] = useState("");
    const [answer, setAnswer] = useState("");
    const [sources, setSources] = useState([]);
    const [loading, setLoading] = useState(false);

    const askQuestion = async () => {
        if (!question.trim()) {
            return;
        }

        try {
            setLoading(true);
            setAnswer("");
            setSources([]);

            const response = await fetch(
                `${API_URL}/chat`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        question: question,
                        top_k: 5
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Something went wrong");
            }

            setAnswer(data.answer);
            setSources(data.sources);

        } catch (error) {
            setAnswer(error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h2>Ask InterviewPrep</h2>

            <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask a question about your documents..."
                rows={4}
            />

            <button
                onClick={askQuestion}
                disabled={loading}
            >
                {loading ? "Thinking..." : "Ask"}
            </button>

            {answer && (
                <div>
                    <h3>Answer</h3>

                    <div className="answer-content">
                        <ReactMarkdown>
                            {answer}
                        </ReactMarkdown>
                    </div>
                </div>
            )}

            {sources.length > 0 && (
                <div>
                    <h3>Sources</h3>

                    {sources.map((source, index) => (
                        <div key={index}>
                            <p>
                                📄 Page {source.page}
                                {" "}
                                • Relevance: {(source.score * 100).toFixed(1)}%
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default Chat;